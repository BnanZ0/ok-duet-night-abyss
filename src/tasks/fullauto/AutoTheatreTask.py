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
# 兜底：按 F 开战之后到结算页出现之前一律算战斗、从不停手（判据在实机上会闪，拿它控制节奏
# 会让技能一顿一顿）。只有红菱形连续消失这么久（掉线、卡在读条、结算页被漏读后停在
# "开启第 X 试炼"那一阶段）才算没进战斗：重开一局，退回去重走第 1 层的走位开机关。
NO_COMBAT_TIME_OUT = 30

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
# 新关卡第 1 层：判据刚出现时角色还在落地/过场收尾，这时候按走位键会被吃掉前面一段
# （表现就是"走位变短了、走不到机关"），所以等关卡加载完再稳这么久才开始走位。
FIRST_LAYER_SETTLE = 1
# 切层之后：角色可能还在攻击/受击后摇里，这时候按 W 会被吃掉（表现就是"向前走被打断"），
# 先等这么久再执行「挂机模式」的移动/复位。
LAYER_SWITCH_SETTLE = 1.5
# 切层之后等目标栏变红（新一层真的开打了）的上限：关号文字是**先变**的，菱形要等切层动画
# 走完才变红 —— 文字一变就往前走的话，那几秒的移动会被切层动画吃掉（实机观察到两层都是这样）。
# 等满上限还不红（加载慢、掉线，或者结算页被漏读后停在新关卡的"开启第 X 试炼"阶段）只记一条
# 警告，照常往下走；真的没进战斗由 NO_COMBAT_TIME_OUT 那条兜底重开。
STAGE_RED_TIME_OUT = 15


class AutoTheatreTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动沉浸式戏剧（不朽剧目·勇者征程）。

    关卡结构：一个关卡 5 层（第 1~5 试炼），只有**第 1 层**要走到机关按 F 开战；
    第 2~5 层游戏自己切、自己开打。所以「挂机模式」那套移动/复位配置只在**层与层之间**
    执行（第 1 层走录制路线），脚本不数层、也没有 BOSS 层的特例。

    结束条件：出现结算页 = 这一局打完，按「打几层」计数。挂机期间红菱形连续消失
    NO_COMBAT_TIME_OUT 秒（掉线、卡读条、结算页被漏读后停在"开启第 X 试炼"阶段）就重开
    一局，退回第 1 层重新走位开机关。

    失败重试：走位/开机关连续失败、结算连续失败各自计数，配置 N 表示允许重试 N 次、
    第 N+1 次连续失败报错停止；中间成功一次就清零。
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
        # 云游戏实拍帧糊、模板分低，给足重试轮次
        self.action_timeout = 20
        self.current_floor = 0
        self.interact_failures = 0
        self.no_combat_failures = 0
        self.result_failures = 0
        self.mission_started = False
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
        self.no_combat_failures = 0
        self.result_failures = 0
        self.mission_started = False
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

        位置优先用菱形模板（只截菱形内部、不含背景，亮暗场景都能命中），没匹上就退回固定框 ——
        离线实测亮场景那颗菱形只有 0.802，压着 0.8 的阈值，差一点点就会把"已开战"漏判成
        没开战（表现：明明在打，却按"没进战斗"处理，30 秒后误判成超时重开一局）。
        红色占比（阈值 0.15）：模板框内 金 0.000 / 红 0.89~0.91；固定框内 金 0.000 / 红 0.23~0.26。
        """
        box = self.find_objective_panel() or self.screen_box(OBJECTIVE_DIAMOND_BOX)
        return self.calculate_color_percentage(OBJECTIVE_RED, box) > OBJECTIVE_RED_THRESHOLD

    def handle_in_mission(self):
        """关内一次处理：第 1 层走位开机关，然后一直挂到结算页或需要重开一局。"""
        if self.find_one(ESC_RETRY):
            # 局内菜单被打开了（一般是玩家自己按的 ESC）：关掉继续，绝不在这里点菜单
            self.send_key("esc", after_sleep=0.5)
            return
        if not self.mission_started:
            # 第 1 层：走录制路线到机关按 F 开战，**不执行「挂机模式」那套移动/复位配置**
            # （那个配置只在层与层之间用）。判据刚出来时角色还在落地收尾，先稳一秒再走。
            self.wait_mission_loaded()
            self.sleep(FIRST_LAYER_SETTLE)
            self.mission_started = True
            self.walk_and_interact()
            # 每一局都是从零开始打，技能计时器必须重新武装：`reset()` 让下一次 tick 立刻触发。
            # 不重置的话长频率技能（比如「终结技 600 秒」）只会在第一层放，后面都在等剩余间隔。
            self.skill_tick.reset()
            self.reset_stage_detector()
        if not self.fight_until_result():
            # 30 秒没进战斗（含结算页被漏读、掉线）：已经重开了一局，退回第 1 层重新走位开机关
            self.mission_started = False

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
        # 弹窗没了不等于真重开了：局内菜单必须也关掉，否则走位键全打进菜单里。
        # 云游戏丢那一下点击时就是这种情况：菜单还开着，可 in_team() 已经是真，
        # wait_mission_loaded() 会立刻放行 → 后面每一步都失败。
        if not self.wait_until(lambda: self.find_one(ESC_RETRY) is None, time_out=time_out,
                               raise_if_not_found=False):
            raise Exception('点了「重新开始」之后局内菜单一直没关掉，停止任务')
        self.wait_mission_loaded(time_out=load_time_out)

    def fight_until_result(self):
        """挂机。返回 True = 结算页出现（这一局打完），False = 该重开一局。

        进战斗之后**一律算战斗状态、从不停手**：判据在实机上会闪，拿它们控制"停不停手"
        会让技能一顿一顿的。只有红菱形连续 NO_COMBAT_TIME_OUT 秒都不在（掉线、卡在读条、
        结算页被漏读后停在"开启第 X 试炼"那一阶段）才算没进战斗 —— 重开一局，
        退回第 1 层重新走位开机关。

        层与层之间（关号变了）就地处理：按「挂机模式」处理一次角色位置，然后接着挂。
        """
        no_combat_since = None
        while True:
            if self.find_one(RESULT_WIN) or self.find_one(RESULT_FAIL):
                return True
            if self.find_one(ESC_RETRY):
                self.send_key("esc", after_sleep=0.5)
                continue
            if self.is_in_combat():
                no_combat_since = None
                self.no_combat_failures = 0
            elif no_combat_since is None:
                no_combat_since = time.time()
            elif time.time() - no_combat_since > NO_COMBAT_TIME_OUT:
                self.no_combat_failures += 1
                if self.no_combat_failures > self.retry_limit('开机关重试次数'):
                    raise Exception(f'连续 {self.no_combat_failures} 次开不了战，停止任务')
                self.log_info(f'{NO_COMBAT_TIME_OUT} 秒没进战斗，重开一局'
                              f'（第 {self.no_combat_failures} 次）')
                self.restart_in_mission()
                return False
            if self.update_stage_text(self.read_stage_text()):
                self.log_info('检测到切层，等目标栏变红（新一层真的开打）再处理角色位置')
                if not self.wait_until(self.is_in_combat, time_out=STAGE_RED_TIME_OUT,
                                       raise_if_not_found=False):
                    self.log_warning(f'切层后等了 {STAGE_RED_TIME_OUT} 秒目标栏还没变红，'
                                     f'照常处理角色位置')
                self.sleep(LAYER_SWITCH_SETTLE)
                self.apply_afk_mode()
                self.reset_stage_detector()
            self.skill_tick()
            self.sleep(0.2)

    # ------------------------------------------------------------------
    # 切层（关号变了）
    # ------------------------------------------------------------------

    def reset_stage_detector(self):
        """每局开始（第 1 层按完 F）调用：第一次读到的关号只当基准点，不算切层。"""
        self.stage_text = None
        self.stage_pending = None
        self.stage_pending_count = 0
        self.stage_next_ocr = 0.0

    def read_stage_text(self):
        """读一次关号；读不到就返回 None（没到该读的时间 / 认不出 / 分数不够）。

        返回 None 只说明"这一轮没有信息"，**不代表关号变了**，调用方必须把它当透明的。
        实测有些切换阶段 HUD 根本不显示那行字，加上主循环 0.2 秒一轮、OCR 1 秒一次的节流，
        每两次真读数之间都夹着好几个 None。

        1 秒一次的小区域 OCR 只花几十毫秒，没必要像波次那样丢线程池。
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
        """把一次读数喂进状态机：连续 STAGE_CONFIRM_COUNT 次读到同一个新关号就是切层了。

        文字先变、层后切，中间还有半截读数，所以要连续确认。
        """
        if text is None:
            # 空读数完全透明：不改基准、不清候选、不动计数。它既不能算一次确认，也不能把已经
            # 攒下的"连续 3 次"打断 —— 打断的后果是切层永远确认不了，层间的移动/复位全都不执行
            # （实机复现过：改成"空读数就清零"之后，向前走/复位再也不触发）。
            return False
        if self.stage_text is None or self.same_stage_text(text, self.stage_text):
            # 半截读数（比如只认出「试炼」两个字）也算同一层，但**不能拿它当基准**：
            # 基准一旦被缩成后缀，「第三试炼」也包含它，后面每次真的切层都会被吞掉
            # （实测：整整一局一次都没确认到，层与层之间的移动/复位全没执行）。
            if self.stage_text is None or len(text) > len(self.stage_text):
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
        self.log_info(f'检测到切层：{self.stage_text} -> {text}')
        self.stage_text = text
        self.stage_pending = None
        self.stage_pending_count = 0
        return True

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
