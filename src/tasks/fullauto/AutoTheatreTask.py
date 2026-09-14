from qfluentwidgets import FluentIcon
import time

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.dna_ui.Defs import COORD

# 「已开战」的判据框（Defs.SCREEN_BOX 里的名字），按颜色用
OBJECTIVE_DIAMOND_BOX = 'THEATRE_OBJECTIVE_DIAMOND'

logger = Logger.get_logger(__name__)

# ---- 界面判据 label（标注在 ok_templates，运行期从 assets 的 coco 标注取模板）----
# 这些 label 的搜索框直接用 coco 标注本身：位置固定、框也很紧（结算页「前往」和
# 「返回」只隔 33px，框放宽会互相串味），所以不写进 Defs.DISCRIMINATORS；
# 点击坐标统一放 Defs.COORD。
OBJECTIVE_PANEL = 'theatre_start'             # 左上目标栏的菱形（金=未开战/红=已开战），命中即"关内已加载"
OBJECTIVE_PANEL_FIGHT = 'theatre_fight'       # 同一个菱形的战斗态标注，只做判据兜底
# 「已开战」用的是菱形所在区域的**颜色**（Defs.SCREEN_BOX.THEATRE_OBJECTIVE_DIAMOND），
# 不是上面两个模板：形状一样、只有颜色不同，而模板在明亮场景里会失手。
INTERACT_PROMPT = 'theatre_f'                 # 机关「F 操作」提示，走位到位的唯一判据
ESC_RETRY = 'esc_retry'                       # 局内菜单「重新开始」
RESTART_CONFIRM = 'esc_restart_check_btn'     # 「是否重新开始战斗」二次确认弹窗的「确定」
RESULT_WIN = 'theatre_win'                    # 结算页右下角黄色圆圈「前往」
RESULT_FAIL = 'theatre_fail'                  # 结算页「返回」，只当失败判据，不点它
RESULT_RETRY = 'theatre_retry'                # 结算页「再次挑战」
START_BTN = 'start_screen_start_btn_3'        # 阵容页「前往」
START_CONFIRM = 'start_screen_start_btn_3_1'  # 「确认进入」弹窗的「确定」

# 目标栏菱形变红 = 已开战。**只看颜色**：游戏有 6 种语言，模板里不能带文字；
# 而金/红两个菱形形状完全一样，去均值归一化的相关度（TM_CCOEFF_NORMED，框架默认）
# 会把绝对色差抵掉 —— 离线实测两个模板互相匹配 0.863（灰度 0.981），都在阈值 0.8 之上，
# 靠模板分数根本分不开。颜色占比离线实测：金菱形框内红色 0.000 / 红菱形框内 0.266，
# 其余界面（菜单/结算/阵容）同位置都是 0，阈值取 0.15 留一倍余量。
OBJECTIVE_RED = {'r': (185, 255), 'g': (0, 120), 'b': (0, 120)}
OBJECTIVE_RED_THRESHOLD = 0.15

# 走位时间轴，录自 `mod\示例-脚本工具\回放和录制软件\scripts\map\custom\沉浸式戏剧.json`。
# 录制里第一条 f12 是录制软件自己的热键（另一个录制样例「羽翼雷昂扬」里没有），
# 不属于走位，已丢弃；其余时间点换算成"相对上一步的等待秒数"：
#   (等待秒数, 按键, 按下/抬起)
WALK_SCHEDULE = (
    (0.996, 'w', True),
    (1.120, 'w', False),
    (0.615, 'w', True),
    (0.111, 'w', False),
    (0.287, 'd', True),
    (0.970, 'd', False),
)
# 走位期间按住 lalt 锁视角，免得防挂机的鼠标抖动把镜头带偏（其他全自动任务同样处理）
WALK_HOLD_KEYS = ('lalt',)
WALK_RELEASE_KEYS = ('w', 'a', 's', 'd')

# 走完位等「F 操作」提示出现：等不到就是没走到机关旁边，判本次走位失败
INTERACT_TIME_OUT = 8
# 按 F 的间隔，以及按 F 之后等开战的上限
INTERACT_INTERVAL = 0.5
FIGHT_TIME_OUT = 10
# 点了「前往」/「再次挑战」之后等离开当前界面、等进关卡加载完成的上限
LOAD_TIME_OUT = 30
# 兜底：按 F 开战之后到结算页出现之前一律算战斗、从不停手，判据只用来判断"是不是掉线了"。
# 连续这么多秒连结果页/局内菜单/HUD/目标栏都认不出来才报错停止；战斗本身不设超时
# （游戏自己会超时进结算页）。
MISSION_LOST_TIME_OUT = 120

# ---- 切层检测（左上目标栏那行关号：「开启第一试炼」/「第一试炼」）----
# 只拿 `theatre_stage` 的标注框当 OCR 区域，**不做模板匹配**：那行字是游戏文本，
# 六种语言各不相同，模板匹配天生不通用。
STAGE_TEXT = 'theatre_stage'
# 主循环 0.2 秒一轮，每这么多秒读一次关号
STAGE_OCR_INTERVAL = 1.0
# 切层时"文字先变、层后切"，中间会有半截读数，所以新关号要连续读到这么多次才确认
STAGE_CONFIRM_COUNT = 3
# OCR 置信度下限：菜单/结算页/加载画面读不出文字，低分噪声（实测结算页会吐 0.65 的「-」）也不算
STAGE_MIN_CONFIDENCE = 0.9
# 等切层动画收尾的上限：目标栏（红菱形）回来就算切好了。文字确认变化时多半已经是红的，
# 所以通常立刻返回；等满这么久还不红只是记一条警告，不报错。
# 别调大：一层打得快，等 30 秒可能这一层都已经打完了。
STAGE_SWITCH_TIME_OUT = 15
# 一个关卡 5 层（第 1~5 试炼），最后一层是 BOSS 层：复位角色会把人传到 BOSS 场地外面，
# 所以切进最后一层什么都不做。也就是一个关卡里只复位 3 次（第 1->2、2->3、3->4 层）。
LAYERS_PER_STAGE = 5
# 新关卡第 1 层：判据刚出现时角色还在落地/过场收尾，这时候按走位键会被吃掉前面一段
# （表现就是"走位变短了、走不到机关"），所以等关卡加载完再稳这么久才开始走位。
FIRST_LAYER_SETTLE = 1


class AutoTheatreTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动沉浸式戏剧（不朽剧目·勇者征程）。

    关卡结构：一个关卡 5 层（第 1~5 试炼），只有**新关卡的第 1 层**要走到机关按 F 开战；
    第 2~5 层是游戏自己切、自己开打的。所以脚本只在"新关卡第 1 层"走位开机关，层与层之间
    等切层动画收尾 + 按「挂机模式」处理一次角色位置；**最后一层是 BOSS 层，什么都不做**
    （复位角色会把人传到 BOSS 场地外面），也就是一个关卡只复位 3 次。5 层打完出结算页，
    点「前往」进下一个关卡（又是第 1 层，重新走位开机关）。

    循环：「阵容页 -> 进图 -> 走位开机关 -> 挂机（层间切层处理）-> 结算页 -> 再进图」。

    失败重试：走位/开机关连续失败、结算连续失败各自计数，配置 N 表示允许重试 N 次、
    第 N+1 次连续失败报错停止；中间成功一次就清零。关卡数由「打几层」控制，0 = 无限。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动沉浸式戏剧"
        self.description = "全自动"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        self.setup_commission_config()
        self.setup_mission_start_config()
        # 这个模式没有轮次和战斗超时：挂机一直打到游戏自己判负/通关进结算页，层数用「打几层」控制
        for key in ("轮次", "超时时间"):
            self.default_config.pop(key, None)
        self.default_config.update({
            "打几层": 0,
            "开机关重试次数": 3,
            "结算失败重试次数": 3,
        })
        self.config_description.update({
            "打几层": "打几层，0 = 无限循环",
            "开机关重试次数": "走位/开机关连续失败几次后报错停止",
            "结算失败重试次数": "结算失败连续重试几次后报错停止",
        })

        self.skill_tick = self.create_skill_ticker()
        self.random_walk_tick = self.create_random_walk_ticker()
        # 云游戏实拍帧糊、模板分低，给足重试轮次
        self.action_timeout = 20
        self.current_floor = 0
        self.interact_failures = 0
        self.result_failures = 0
        self.mission_started = False
        self.stage_index = 0
        self.reset_stage_detector()

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoTheatreTask error", e)
            raise

    def do_run(self):
        """主循环：看画面属于哪个界面就处理哪个，打满层数正常返回。

        启动时必须停在阵容页或结算页（中途的加载/过场画面只是等一下）。
        """
        self.init_all()
        if not self.known_screen():
            raise Exception("请先把游戏停在「勇者征程」阵容页或结算页上再启动任务")
        unknown_since = None
        while True:
            if self.find_one(START_BTN):
                self.start_mission()
            elif self.find_one(RESULT_WIN) or self.find_one(RESULT_FAIL):
                if self.handle_result():
                    return
            elif self.in_theatre_mission():
                self.handle_in_mission()
            else:
                # 加载 / 过场 / 切图：等画面回来，但别无限空转
                if unknown_since is None:
                    unknown_since = time.time()
                    self.log_info('等待界面切换（加载/过场）...')
                elif time.time() - unknown_since > LOAD_TIME_OUT:
                    raise Exception(f'等了 {LOAD_TIME_OUT} 秒还认不出当前界面，停止任务')
                self.sleep(0.5)
                continue
            unknown_since = None
            self.sleep(0.2)

    def init_all(self):
        self.load_char()
        self.skill_tick.reset()
        self.current_floor = 0
        self.interact_failures = 0
        self.result_failures = 0
        self.mission_started = False
        self.stage_index = 0
        self.reset_stage_detector()

    def retry_limit(self, key, default=3):
        """读重试次数配置：允许重试 N 次，第 N+1 次连续失败报错。"""
        try:
            return max(0, int(self.config.get(key, default)))
        except (TypeError, ValueError):
            return default

    def target_floor(self):
        """打几层：0 = 无限循环。"""
        try:
            return max(0, int(self.config.get('打几层', 0)))
        except (TypeError, ValueError):
            return 0

    def known_screen(self):
        """是不是一个能开工的界面（阵容页 / 结算页 / 关内）。"""
        return (self.find_one(START_BTN) is not None
                or self.find_one(RESULT_WIN) is not None
                or self.find_one(RESULT_FAIL) is not None
                or self.in_theatre_mission())

    # ------------------------------------------------------------------
    # 阵容页
    # ------------------------------------------------------------------

    def left_start_screen(self):
        """已经不在阵容页（无论在加载还是已经进图）。"""
        return self.find_one(START_BTN) is None and self.find_one(START_CONFIRM) is None

    def start_mission(self, time_out=LOAD_TIME_OUT):
        """阵容页：点「前往」，有「确认进入」弹窗就点「确定」，然后等离开阵容页。

        弹窗不是每次都有（游戏里能设成不再提示），而且弹窗一盖上来阵容页的「前往」
        就被压暗到认不出来 —— 所以"弹窗出现"和"已经进图"都算这一步走通，谁先到算谁。
        云游戏会丢点击，所以点一次没动静就再点一次（间隔 1 秒）。
        """
        def confirm_or_left():
            return self.find_one(START_CONFIRM) is not None or self.left_start_screen()

        if not self.wait_until(confirm_or_left, time_out=time_out,
                               post_action=lambda: self.click_ui_coord(
                                   COORD.THEATRE_START, name=START_BTN, after_sleep=1),
                               raise_if_not_found=False):
            raise Exception(f'点了「前往」之后 {time_out} 秒还停在阵容页（门票/体力不足或点击没生效）')
        if self.find_one(START_CONFIRM):
            if not self.wait_until(self.left_start_screen, time_out=time_out,
                                   post_action=lambda: self.click_ui_coord(
                                       COORD.THEATRE_START_CONFIRM, name=START_CONFIRM, after_sleep=1),
                                   raise_if_not_found=False):
                raise Exception('点了「确认进入」的「确定」之后没能进关卡（门票/体力不足？）')

    # ------------------------------------------------------------------
    # 关内：等加载 -> 走位开机关 -> 挂机
    # ------------------------------------------------------------------

    def in_theatre_mission(self):
        """是不是在关内（局内菜单盖在 HUD 上时也算）。"""
        return self.in_team() or self.find_one(ESC_RETRY) is not None

    def find_objective_panel(self):
        """左上目标栏的菱形（金/红都在同一个位置）。

        命中就代表"关卡已经加载完、可以开始走位"；局内菜单和结算页都不命中。
        """
        return self.find_one(OBJECTIVE_PANEL) or self.find_one(OBJECTIVE_PANEL_FIGHT)

    def is_in_combat(self):
        """目标栏菱形变红 = 已开战（只看颜色，和界面语言、背景明暗都无关）。

        位置优先用菱形模板（现在只截菱形内部、不含背景，所以亮暗场景都能命中），
        没匹上就退回固定框 —— 离线实测亮场景那颗菱形只有 0.802，压着 0.8 的阈值，
        差一点点就会把"已开战"漏判成没开战（表现：切层后等红菱形白等到超时）。
        红色占比（阈值 0.15）：模板框内 金 0.000 / 红 0.89~0.91；固定框内 金 0.000 / 红 0.23~0.26。
        """
        box = self.find_objective_panel() or self.screen_box(OBJECTIVE_DIAMOND_BOX)
        return self.calculate_color_percentage(OBJECTIVE_RED, box) > OBJECTIVE_RED_THRESHOLD

    def handle_in_mission(self):
        if self.find_one(ESC_RETRY):
            # 局内菜单被打开了（一般是玩家自己按的 ESC）：关掉继续，绝不在这里点菜单
            self.send_key("esc", after_sleep=0.5)
            return
        if not self.mission_started:
            self.wait_mission_loaded()
            self.sleep(FIRST_LAYER_SETTLE)
            self.mission_started = True
            self.stage_index = 1
            self.walk_and_interact()
            # 每一关都是从零开始打，技能计时器必须重新武装：`reset()` 让下一次 tick 立刻触发。
            # 不重置的话长频率技能（比如「终结技 600 秒」）只有在第一关会放，后面每一关
            # 都在等第一关那次计时的剩余间隔，等于整关不放技能。
            self.skill_tick.reset()
            self.reset_stage_detector()
        # 挂机；游戏自己切到下一关（关号变了）就把这一关的开头处理一遍再接着挂
        while self.fight_until_result():
            self.handle_stage_switch()

    def wait_mission_loaded(self, time_out=LOAD_TIME_OUT):
        """等关卡加载完：目标栏菱形或者通用局内 HUD（左下角 Lv）出来都算。

        带上 `in_team()` 兜底是必须的：菱形模板在明亮的关卡场景里会失手，
        只用它会在那种关卡误报"没进关卡"。
        """
        if not self.wait_until(lambda: self.find_objective_panel() is not None or self.in_team(),
                               time_out=time_out, raise_if_not_found=False):
            raise Exception(f'等了 {time_out} 秒还没进关卡（门票/体力不足或掉线？）')

    def walk_and_interact(self):
        """走位到机关并按 F 开战：连续失败到上限就报错停止。"""
        limit = self.retry_limit('开机关重试次数')
        while not self.walk_and_interact_once():
            self.interact_failures += 1
            if self.interact_failures > limit:
                raise Exception(f'走位开机关连续失败 {self.interact_failures} 次，停止任务')
            self.log_info(f'走位开机关第 {self.interact_failures} 次失败（最多 {limit} 次），'
                          f'ESC 重新开始')
            self.restart_in_mission()
        self.interact_failures = 0

    def walk_and_interact_once(self):
        """一次尝试：走位 -> 等「F 操作」提示 -> 按 F 直到开战。成功返回 True。"""
        self.play_walk()
        if not self.wait_until(lambda: self.find_one(INTERACT_PROMPT) is not None,
                               time_out=INTERACT_TIME_OUT, raise_if_not_found=False):
            self.log_info(f'走位之后 {INTERACT_TIME_OUT} 秒没看到「F 操作」提示，判定走位失败')
            return False
        deadline = time.time() + FIGHT_TIME_OUT
        while time.time() < deadline:
            if self.is_in_combat():
                self.log_info('已经开战')
                return True
            self.send_key(self.get_interact_key(), down_time=0.1)
            self.sleep(INTERACT_INTERVAL)
        return self.is_in_combat()

    def play_walk(self):
        """按录制时间轴走位；全程按住 lalt 锁视角，不管成功失败都松开所有按键。"""
        for key in WALK_HOLD_KEYS:
            self.send_key_down(key)
        try:
            for wait, key, down in WALK_SCHEDULE:
                self.sleep(wait)
                if down:
                    self.send_key_down(key)
                else:
                    self.send_key_up(key)
        finally:
            for key in WALK_RELEASE_KEYS:
                self.send_key_up(key)
            for key in WALK_HOLD_KEYS:
                self.send_key_up(key)

    def restart_in_mission(self, time_out=10, load_time_out=LOAD_TIME_OUT):
        """走位/开机关失败后局内重来：ESC 开菜单 -> 点「重新开始」-> 点二次确认的「确定」。

        两个都是云游戏爱丢的点击，所以都是"点到出结果为止"：先点到弹窗出来，再点到弹窗消失。
        重开会把关卡重新加载一遍，菜单/弹窗/加载画面都会盖掉目标栏判据，所以"先消失再回来"
        正好当重开完成的信号；万一它没消失（秒重开）也不会卡住，直接往下走。
        """
        start = time.time()
        while not self.find_one(ESC_RETRY):
            if time.time() - start > time_out:
                raise Exception('局内菜单打不开，没法重新开始')
            self.send_key("esc")
            self.wait_until(lambda: self.find_one(ESC_RETRY) is not None, time_out=2,
                            raise_if_not_found=False)
        self.wait_until(
            condition=lambda: self.find_one(RESTART_CONFIRM) is not None,
            post_action=lambda: self.click_ui_coord(COORD.THEATRE_ESC_RETRY, name=ESC_RETRY,
                                                    after_sleep=0.5),
            time_out=time_out,
        )
        self.wait_until(
            condition=lambda: not self.find_one(RESTART_CONFIRM),
            post_action=lambda: self.click_ui_coord(COORD.THEATRE_RESTART_CONFIRM,
                                                    name=RESTART_CONFIRM, after_sleep=0.5),
            time_out=time_out,
        )
        self.wait_until(lambda: self.find_objective_panel() is None, time_out=time_out,
                        raise_if_not_found=False)
        self.wait_mission_loaded(time_out=load_time_out)

    def in_combat_screen(self):
        """画面还算"在关内"吗 —— 只用来判断是不是掉线了，不用来决定放不放技能。

        两个判据取并集：通用的局内 HUD（`in_team()`，靠左下角 Lv 文字）和本模式的
        左上目标栏。实机上它们都会偶尔失手，所以这个判断不适合控制技能节奏，
        只适合"连续多久什么都认不出来"这种粗粒度兜底。
        """
        return self.in_team() or self.find_objective_panel() is not None

    def fight_until_result(self):
        """挂机到结算页出现（返回 False），或者检测到切到下一关（返回 True）。

        进战斗之后（按 F 确认开战）到结算页出现之前，**一律算战斗状态、从不停手**：
        这个模式的判据在实机上会闪，拿它们控制"停不停手"会让技能一顿一顿的。
        只有连续 MISSION_LOST_TIME_OUT 秒连结果页/局内菜单/HUD/目标栏都认不出来
        （掉线、被踢回主界面）才报错停止。
        """
        lost_since = None
        while True:
            if self.find_one(RESULT_WIN) or self.find_one(RESULT_FAIL):
                return False
            if self.find_one(ESC_RETRY):
                self.send_key("esc", after_sleep=0.5)
                continue
            if self.in_combat_screen():
                lost_since = None
            elif lost_since is None:
                lost_since = time.time()
            elif time.time() - lost_since > MISSION_LOST_TIME_OUT:
                raise Exception(f'连续 {MISSION_LOST_TIME_OUT} 秒什么状态都认不出来，停止任务')
            if self.update_stage_text(self.read_stage_text()):
                return True
            self.skill_tick()
            self.random_walk_tick()
            self.sleep(0.2)

    # ------------------------------------------------------------------
    # 切层（关号变了）
    # ------------------------------------------------------------------

    def reset_stage_detector(self):
        """按 F 开战之后调用：第一次读到的关号只当基准点，所以第一层不会触发重置。"""
        self.stage_text = None
        self.stage_pending = None
        self.stage_pending_count = 0
        self.stage_next_ocr = 0.0

    def read_stage_text(self):
        """读左上目标栏那行关号（「开启第一试炼」/「第一试炼」），最多 STAGE_OCR_INTERVAL 秒一次。

        菜单、结算页、加载画面读不出文字（实测为空），低分噪声也不算 —— 一律返回 None，
        调用方按"没读到"处理，不能当成"变了"。1 秒一次的小区域 OCR 只花几十毫秒，
        没必要像波次那样丢线程池。
        """
        if time.time() < self.stage_next_ocr:
            return None
        self.stage_next_ocr = time.time() + STAGE_OCR_INTERVAL
        texts = self.ocr(box=self.get_box_by_name(STAGE_TEXT))
        best = max(texts, key=lambda text: text.confidence, default=None)
        if best is None or best.confidence < STAGE_MIN_CONFIDENCE or len(best.name) < 2:
            return None
        return best.name

    def same_stage_text(self, one, other):
        """两个读数是不是"同一关"，只比较、不解析。

        同一关里按 F 开战会让那行字从「开启第一试炼」变成「第一试炼」（前缀没了），
        两边互相包含就算同一关 —— 否则每次按 F 都会被误判成切层。不解析文字是因为
        游戏有六种语言、而且实测 OCR 出来是 GBK 乱码，只稳定不可读。
        """
        return one == other or one in other or other in one

    def update_stage_text(self, text):
        """把一次读数喂进状态机：连续 STAGE_CONFIRM_COUNT 次读到同一个新关号才算切层。

        文字先变、层后切，中间还有半截读数，所以要连续确认。
        """
        if text is None:
            return False
        if self.stage_text is None or self.same_stage_text(text, self.stage_text):
            self.stage_text = text
            self.stage_pending = None
            self.stage_pending_count = 0
            return False
        if text == self.stage_pending:
            self.stage_pending_count += 1
        else:
            self.stage_pending = text
            self.stage_pending_count = 1
        if self.stage_pending_count < STAGE_CONFIRM_COUNT:
            return False
        self.stage_index += 1
        self.log_info(f'检测到切层：{self.stage_text} -> {text}（本关卡第 {self.stage_index} 层）')
        self.stage_text = text
        self.stage_pending = None
        self.stage_pending_count = 0
        return True

    def wait_stage_ready(self, time_out=STAGE_SWITCH_TIME_OUT):
        """等目标栏变红（新一层开打）就算切层动画收尾，可以直接处理角色位置。

        文字确认变化时多半已经是红的了，所以基本是立刻返回。等满上限还不红（加载慢、掉线）
        不报错：记一条警告，照常往下走。
        """
        if self.wait_until(self.is_in_combat, time_out=time_out, raise_if_not_found=False):
            return True
        self.log_warning(f'等了 {time_out} 秒目标栏还没变红（加载慢或掉线？），继续处理角色位置')
        return False

    def handle_stage_switch(self):
        """切到下一层：只有新关卡的第 1 层要按 F 开机关，层与层之间不用。

        等目标栏变红（切层动画收尾）之后按「挂机模式」处理角色位置。
        **最后一层（BOSS 层）不做"复位角色"** —— 那里复位会把人传到 BOSS 场地外面；
        「向前走 / 前进到开战」在 BOSS 层照常生效（这两个只是按键走动，不传送）。
        """
        boss_layer = self.stage_index >= LAYERS_PER_STAGE
        self.log_info('检测到切层，等目标栏变红（新一层开打）')
        self.wait_stage_ready()
        if boss_layer:
            self.log_info(f'第 {self.stage_index} 层是 BOSS 层，跳过复位角色（复位会传到场地外）')
        self.apply_afk_mode(allow_reset=not boss_layer)
        self.reset_stage_detector()

    def advance_failed(self):
        """「自动前进到开战」在这个模式里超时：没有「放弃挑战」可点，记一条日志继续挂机。

        切层时目标栏本来就是红的（新一层自己开打），这个模式在切层里基本不会真的走满超时。
        """
        self.log_info('自动前进到开战超时，不再前进，继续挂机')
        return True

    # ------------------------------------------------------------------
    # 结算页
    # ------------------------------------------------------------------

    def handle_result(self):
        """结算页：成功点「前往」进下一层，失败点「再次挑战」重来。返回是否该结束任务。"""
        self.mission_started = False
        if self.find_one(RESULT_WIN):
            self.result_failures = 0
            self.current_floor += 1
            self.log_info(f'第 {self.current_floor} 层完成')
            target = self.target_floor()
            if target and self.current_floor >= target:
                self.log_info(f'已经打满 {target} 层，任务结束')
                return True
            self.click_ui_coord(COORD.THEATRE_RESULT_WIN, name=RESULT_WIN, after_sleep=1)
            self.wait_left_result()
            return False
        limit = self.retry_limit('结算失败重试次数')
        self.result_failures += 1
        if self.result_failures > limit:
            raise Exception(f'结算连续失败 {self.result_failures} 次，停止任务')
        self.log_info(f'第 {self.current_floor + 1} 层结算失败，'
                      f'第 {self.result_failures} 次重试（最多 {limit} 次）')
        self.click_ui_coord(COORD.THEATRE_RESULT_RETRY, name=RESULT_RETRY, after_sleep=1)
        self.wait_left_result()
        return False

    def wait_left_result(self, time_out=LOAD_TIME_OUT):
        """点了「前往」/「再次挑战」之后等离开结算页，免得下一轮又点一次。"""
        def left_result():
            return self.find_one(RESULT_WIN) is None and self.find_one(RESULT_FAIL) is None

        if not self.wait_until(left_result, time_out=time_out, raise_if_not_found=False):
            raise Exception(f'点了结算页的按钮之后 {time_out} 秒还停在结算页')
