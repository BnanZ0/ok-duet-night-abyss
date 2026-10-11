# 自动狩月人（狩月人之阶）界面判据与流程测试
import unittest

from ok import TaskDisabledException
from src.config import config
from ok.test.TaskTestCase import TaskTestCase

from src.dna_ui.Defs import COORD, SCREEN_BOX
import src.tasks.fullauto.AutoMoonHunterTask as syr_module
from tests.support.task_helpers import check_image, run_fight_case
from src.tasks.fullauto.AutoMoonHunterTask import (
    AutoMoonHunterTask, FIGHT_TIME_OUT, HUD_FIGHT, HUD_MARKER_BOX, HUD_START,
    LOAD_TIME_OUT, NO_COMBAT_TIME_OUT, RESTART_FAILURE_LIMIT, RESULT_RESTART,
    RUN_SETTLE, SKILL_STOP_DELAY, START_BTN, START_CONFIRM, SYR_MARKER_RED,
    SYR_MARKER_RED_THRESHOLD, WALK_HOLD_KEYS, WALK_RELEASE_KEYS, WALK_SCHEDULE,
)

IMAGES = 'tests/images/'
OTHER_SHOTS = ('syr_start.png', 'syr_hud.png', 'syr_hud_fighting.png', 'syr_result.png')


class TestMoonHunterTask(TaskTestCase):
    task_class = AutoMoonHunterTask

    config = config

    def _check(self, image, finder, expected=True):
        check_image(self, IMAGES + image, finder, expected)

    # ---- 界面判据：四个 label 各认各的 ----

    def test_start_btn_only_on_the_lineup_screen(self):
        """阵容页「开始挑战」按钮里的 ◯ 图标只在阵容页命中。"""
        self._check('syr_start.png', lambda: self.task.find_one(START_BTN))
        for shot in ('syr_hud.png', 'syr_hud_fighting.png', 'syr_result.png'):
            self._check(shot, lambda: self.task.find_one(START_BTN), expected=False)

    def test_hud_marker_on_both_states(self):
        """左上角菱形金/红都算"关卡已加载"，阵容页和结算页都不命中。"""
        for shot in ('syr_hud.png', 'syr_hud_fighting.png'):
            self._check(shot, self.task.find_hud_marker)
        self._check('syr_start.png', self.task.find_hud_marker, expected=False)
        self._check('syr_result.png', self.task.find_hud_marker, expected=False)

    def test_combat_is_decided_by_colour(self):
        """金色 = 未开战，红色 = 已开战；阵容页/结算页同位置都不是战斗。

        两个菱形是同一个控件、形状一样，只能按颜色判（见模块里的实测注释）。
        """
        for shot, expected in (('syr_hud.png', False),
                               ('syr_hud_fighting.png', True),
                               ('syr_start.png', False),
                               ('syr_result.png', False)):
            self._check(shot, self.task.is_in_combat, expected=expected)

    def test_combat_colour_margin(self):
        """红色占比要有余量：未开战 0.0000，已开战 0.6154（阈值 0.15）。"""
        task = self.task
        self.set_image(IMAGES + 'syr_hud.png')
        idle = task.calculate_color_percentage(SYR_MARKER_RED, task.screen_box(HUD_MARKER_BOX))
        self.set_image(IMAGES + 'syr_hud_fighting.png')
        fighting = task.calculate_color_percentage(SYR_MARKER_RED, task.screen_box(HUD_MARKER_BOX))
        self.assertAlmostEqual(idle, 0.0, places=4, msg='未开战那一帧不该有红色')
        self.assertGreater(fighting, SYR_MARKER_RED_THRESHOLD * 3, '阈值至少留 3 倍余量')
        self.assertAlmostEqual(fighting, 0.6154, places=3, msg='已开战那一帧的红色占比实测值')

    def test_combat_survives_a_template_miss(self):
        """模板没匹上也不能把"已开战"漏判：退回固定框数颜色。"""
        self.set_image(IMAGES + 'syr_hud_fighting.png')
        self.assertTrue(self.task.is_in_combat(), '亮场景的红菱形要认得出已开战')
        original = self.task.find_hud_marker
        try:
            self.task.find_hud_marker = lambda: None
            self.assertTrue(self.task.is_in_combat(), '模板没匹上时要按固定框的颜色兜底')
        finally:
            self.task.find_hud_marker = original

    def test_result_restart_only_on_the_result_screen(self):
        """结算页「重新开始」的环形箭头只在结算页命中。"""
        self._check('syr_result.png', lambda: self.task.find_one(RESULT_RESTART))
        for shot in ('syr_start.png', 'syr_hud.png', 'syr_hud_fighting.png'):
            self._check(shot, lambda: self.task.find_one(RESULT_RESTART), expected=False)

    def test_in_mission(self):
        """局内 = 通用 HUD（in_team）或局内菜单；阵容页/结算页都不算。

        菜单判据用的是共用的设置齿轮（`find_esc_menu`）—— 这个模式的菜单里没有「重新开始」，
        不能像戏剧那样拿那个按钮当判据，所以这里用戏剧的菜单截图（同一个局内菜单）来钉住。
        """
        for shot in ('syr_hud.png', 'syr_hud_fighting.png', 'theatre_esc_menu.png'):
            self._check(shot, self.task.in_moon_hunter_mission, expected=True)
        for shot in ('syr_start.png', 'syr_result.png'):
            self._check(shot, self.task.in_moon_hunter_mission, expected=False)

    def test_known_screen(self):
        """阵容页 / 结算页 / 局内都算能开工的界面。"""
        for shot in OTHER_SHOTS:
            self._check(shot, self.task.known_screen, expected=True)

    # ---- 走位时间轴：录制的路径不能被改坏 ----

    def test_walk_schedule_matches_recording(self):
        """时间轴来自 `mod\\...\\scripts\\map\\custom\\狩月人.json`（总长 5.2618 秒）。

        录制里 12 个动作、没有 f12 热键：w 按下之后反复点 shift（冲刺），再松 w、按 d 右转。
        """
        total = sum(wait for wait, _, _ in WALK_SCHEDULE)
        self.assertAlmostEqual(total, 5.2618, places=4, msg=f'走位总时长 {total} 和录制对不上')
        self.assertAlmostEqual(WALK_SCHEDULE[0][0], 0.5286, places=4, msg='开头要等 0.5286 秒')
        self.assertEqual([(key, down) for _, key, down in WALK_SCHEDULE],
                         [('w', True), ('shift', True), ('shift', False), ('shift', True),
                          ('shift', False), ('shift', True), ('shift', False), ('w', False),
                          ('d', True), ('shift', True), ('shift', False), ('d', False)])

    def test_play_walk_holds_lalt_and_releases_everything(self):
        """走位全程按住 lalt 锁视角；走完和被打断两种情况下，用到的键都要松开。

        踩过的隐患：中途抛 TaskDisabledException（玩家停任务）时如果没在 finally 里松键，
        w/d/shift 会一直按着，角色会一直往前跑。
        """
        task = self.task
        original = {name: getattr(task, name) for name in ('sleep', 'send_key_down', 'send_key_up')}
        expected = set(WALK_RELEASE_KEYS) | set(WALK_HOLD_KEYS)
        used = {key for _, key, _ in WALK_SCHEDULE} | set(WALK_HOLD_KEYS)
        self.assertTrue(used <= expected, '时间轴用到的键都要在松开名单里')
        downs, ups = [], []
        try:
            task.send_key_down = downs.append
            task.send_key_up = ups.append
            task.sleep = lambda seconds: None

            task.play_walk()
            self.assertEqual(downs[0], 'lalt', '走位一开始就要按住 lalt')
            self.assertEqual(set(ups), expected, '走位用到的键必须全部松开')

            ups.clear()

            def boom(seconds):
                raise TaskDisabledException()

            task.sleep = boom
            with self.assertRaises(TaskDisabledException):
                task.play_walk()
            self.assertEqual(set(ups), expected, '走位被打断时键也必须全部松开')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 配置 ----

    def test_config_shape(self):
        """配置只有「打几次」：没有轮次/超时时间，也没有「挂机模式」那套移动配置。"""
        config = self.task.default_config
        self.assertEqual(config['打几次'], 0, '默认 0 = 无限循环')
        self.assertIn('0 = 无限循环', self.task.config_description['打几次'])
        for key in ('轮次', '超时时间', '随机游走', '挂机模式', '开局向前走'):
            self.assertNotIn(key, config, f'这个模式不该有「{key}」配置')

    def test_target_runs(self):
        task = self.task
        original = task.config
        try:
            task.config = {'打几次': 0}
            self.assertEqual(task.target_runs(), 0, '0 = 无限循环')
            task.config = {'打几次': '5'}
            self.assertEqual(task.target_runs(), 5, '配置控件给字符串也要能读')
            task.config = {'打几次': 'x'}
            self.assertEqual(task.target_runs(), 0, '读不出来就当无限')
            task.config = {'打几次': -3}
            self.assertEqual(task.target_runs(), 0, '负数当无限')
        finally:
            task.config = original

    # ---- 启动位置 / 阵容页 ----

    def test_start_requires_known_screen(self):
        """停在游戏主界面/菜单里启动 -> 直接报错，不乱点。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('init_all', 'find_one', 'in_moon_hunter_mission')}
        try:
            task.init_all = lambda: None
            task.find_one = lambda *a, **kw: None
            task.in_moon_hunter_mission = lambda: False
            with self.assertRaises(Exception) as caught:
                task.do_run()
            self.assertIn('阵容页', str(caught.exception))
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_start_mission_clicks_start_then_confirm(self):
        """阵容页：点「开始挑战」；出现「确认进入」弹窗就点「确定」，再等离开阵容页。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('find_one', 'click_ui_coord')}
        clicks = []
        stage = {'n': 0}

        def fake_find_one(name, *args, **kwargs):
            if name == START_BTN:
                return 'box' if stage['n'] == 0 else None
            if name == START_CONFIRM:
                return 'box' if stage['n'] == 1 else None
            return None

        def fake_click(coord, **kwargs):
            clicks.append(coord)
            stage['n'] += 1

        try:
            task.find_one = fake_find_one
            task.click_ui_coord = fake_click
            task.aborted_run = True
            task.start_mission(time_out=1)
            self.assertEqual(clicks, [COORD.SYR_START, COORD.START_CONFIRM],
                             '先点「开始挑战」，有弹窗再点「确定」')
            self.assertFalse(task.aborted_run,
                             '从阵容页开新一局要清掉「中途退出」标记，否则会吞掉下一张结算页的计数')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 局内：走位一次 + 等开战 ----

    def test_run_walks_once_then_fights(self):
        """每次进局内只走一次位：加载 -> 稳 RUN_SETTLE 秒 -> 关技能 -> 走位 -> 等开战 -> 打。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'wait_mission_loaded', 'play_walk', 'stop_skills', 'sleep',
                     'wait_combat', 'fight_until_result', 'skill_tick', 'mission_started')}
        events = []

        def fake_tick():
            pass

        fake_tick.reset = lambda: events.append('reset')
        try:
            task.find_one = lambda *a, **kw: None
            task.wait_mission_loaded = lambda *a, **kw: events.append('loaded')
            task.sleep = lambda seconds: events.append(('sleep', seconds))
            task.play_walk = lambda: events.append('walk')
            task.stop_skills = lambda *a, **kw: events.append('stop_skills')
            task.wait_combat = lambda: events.append('wait_combat') or True
            task.fight_until_result = lambda: events.append('fight') or True
            task.skill_tick = fake_tick

            task.mission_started = False
            task.handle_in_mission()
            self.assertEqual(events, ['loaded', ('sleep', RUN_SETTLE), 'stop_skills', 'walk',
                                      'reset', 'wait_combat', 'fight'],
                             '加载 -> 稳 RUN_SETTLE 秒 -> 关技能 -> 走位 -> 重新武装技能 -> 打')
            self.assertEqual(RUN_SETTLE, 1)

            events.clear()
            task.handle_in_mission()                      # 同一局里再进一次
            self.assertEqual(events, ['wait_combat', 'fight'], '同一局内不该重复走位')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_walk_never_combat_restarts_and_rewalks(self):
        """走位之后一直没开战：记一次失败 + 退出副本重开，并把局内状态清掉（下次重新走位）。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'wait_mission_loaded', 'play_walk', 'stop_skills', 'sleep',
                     'wait_until', 'restart_in_mission', 'skill_tick', 'run_failures', 'log_info')}
        restarts = []
        logs = []
        try:
            task.find_one = lambda *a, **kw: None
            task.wait_mission_loaded = lambda *a, **kw: None
            task.play_walk = lambda: None
            task.stop_skills = lambda *a, **kw: None
            task.sleep = lambda seconds: None
            task.skill_tick = lambda: None
            task.wait_until = lambda *a, **kw: False        # 等不到开战
            task.restart_in_mission = lambda *a, **kw: restarts.append(1)
            task.log_info = lambda message, *a, **kw: logs.append(message)
            task.run_failures = 0
            self.assertFalse(task.wait_combat(), '等不到开战要返回 False')
            self.assertEqual(restarts, [1], '退出副本重开一局')
            self.assertEqual(task.run_failures, 1)
            self.assertTrue(any(str(FIGHT_TIME_OUT) in message for message in logs))
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_restart_in_mission_exits_then_waits_a_known_screen(self):
        """重开一局 = 关技能 -> 标记中途退出 -> 退出副本 -> 等回结算页或阵容页。

        退出之后两种落点都要接住：正常落结算页（挑战失败），结算页倒计时自动退出时落阵容页。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('exit_mission', 'find_one', 'wait_until', 'stop_skills', 'aborted_run')}
        events = []
        try:
            task.stop_skills = lambda *a, **kw: events.append('stop_skills')
            task.exit_mission = lambda *a, **kw: events.append('exit_mission') or True
            task.wait_until = lambda condition, *a, **kw: bool(condition())
            task.aborted_run = False

            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_RESTART else None
            task.restart_in_mission()
            self.assertEqual(events, ['stop_skills', 'exit_mission'])
            self.assertTrue(task.aborted_run, '要标记这一页是中途退出来的')

            events.clear()
            task.find_one = lambda name, *a, **kw: 'box' if name == START_BTN else None
            task.restart_in_mission()                       # 落阵容页也算回到已知界面
            self.assertEqual(events, ['stop_skills', 'exit_mission'])
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_restart_in_mission_failure_modes(self):
        """菜单打不开、退出后一直认不出界面：都要报错停止，不能干等或乱点。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('exit_mission', 'find_one', 'wait_until', 'stop_skills', 'aborted_run')}
        try:
            task.stop_skills = lambda *a, **kw: None
            task.wait_until = lambda *a, **kw: False
            task.find_one = lambda *a, **kw: None
            task.aborted_run = False

            task.exit_mission = lambda *a, **kw: False
            with self.assertRaises(Exception) as caught:
                task.restart_in_mission()
            self.assertIn('局内菜单', str(caught.exception))

            task.exit_mission = lambda *a, **kw: True
            with self.assertRaises(Exception) as caught:
                task.restart_in_mission()
            self.assertIn('结算页或阵容页', str(caught.exception))
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_failures_stop_after_the_limit(self):
        """连续失败超过内部上限就报错停止，不能无限重开。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('run_failures', 'log_info')}
        try:
            task.log_info = lambda *a, **kw: None
            task.run_failures = RESTART_FAILURE_LIMIT
            with self.assertRaises(Exception) as caught:
                task.note_failure('走位之后开不了战')
            self.assertIn('停止任务', str(caught.exception))
            self.assertEqual(task.run_failures, RESTART_FAILURE_LIMIT + 1)
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 挂机：什么时候算打完、什么时候算没进战斗 ----

    def _fight_case(self, in_combat_seq, exit_at, seconds_per_poll):
        """跑一遍 fight_until_result，返回（返回值, 技能次数, 日志, 重开次数）。"""
        def setup(task):
            task.run_failures = 0

        return run_fight_case(self, syr_module, RESULT_RESTART, in_combat_seq, exit_at,
                              seconds_per_poll, patch_names=('run_failures',), setup=setup)

    def test_fight_returns_true_on_result_screen(self):
        """出现结算页 = 这一局打完：返回 True（交给主循环去点「重新开始」）。"""
        result, skills, logs, restarts = self._fight_case([True, True, True], exit_at=3,
                                                         seconds_per_poll=0.5)
        self.assertTrue(result)
        self.assertEqual(len(skills), 2, '结算页出现之前一直在放技能')
        self.assertEqual(logs, [])
        self.assertEqual(restarts, [])

    def test_fight_never_pauses_when_the_diamond_blinks(self):
        """红菱形闪一下照常放技能，也不打任何日志、不重开。"""
        result, skills, logs, restarts = self._fight_case([False, True, True], exit_at=3,
                                                         seconds_per_poll=0.5)
        self.assertTrue(result)
        self.assertEqual(len(skills), 2, '闪一下的那一轮也必须放技能')
        self.assertEqual(logs, [], '挂机期间不该打日志')
        self.assertEqual(restarts, [], '闪一下不算"没进战斗"')

    def test_fight_stops_skills_when_the_red_diamond_stays_away(self):
        """红菱形连续消失超过 SKILL_STOP_DELAY 秒就停手，重新确认在战斗中才恢复。

        停手是给"下一局的开场"留白：判据消失（加载画面、结算页被漏读）期间按出去的技能会被
        游戏缓冲到下一局开场，人物还没走位先放一个技能 —— 苏乙终结技那种长动作一锁，
        走位整段被吃掉。闪一下不算，30 秒的"没进战斗"兜底也不受影响。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'is_in_combat', 'skill_tick', 'log_info', 'sleep',
                     'restart_in_mission', 'run_failures', 'combat_seen_at', 'skills_stopped')}
        original_time = syr_module.time
        clock = {'now': 100.0}
        combat = {'state': True}
        fired = []
        states = [True, True] + [False] * 6 + [True, True]
        polls = {'n': 0}

        try:
            def fake_find_one(name, *args, **kwargs):
                return 'result' if polls['n'] >= len(states) and name == RESULT_RESTART else None

            def fake_is_in_combat():
                if polls['n'] < len(states):
                    combat['state'] = states[polls['n']]
                return combat['state']

            def fake_sleep(seconds):
                polls['n'] += 1
                clock['now'] += 0.5                     # 主循环 0.2 秒一轮，这里取 0.5 更好算

            task.find_one = fake_find_one
            task.is_in_combat = fake_is_in_combat
            task.skill_tick = lambda: fired.append(combat['state'])
            task.log_info = lambda *a, **kw: None
            task.sleep = fake_sleep
            task.restart_in_mission = lambda *a, **kw: None
            task.run_failures = 0
            task.combat_seen_at = 100.0
            task.skills_stopped = False
            syr_module.time = type('FakeTime', (), {'time': staticmethod(lambda: clock['now'])})

            self.assertTrue(task.fight_until_result())
            # 前两轮在战斗里照常放；判据消失后 SKILL_STOP_DELAY（2 秒 = 4 轮）内还放，
            # 再往后停手；判据回来才恢复。
            self.assertEqual(fired, [True, True, False, False, False, False, True, True])
            self.assertEqual(SKILL_STOP_DELAY, 2.0)
        finally:
            syr_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    def test_fight_restarts_after_no_combat_timeout(self):
        """红菱形连续消失 NO_COMBAT_TIME_OUT 秒 = 没进战斗：重开一局，不报错。"""
        result, skills, logs, restarts = self._fight_case([False] * 20, exit_at=99,
                                                         seconds_per_poll=5.0)
        self.assertFalse(result, '该重开一局：返回 False，让调用方重新走位')
        self.assertEqual(len(restarts), 1, '只重开一次，剩下的交给外层重走')
        self.assertTrue(any(str(NO_COMBAT_TIME_OUT) in message for message in logs),
                        f'日志要写清楚是 {NO_COMBAT_TIME_OUT} 秒没进战斗')

    # ---- 结算页 ----

    def test_result_click_stops_skills_first(self):
        """点「重新开始」之前先把技能停掉：这一下点击不能跟着一个刚按出去的技能进下一局。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result',
                     'mission_started', 'skills_stopped', 'current_run', 'run_failures',
                     'aborted_run')}
        stopped_at_click = []
        try:
            task.config = {'打几次': 0}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_RESTART else None
            task.click_ui_coord = lambda coord, **kw: stopped_at_click.append(task.skills_stopped)
            task.wait_left_result = lambda *a, **kw: None
            task.skills_stopped = False
            task.current_run = 0
            task.run_failures = 0
            task.aborted_run = False
            self.assertFalse(task.handle_result())
            self.assertEqual(stopped_at_click, [True], '点「重新开始」之前技能总闸必须已经关掉')
            self.assertEqual(task.current_run, 1)
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_result_counts_runs_and_stops_at_target(self):
        """打完一局算一次；「打几次」到了就结束，不再点「重新开始」。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result',
                     'mission_started', 'stop_skills', 'current_run', 'run_failures',
                     'aborted_run')}
        clicks = []
        try:
            task.config = {'打几次': 2}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_RESTART else None
            task.click_ui_coord = lambda coord, **kw: clicks.append(coord)
            task.wait_left_result = lambda *a, **kw: None
            task.stop_skills = lambda *a, **kw: None
            task.current_run = 0
            task.run_failures = 3
            task.aborted_run = False
            self.assertFalse(task.handle_result(), '第 1 次还不该结束')
            self.assertEqual(task.run_failures, 0, '打完一局要清零连续失败计数')
            self.assertTrue(task.handle_result(), '第 2 次打满就该结束')
            self.assertEqual(clicks, [COORD.SYR_RESTART], '打满之后不该再点「重新开始」')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_result_from_a_give_up_is_not_counted(self):
        """「走位没开起来 → 退出副本」落回的那张结算页：不计次、不清失败计数，照样点「重新开始」。

        「打几次」只数真打完的局数；连续失败由 note_failure 的 3 次上限兜底（0 = 无限时也一样）。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result',
                     'mission_started', 'stop_skills', 'current_run', 'run_failures',
                     'aborted_run', 'log_info')}
        clicks = []
        logs = []
        try:
            task.config = {'打几次': 2}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_RESTART else None
            task.click_ui_coord = lambda coord, **kw: clicks.append(coord)
            task.wait_left_result = lambda *a, **kw: None
            task.stop_skills = lambda *a, **kw: None
            task.log_info = lambda message, *a, **kw: logs.append(message)
            task.current_run = 1
            task.run_failures = 2
            task.aborted_run = True
            self.assertFalse(task.handle_result(), '中途退出的那一页不算打满')
            self.assertEqual(task.current_run, 1, '中途退出不计入「打几次」')
            self.assertEqual(task.run_failures, 2, '连续失败计数要留着，交给 3 次上限兜底')
            self.assertFalse(task.aborted_run, '标记用掉就要清掉')
            self.assertEqual(clicks, [COORD.SYR_RESTART], '照样点「重新开始」继续')
            self.assertTrue(any('不计入次数' in message for message in logs))
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_wait_left_result_raises_when_stuck(self):
        """点了「重新开始」还停在结算页 -> 报错停止（门票/体力不足时就是这个样子）。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('find_one', 'wait_until')}
        try:
            task.find_one = lambda *a, **kw: 'box'
            task.wait_until = lambda *a, **kw: False
            with self.assertRaises(Exception) as caught:
                task.wait_left_result(time_out=1)
            self.assertIn('结算页', str(caught.exception))
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 共用坐标 / 判据框的出处 ----

    def test_defs_entries(self):
        """点击坐标和颜色兜底框都在 Defs 里，共用坐标和戏剧是同一份。"""
        from src.dna_ui.Defs import COORD as coords
        self.assertEqual(coords.SYR_START, (1277, 810))
        self.assertEqual(coords.SYR_RESTART, (588, 792))
        self.assertEqual(coords.THEATRE_ESC_RETRY, coords.ESC_MENU_RETRY)
        self.assertEqual(coords.THEATRE_RESTART_CONFIRM, coords.ESC_MENU_RETRY_CONFIRM)
        self.assertEqual(coords.THEATRE_START_CONFIRM, coords.START_CONFIRM)
        self.assertEqual(SCREEN_BOX.SYR_HUD_MARKER, (1600, 900, 45, 273, 51, 286, True))
        self.assertEqual(HUD_START, 'syr_hud_start')
        self.assertEqual(HUD_FIGHT, 'syr_hud_fight')
        self.assertEqual(RESULT_RESTART, 'syr_hud_restart')
        self.assertEqual(START_BTN, 'syr_start_btn')
        self.assertEqual(LOAD_TIME_OUT, 30)


if __name__ == '__main__':
    unittest.main()
