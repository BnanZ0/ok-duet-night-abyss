from qfluentwidgets import FluentIcon
import time

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.dna_ui.Defs import COORD

logger = Logger.get_logger(__name__)

# ---- 界面判据 label（标注在 ok_templates，运行期从 assets 的 coco 标注取模板）----
# 和沉浸式戏剧一样，这些 label 的搜索框就是 coco 标注本身（框架按标注位置 ±0.4% 的方差搜），
# 位置固定、框也很紧，所以不写进 Defs.DISCRIMINATORS；点击坐标统一放 Defs.COORD。
START_BTN = 'syr_start_btn'                    # 阵容页「开始挑战」按钮里的 ◯ 图标
HUD_START = 'syr_hud_start'                    # 局内左上角金色菱形：关卡已加载、还没开战
HUD_FIGHT = 'syr_hud_fight'                    # 同一个菱形的战斗态标注，只做判据兜底
RESULT_RESTART = 'syr_hud_restart'             # 结算页「重新开始」的环形箭头
START_CONFIRM = 'start_screen_start_btn_3_1'   # 「确认进入」弹窗的「确定」（各模式共用）
ESC_RETRY = 'esc_retry'                        # 局内菜单「重新开始」（和戏剧共用同一个菜单）
RESTART_CONFIRM = 'esc_restart_check_btn'      # 「是否重新开始战斗」二次确认弹窗的「确定」

# 「已开战」用的颜色框（Defs.SCREEN_BOX 里的名字）
HUD_MARKER_BOX = 'SYR_HUD_MARKER'

# 左上角菱形变红 = 已开战，**只看颜色**：金/红两个菱形是同一个控件、形状完全一样，
# 去均值归一化的相关度（TM_CCOEFF_NORMED，框架默认）会把绝对色差抵掉 —— 靠模板分数分不开
# （戏剧那边实测金/红两个模板互相匹配 0.863，高于阈值 0.8）。红色占比实测（阈值 0.15）：
#   未开战 syr_hud.png 0.0000（#fff19f 一类金色）
#   已开战 syr_hud_fighting.png 0.6154（#cc2f3a 一类红色）
#   阵容页 syr_start.png / 结算页 syr_result.png 同位置都是 0.0000
# 下限取 185：阵容页同位置的背景是暗棕（#904c32，r=144），下限放宽到 120 会在阵容页误判成已开战。
SYR_MARKER_RED = {'r': (185, 255), 'g': (0, 120), 'b': (0, 120)}
SYR_MARKER_RED_THRESHOLD = 0.15

# 走位时间轴，录自 `mod\示例-脚本工具\回放和录制软件\scripts\map\custom\狩月人.json`
# （12 个动作、总长 5.2618 秒；这份录制里没有 f12 热键）。时间点换算成"相对上一步的等待秒数"：
#   (等待秒数, 按键, 按下/抬起)
WALK_SCHEDULE = (
    (0.5286, 'w', True),
    (0.3853, 'shift', True),
    (0.4403, 'shift', False),
    (0.9652, 'shift', True),
    (0.8642, 'shift', False),
    (0.4469, 'shift', True),
    (0.3370, 'shift', False),
    (0.0844, 'w', False),
    (0.0051, 'd', True),
    (0.3361, 'shift', True),
    (0.4116, 'shift', False),
    (0.4571, 'd', False),
)
# 走位期间按住 lalt 锁视角，免得防挂机的鼠标抖动把镜头带偏（其他全自动任务同样处理）
WALK_HOLD_KEYS = ('lalt',)
# shift 是录制里的冲刺键，也要松开：中途被打断时不能让它一直按着
WALK_RELEASE_KEYS = ('w', 'a', 's', 'd', 'shift')

# 关卡加载完之后先稳这么久再走位：判据刚出来时角色还在落地/过场收尾，这时候按走位键会被吃掉
RUN_SETTLE = 1
# 点了「开始挑战」/「重新开始」之后等离开当前界面、等进关卡加载完成的上限
LOAD_TIME_OUT = 30
# 走位之后等开战（菱形变红）的上限：等不到就是这次没开起来，ESC 重新开始一局
FIGHT_TIME_OUT = 10
# 兜底：红菱形连续消失这么久（掉线、卡在读条、结算页被漏读）才算没在战斗：ESC 重开一局。
# 技能不跟这个兜底走 —— 技能按 SKILL_STOP_DELAY 那条规则停手，见 tick_skills。
NO_COMBAT_TIME_OUT = 30
# 技能总闸宽限：红菱形连续消失超过这么久才停手（实机上判据会闪，闪一下不算）。见 tick_skills
SKILL_STOP_DELAY = 2.0
# 连续失败（开不了战 / 结算点不动）几次后报错停止。配置里只留「打几次」，这个用内部常量
RESTART_FAILURE_LIMIT = 3


class AutoMoonHunterTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动狩月人（狩月人之阶）。

    一局的结构：阵容页点「开始挑战」-> 读条 -> 局内左上角出现金色菱形（`syr_hud_start`）
    -> 按录制路线走位触发战斗 -> 菱形变红（`syr_hud_fight`）= 已开战，按全局技能配置打
    -> 打完出现结算页（`syr_hud_restart`）-> 点「重新开始」直接回到读条，循环下一局。
    副本内部没有分阶段/分关卡，所以没有关卡号 OCR、没有层间移动配置，配置只有「打几次」。

    开不了战：走位之后 FIGHT_TIME_OUT 秒还没变红就 ESC -> 点「重新开始」重来一局。
    结束条件：出现结算页算一局打完，按「打几次」计数（0 = 无限循环）。
    连续失败 RESTART_FAILURE_LIMIT 次报错停止。

    技能：只在菱形变红（真在打）期间释放。走位、结算、重开之前都会关掉技能总闸
    （见 `stop_skills`），免得按出去的技能被游戏缓冲到下一局的开场、把走位吃掉。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动狩月人"
        self.description = "全自动"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        # 这个模式没有轮次、战斗超时，也没有「挂机模式」那套移动/复位配置：只有"打几次"
        self.default_config.update({
            "打几次": 0,
        })
        self.config_description.update({
            "打几次": "打几次，0 = 无限循环",
        })

        self.skill_tick = self.create_skill_ticker()
        # 技能总闸（见 stop_skills / tick_skills）：默认开着，战斗判据连续消失超时，
        # 或者走到走位/结算/重开这些窗口才关上。
        self.skills_stopped = False
        self.combat_seen_at = time.time()
        self.current_run = 0
        self.run_failures = 0
        self.mission_started = False

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
            logger.error("AutoMoonHunterTask error", e)
            raise

    def do_run(self):
        """主循环：看画面属于哪个界面就处理哪个，打满次数正常返回。

        启动时必须停在阵容页或结算页（中途的加载/过场画面只是等一下）。
        """
        self.init_all()
        if not self.known_screen():
            raise Exception("请先把游戏停在「狩月人之阶」阵容页或结算页上再启动任务")
        while True:
            if self.find_one(START_BTN):
                self.start_mission()
            elif self.find_one(RESULT_RESTART):
                if self.handle_result():
                    return
            elif self.in_moon_hunter_mission():
                self.handle_in_mission()
            else:
                self.wait_screen_back()
            self.sleep(0.2)

    def wait_screen_back(self, time_out=LOAD_TIME_OUT):
        """卡在加载/过场画面：等认出下一个界面，等太久就报错（别无限空转）。"""
        self.log_info('等待界面切换（加载/过场）...')
        deadline = time.time() + time_out
        while time.time() < deadline:
            self.sleep(0.5)
            if self.known_screen():
                return
        raise Exception(f'等了 {time_out} 秒还认不出当前界面，停止任务')

    def init_all(self):
        """每次启动都从头开始：技能计时器重新武装、计数清零、这一局还没走过位。"""
        self.load_char()
        self.skill_tick.reset()
        self.skills_stopped = False
        self.combat_seen_at = time.time()
        self.current_run = 0
        self.run_failures = 0
        self.mission_started = False

    def target_runs(self):
        """读「打几次」配置：0 表示无限循环，读不出来也当无限。"""
        try:
            return max(0, int(self.config.get('打几次', 0)))
        except (TypeError, ValueError):
            return 0

    def note_failure(self, reason):
        """记一次连续失败：超过上限就报错停止（配置里只有「打几次」，上限用内部常量）。"""
        self.run_failures += 1
        if self.run_failures > RESTART_FAILURE_LIMIT:
            raise Exception(f'连续 {self.run_failures} 次{reason}，停止任务')
        self.log_info(f'{reason}（第 {self.run_failures} 次，最多 {RESTART_FAILURE_LIMIT} 次），'
                      f'ESC 重新开始')

    # ------------------------------------------------------------------
    # 界面判据
    # ------------------------------------------------------------------

    def known_screen(self):
        """是不是一个能开工的界面（阵容页 / 结算页 / 局内）。"""
        return (self.find_one(START_BTN) is not None
                or self.find_one(RESULT_RESTART) is not None
                or self.in_moon_hunter_mission())

    def in_moon_hunter_mission(self):
        """是不是在局内（局内菜单盖在 HUD 上时也算）。"""
        return self.in_team() or self.find_one(ESC_RETRY) is not None

    def find_hud_marker(self):
        """左上角那颗菱形（金/红都在同一个位置）。

        命中就代表"关卡已经加载完、可以开始走位"；局内菜单和结算页都不命中。
        """
        return self.find_one(HUD_START) or self.find_one(HUD_FIGHT)

    def is_in_combat(self):
        """左上角菱形变红 = 已开战（只看颜色，和界面语言、背景明暗都无关）。

        位置优先用菱形模板（只截菱形内部、不含背景，亮暗场景都能命中），没匹上就退回固定框 ——
        模板在明亮场景里会失手，差一点点就会把"已开战"漏判成没开战（表现：明明在打，
        却按"没进战斗"处理，几十秒后误判成超时重开一局）。
        红色占比（阈值 SYR_MARKER_RED_THRESHOLD）：未开战 0.0000 / 已开战 0.6154。
        """
        box = self.find_hud_marker() or self.screen_box(HUD_MARKER_BOX)
        return self.calculate_color_percentage(SYR_MARKER_RED, box) > SYR_MARKER_RED_THRESHOLD

    # ------------------------------------------------------------------
    # 阵容页
    # ------------------------------------------------------------------

    def left_start_screen(self):
        """已经不在阵容页（无论在加载还是已经进图）。"""
        return self.find_one(START_BTN) is None and self.find_one(START_CONFIRM) is None

    def start_mission(self, time_out=LOAD_TIME_OUT):
        """阵容页：点「开始挑战」，有「确认进入」弹窗就点「确定」，然后等离开阵容页。

        弹窗不是每次都有（游戏里能设成不再提示），而且弹窗一盖上来阵容页的「开始挑战」
        就被压暗到认不出来 —— 所以"弹窗出现"和"已经进图"都算这一步走通，谁先到算谁。
        云游戏会丢点击，所以点一次没动静就再点一次（间隔 1 秒）。
        """
        def confirm_or_left():
            return self.find_one(START_CONFIRM) is not None or self.left_start_screen()

        if not self.wait_until(confirm_or_left, time_out=time_out,
                               post_action=lambda: self.click_ui_coord(
                                   COORD.SYR_START, name=START_BTN, after_sleep=1),
                               raise_if_not_found=False):
            raise Exception(f'点了「开始挑战」之后 {time_out} 秒还停在阵容页'
                            f'（门票/体力不足或点击没生效）')
        if self.find_one(START_CONFIRM):
            if not self.wait_until(self.left_start_screen, time_out=time_out,
                                   post_action=lambda: self.click_ui_coord(
                                       COORD.START_CONFIRM, name=START_CONFIRM, after_sleep=1),
                                   raise_if_not_found=False):
                raise Exception('点了「确认进入」的「确定」之后没能进关卡（门票/体力不足？）')

    # ------------------------------------------------------------------
    # 局内：等加载 -> 走位 -> 打到结算页
    # ------------------------------------------------------------------

    def handle_in_mission(self):
        """局内一次处理：走位触发战斗，然后一直打到结算页或需要重开一局。"""
        if self.find_one(ESC_RETRY):
            # 局内菜单被打开了（一般是玩家自己按的 ESC）：关掉继续，绝不在这里点菜单
            self.send_key("esc", after_sleep=0.5)
            return
        if not self.mission_started:
            self.wait_mission_loaded()
            self.sleep(RUN_SETTLE)
            # 走位全程不许按技能：技能动作会把按下去的走位键吃掉
            self.stop_skills('走位')
            self.mission_started = True
            self.play_walk()
            # 每一局都是从零开始打，技能计时器必须重新武装：`reset()` 让下一次 tick 立刻触发
            self.skill_tick.reset()
        if not self.wait_combat():
            self.mission_started = False
            return
        if not self.fight_until_result():
            # 红菱形长时间不在（掉线、卡在读条）：已经重开了一局，退回重新走位
            self.mission_started = False

    def wait_mission_loaded(self, time_out=LOAD_TIME_OUT):
        """等关卡加载完：左上角菱形或者通用局内 HUD（左下角 Lv）出来都算。

        带上 `in_team()` 兜底是必须的：菱形模板在明亮的关卡场景里会失手，
        只用它会在那种关卡误报"没进关卡"。
        """
        if not self.wait_until(lambda: self.find_hud_marker() is not None or self.in_team(),
                               time_out=time_out, raise_if_not_found=False):
            raise Exception(f'等了 {time_out} 秒还没进关卡（门票/体力不足或掉线？）')

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

    def wait_combat(self, time_out=FIGHT_TIME_OUT):
        """走位之后等开战（左上角菱形变红）；等不到就判这次没开起来，ESC 重新开始一局。"""
        if self.wait_until(self.is_in_combat, time_out=time_out, raise_if_not_found=False):
            self.run_failures = 0
            return True
        self.note_failure(f'走位之后 {time_out} 秒还没开战')
        self.restart_in_mission()
        return False

    def fight_until_result(self):
        """挂机。返回 True = 结算页出现（这一局打完），False = 该重开一局。

        红菱形闪一下不算"没进战斗"（判据在实机上会闪）：只有连续消失 NO_COMBAT_TIME_OUT 秒
        （掉线、卡在读条、结算页被漏读后停在加载画面）才算没在战斗 —— 重开一局。
        技能不跟这个兜底走：技能按 SKILL_STOP_DELAY 那条规则停手（见 `tick_skills`），
        加载/结算期间一律不按。
        """
        no_combat_since = None
        while True:
            if self.find_one(RESULT_RESTART):
                return True
            if self.find_one(ESC_RETRY):
                self.stop_skills('局内菜单被打开')
                self.send_key("esc", after_sleep=0.5)
                continue
            in_combat = self.is_in_combat()
            if in_combat:
                no_combat_since = None
                self.run_failures = 0
            elif no_combat_since is None:
                no_combat_since = time.time()
            elif time.time() - no_combat_since > NO_COMBAT_TIME_OUT:
                self.note_failure(f'{NO_COMBAT_TIME_OUT} 秒没进战斗')
                self.restart_in_mission()
                return False
            self.tick_skills(in_combat)
            self.sleep(0.2)

    def restart_in_mission(self, time_out=10, load_time_out=LOAD_TIME_OUT):
        """局内重来：ESC 开菜单 -> 点「重新开始」-> 点二次确认的「确定」。

        两个都是云游戏爱丢的点击，所以都是"点到出结果为止"：先点到弹窗出来，再点到弹窗消失。
        重开会把关卡重新加载一遍，菜单/弹窗/加载画面都会盖掉菱形判据，所以"先消失再回来"
        正好当重开完成的信号；万一它没消失（秒重开）也不会卡住，直接往下走。
        """
        self.stop_skills('重新开始')
        start = time.time()
        while not self.find_one(ESC_RETRY):
            if time.time() - start > time_out:
                raise Exception('局内菜单打不开，没法重新开始')
            self.send_key("esc")
            self.wait_until(lambda: self.find_one(ESC_RETRY) is not None, time_out=2,
                            raise_if_not_found=False)
        self.wait_until(
            condition=lambda: self.find_one(RESTART_CONFIRM) is not None,
            post_action=lambda: self.click_ui_coord(COORD.ESC_MENU_RETRY, name=ESC_RETRY,
                                                    after_sleep=0.5),
            time_out=time_out,
        )
        self.wait_until(
            condition=lambda: not self.find_one(RESTART_CONFIRM),
            post_action=lambda: self.click_ui_coord(COORD.ESC_MENU_RETRY_CONFIRM,
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

    # ------------------------------------------------------------------
    # 技能：只在真在打的时候放
    # ------------------------------------------------------------------

    def stop_skills(self, reason=None):
        """关掉技能总闸：关掉之后 `tick_skills` 一律不按，直到重新确认在战斗中。

        `create_skill_ticker` 的 tick 是同步的（按技能键和「释放后等待」都在一次调用里做完），
        所以闸门一关就真的不会再按技能。已经在按的那一发收不回来，靠调用点留出的提前量
        （走位之前、结算页之后整段加载时间）等它的动作走完。
        """
        if self.skills_stopped:
            return
        self.skills_stopped = True
        if reason:
            self.log_info(f'停止释放技能：{reason}')
        else:
            self.log_debug('停止释放技能：战斗判据消失')

    def tick_skills(self, in_combat):
        """按技能 —— 只认"确认在战斗中"，不在战斗状态就停手。

        以前这里是无条件 `skill_tick()`：结算页被漏读、加载这些"没在打"的帧上照样按技能，
        那一下会被游戏缓冲到下一局的开场 —— 人物还没走位先放一个技能，苏乙终结技这种
        长动作一锁，走位整段被吃掉。
        """
        if in_combat:
            self.combat_seen_at = time.time()
            if self.skills_stopped:
                self.skills_stopped = False
                self.log_debug('恢复释放技能')
        elif not self.skills_stopped and time.time() - self.combat_seen_at > SKILL_STOP_DELAY:
            self.stop_skills()
        if self.skills_stopped:
            return
        self.skill_tick()

    # ------------------------------------------------------------------
    # 结算页
    # ------------------------------------------------------------------

    def handle_result(self):
        """结算页：点「重新开始」直接开下一局。返回是否该结束任务。

        点之前先把技能停掉：结算页被漏读时技能还在按，那一下会跟着点击一起被带进下一局的开场，
        人物还没走位先放一个技能。结算页有 90 多秒的自动退出倒计时，所以检测到就立刻点。
        """
        self.stop_skills('结算页')
        self.mission_started = False
        self.run_failures = 0
        self.current_run += 1
        self.log_info(f'第 {self.current_run} 次完成')
        target = self.target_runs()
        if target and self.current_run >= target:
            self.log_info(f'已经打满 {target} 次，任务结束')
            return True
        self.click_ui_coord(COORD.SYR_RESTART, name=RESULT_RESTART, after_sleep=1)
        self.wait_left_result()
        return False

    def wait_left_result(self, time_out=LOAD_TIME_OUT):
        """点了「重新开始」之后等离开结算页，免得下一轮又点一次。"""
        if not self.wait_until(lambda: self.find_one(RESULT_RESTART) is None,
                               time_out=time_out, raise_if_not_found=False):
            raise Exception(f'点了「重新开始」之后 {time_out} 秒还停在结算页（门票/体力不足？）')
