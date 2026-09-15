# 自动沉浸式戏剧（不朽剧目·勇者征程）界面判据与流程测试
import unittest
from types import SimpleNamespace

from ok import TaskDisabledException
from src.config import config
from ok.test.TaskTestCase import TaskTestCase

from src.dna_ui.Defs import COORD
import src.tasks.CommissionsTask as commissions_module
import src.tasks.fullauto.AutoTheatreTask as theatre_module
from src.tasks.fullauto.AutoTheatreTask import (
    AutoTheatreTask, ESC_RETRY, INTERACT_PROMPT, OBJECTIVE_PANEL, OBJECTIVE_PANEL_FIGHT,
    OBJECTIVE_RED, OBJECTIVE_RED_THRESHOLD, RESULT_FAIL, RESULT_RETRY, RESULT_WIN,
    RESTART_CONFIRM, START_BTN, START_CONFIRM, WALK_HOLD_KEYS, WALK_RELEASE_KEYS, WALK_SCHEDULE,
)

IMAGES = 'tests/images/'


class TestTheatreTask(TaskTestCase):
    task_class = AutoTheatreTask

    config = config

    def _check(self, image, finder, expected=True):
        self.set_image(IMAGES + image)
        feature = finder()
        self.logger.info(f'{image} -> {feature}')
        if isinstance(feature, bool):
            self.assertEqual(feature, expected, f'{image} should be {expected}')
        elif expected:
            self.assertIsNotNone(feature, f'{image} should match')
        else:
            self.assertIsNone(feature, f'{image} should not match')

    # ---- 阵容页 / 结算页：按钮判据各认各的 ----

    def test_start_screen_labels(self):
        """阵容页只有「前往」命中；「确认进入」弹窗里只有「确定」命中。

        弹窗一盖上来，背后的阵容页会被压暗到「前往」认不出来 —— 这一点必须在判据里
        钉死：`start_mission` 就是靠"弹窗出现 / 阵容页消失"来判断"这一步走通了"。
        """
        self._check('start_screen_3.png', lambda: self.task.find_one(START_BTN))
        self._check('start_screen_3.png', lambda: self.task.find_one(START_CONFIRM), expected=False)
        self._check('start_screen_3_1.png', lambda: self.task.find_one(START_CONFIRM))
        self._check('start_screen_3_1.png', lambda: self.task.find_one(START_BTN), expected=False)

    def test_start_btn_not_on_result_screens(self):
        """阵容页的「前往」不能出现在结算页上：结算页的「前往」是另一个图标。"""
        for shot in ('theatre_result_win.png', 'theatre_result_fail.png'):
            self._check(shot, lambda: self.task.find_one(START_BTN), expected=False)

    def test_result_win_and_fail_do_not_cross(self):
        """结算页胜负只看最右下角那颗按钮：黄色圆圈=前往(胜)、蓝色返回图标=败。

        两个图标只隔 33px，所以标注框（搜索框）必须保持紧框 —— 框放宽就会互相串味。
        余量（离线实测）：胜页 前往 1.0000 / 返回 0.292；败页 返回 1.0000 / 前往 0.178。
        """
        self.set_image(IMAGES + 'theatre_result_win.png')
        self.assertIsNotNone(self.task.find_one(RESULT_WIN), '胜页应命中「前往」')
        self.assertIsNone(self.task.find_one(RESULT_FAIL), '胜页不该命中「返回」')
        self.assertIsNone(self.task.find_one(RESULT_RETRY), '胜页没有「再次挑战」')

        self.set_image(IMAGES + 'theatre_result_fail.png')
        self.assertIsNotNone(self.task.find_one(RESULT_FAIL), '败页应命中「返回」')
        self.assertIsNotNone(self.task.find_one(RESULT_RETRY), '败页应命中「再次挑战」')
        self.assertIsNone(self.task.find_one(RESULT_WIN), '败页不该命中「前往」')

    # ---- 关内：目标栏判据 + 颜色判据 ----

    def test_objective_panel_on_both_states(self):
        """金菱形和红菱形是同一个控件（形状一样），两个都算"关卡已加载"。

        模板分数分不开这两种状态 —— 离线实测两个模板互相匹配 0.863/0.864（灰度 0.981），
        都高于阈值 0.8。所以"未开战/已开战"只能靠颜色占比判断，别把它换成模板分数。
        """
        for shot in ('theatre_start.png', 'theatre_fighting.png'):
            self._check(shot, self.task.find_objective_panel)
        for shot in ('theatre_esc_menu.png', 'theatre_result_win.png',
                     'theatre_result_fail.png', 'start_screen_3.png'):
            self._check(shot, self.task.find_objective_panel, expected=False)

    def test_combat_is_decided_by_colour(self):
        """金色（破解机关）= 未开战，红色（击败来袭的敌人）= 已开战。

        颜色占比（离线实测，阈值 0.15）：未开战 0.000；已开战暗场景 0.26 / 亮场景 0.23。
        其余界面（菜单/结算/阵容）同位置都是 0，所以不会误判成战斗。
        """
        for shot, expected in (('theatre_start.png', False),
                               ('theatre_fighting.png', True),
                               ('theatre_fighting_layer2.png', True),
                               ('theatre_esc_menu.png', False),
                               ('theatre_result_win.png', False),
                               ('theatre_result_fail.png', False),
                               ('start_screen_3.png', False)):
            self._check(shot, self.task.is_in_combat, expected=expected)

    def test_combat_survives_a_template_miss(self):
        """模板没匹上也不能把"已开战"漏判 —— 这就是切层白等 30 秒那个 bug。

        亮场景（第二试炼）那颗红菱形模板分只有 0.802，压着默认阈值 0.8：菱形在、颜色也对，
        只差 0.002。所以菱形模板失手时要退回固定框数颜色。
        """
        self.set_image(IMAGES + 'theatre_fighting_layer2.png')
        self.assertTrue(self.task.is_in_combat(), '亮场景的红菱形要认得出已开战')
        original = self.task.find_objective_panel
        try:
            self.task.find_objective_panel = lambda: None
            self.assertTrue(self.task.is_in_combat(), '模板没匹上时要按固定框的颜色兜底')
        finally:
            self.task.find_objective_panel = original

    def test_interact_prompt_only_near_device(self):
        """「F 操作」提示只有走到机关旁边才有：这张截图是走位之后拍的，命中。

        走位到位的唯一判据就是它 —— 目标栏的菱形一进图就有了，和走没走到无关。
        已经开战（`theatre_fighting.png`）和菜单/结算/阵容页都不该命中。
        """
        self._check('theatre_start.png', lambda: self.task.find_one(INTERACT_PROMPT))
        for shot in ('theatre_fighting.png', 'theatre_esc_menu.png', 'theatre_result_win.png',
                     'theatre_result_fail.png', 'start_screen_3.png'):
            self._check(shot, lambda: self.task.find_one(INTERACT_PROMPT), expected=False)

    # ---- 关内判定：只有关内为真 ----

    def test_in_theatre_mission(self):
        """局内 HUD（含盖着 HUD 的局内菜单）为真，阵容页/结算页为假。

        `in_theatre_mission()` 误报的后果：结算页会被当成关内，主循环直接去走位、
        按 F，把流程带偏。
        """
        for shot in ('theatre_start.png', 'theatre_fighting.png', 'theatre_esc_menu.png'):
            self._check(shot, self.task.in_theatre_mission, expected=True)
        for shot in ('theatre_result_win.png', 'theatre_result_fail.png',
                     'start_screen_3.png', 'start_screen_3_1.png'):
            self._check(shot, self.task.in_theatre_mission, expected=False)

    def test_esc_retry_is_the_in_mission_menu(self):
        """局内菜单按「重新开始」判据识别（本模式菜单和旧 ESC 菜单按钮不同）。"""
        self._check('theatre_esc_menu.png', lambda: self.task.find_one(ESC_RETRY))
        for shot in ('theatre_start.png', 'theatre_fighting.png', 'theatre_result_win.png',
                     'theatre_result_fail.png', 'start_screen_3.png'):
            self._check(shot, lambda: self.task.find_one(ESC_RETRY), expected=False)

    def test_restart_confirm_only_in_the_dialog(self):
        """「重新开始」的二次确认只在弹窗截图上命中，菜单/战斗/结算/阵容都不命中。"""
        self._check('theatre_restart_confirm.png', lambda: self.task.find_one(RESTART_CONFIRM))
        for shot in ('theatre_esc_menu.png', 'theatre_fighting.png', 'theatre_start.png',
                     'theatre_result_win.png', 'theatre_result_fail.png', 'start_screen_3.png'):
            self._check(shot, lambda: self.task.find_one(RESTART_CONFIRM), expected=False)

    def test_restart_clicks_restart_then_confirm(self):
        """走位失败重来：点「重新开始」-> 点二次确认的「确定」-> 局内菜单必须关掉。

        踩过的坑：原来以为「重新开始」没有二次确认，点一下就往下走 —— 弹窗会一直挂着，
        后面的判据全被它盖住。云游戏会丢点击，所以两个都是"点到出结果为止"；
        而且「确定」之后必须确认局内菜单真的关了（菜单还开着时 in_team() 已经是真，
        wait_mission_loaded() 会误判成"重开完成"，走位键全打进菜单里）。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'click_ui_coord', 'send_key', 'wait_mission_loaded',
                     'find_objective_panel', 'log_info')}
        state = {'menu': True, 'dialog': False}
        clicks = []
        try:
            def fake_find_one(name, *args, **kwargs):
                if name == ESC_RETRY:
                    return 'retry' if state['menu'] else None
                if name == RESTART_CONFIRM:
                    return 'ok' if state['dialog'] else None
                return None

            def fake_click(coord, **kwargs):
                clicks.append(coord)
                if coord == COORD.THEATRE_ESC_RETRY:
                    state['dialog'] = True
                elif coord == COORD.THEATRE_RESTART_CONFIRM:
                    state['dialog'] = False
                    state['menu'] = False          # 点确定之后关卡重开，菜单关掉

            task.find_one = fake_find_one
            task.click_ui_coord = fake_click
            task.send_key = lambda *a, **kw: None
            task.wait_mission_loaded = lambda *a, **kw: None
            task.find_objective_panel = lambda: None
            task.log_info = lambda *a, **kw: None

            task.restart_in_mission(time_out=5, load_time_out=5)

            self.assertEqual(clicks, [COORD.THEATRE_ESC_RETRY, COORD.THEATRE_RESTART_CONFIRM],
                             '先点「重新开始」，再点二次确认的「确定」')
            self.assertFalse(state['menu'], '最后局内菜单必须关掉')
            self.assertFalse(state['dialog'], '最后弹窗要关掉')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 走位时间轴：录制的路径不能被改坏 ----

    def test_walk_schedule_matches_recording(self):
        """时间轴来自 `mod\\...\\scripts\\map\\custom\\沉浸式戏剧.json`（总长 4.099 秒）。

        录制里第一条 f12 是录制软件自己的热键，已经丢掉；剩下的按键序列是
        w(1.120) -> 松 -> w(0.111) -> 松 -> d(0.970) -> 松，前面先等 0.996 秒。
        """
        total = sum(wait for wait, _, _ in WALK_SCHEDULE)
        self.assertAlmostEqual(total, 4.099, places=3, msg=f'走位总时长 {total} 和录制对不上')
        self.assertAlmostEqual(WALK_SCHEDULE[0][0], 0.996, places=3, msg='开头要等 0.996 秒')
        self.assertEqual([(key, down) for _, key, down in WALK_SCHEDULE],
                         [('w', True), ('w', False), ('w', True), ('w', False),
                          ('d', True), ('d', False)])
        self.assertNotIn('f12', [key for _, key, _ in WALK_SCHEDULE], 'f12 是录制软件热键，不该走位')

    def test_play_walk_holds_lalt_and_releases_everything(self):
        """走位期间按住 lalt 锁视角；结束时（含中途被打断）每个键都要松开。

        踩过的隐患：走位中途抛 TaskDisabledException（玩家停任务）时如果没在 finally
        里松键，w/d 会一直按着，角色会一直往前跑。
        """
        task = self.task
        original = {name: getattr(task, name) for name in ('sleep', 'send_key_down', 'send_key_up')}
        events = []
        try:
            task.sleep = lambda seconds: events.append('sleep')
            task.send_key_down = lambda key: events.append('down ' + key)
            task.send_key_up = lambda key: events.append('up ' + key)
            task.play_walk()
            self.assertEqual(events[0], 'down lalt', '走位一开始就要按住 lalt')
            self.assertEqual(events.count('sleep'), len(WALK_SCHEDULE), '每一段都要按时间轴等')
            keys = [event for event in events if event != 'sleep']
            self.assertEqual(keys[1:], ['down w', 'up w', 'down w', 'up w',
                                        'down d', 'up d', 'up w', 'up a', 'up s', 'up d',
                                        'up lalt'])
            for key in WALK_RELEASE_KEYS + WALK_HOLD_KEYS:
                self.assertIn('up ' + key, events, f'{key} 走完必须松开')

            def boom(seconds):
                raise TaskDisabledException()

            events.clear()
            task.sleep = boom
            with self.assertRaises(TaskDisabledException):
                task.play_walk()
            for key in WALK_RELEASE_KEYS + WALK_HOLD_KEYS:
                self.assertIn('up ' + key, events, f'走位被打断时 {key} 也必须松开')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 重试计数：配置 N = 允许重试 N 次，第 N+1 次连续失败报错 ----

    def test_interact_retries_stop_after_n_plus_one(self):
        """走位/开机关连续失败：配置 3 -> 重试 3 次，第 4 次失败报错；中间成功清零。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'walk_and_interact_once', 'restart_in_mission')}
        restarts = []
        try:
            task.config = {'开机关重试次数': 3}
            task.walk_and_interact_once = lambda: False
            task.restart_in_mission = lambda: restarts.append('restart')
            with self.assertRaises(Exception) as caught:
                task.walk_and_interact()
            self.assertIn('4', str(caught.exception), '第 4 次连续失败才报错')
            self.assertEqual(restarts.count('restart'), 3, '配置 3 就是允许重试 3 次')
            self.assertEqual(task.interact_failures, 4)

            # 中间成功一次：计数清零，不再报错
            task.interact_failures = 2
            restarts.clear()
            results = [False, True]
            task.walk_and_interact_once = lambda: results.pop(0)
            task.walk_and_interact()
            self.assertEqual(task.interact_failures, 0)
            self.assertEqual(restarts.count('restart'), 1)
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_result_retries_stop_after_n_plus_one(self):
        """结算连续失败：配置 3 -> 点 3 次「再次挑战」，第 4 次失败报错。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result', 'mission_started')}
        clicks = []
        try:
            task.config = {'结算失败重试次数': 3, '打几层': 0}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_FAIL else None
            task.click_ui_coord = lambda coord, **kw: clicks.append(coord)
            task.wait_left_result = lambda *a, **kw: None
            for attempt in (1, 2, 3):
                self.assertFalse(task.handle_result(), '还没到上限不该结束任务')
            self.assertEqual(clicks, [COORD.THEATRE_RESULT_RETRY] * 3, '失败时点「再次挑战」')
            with self.assertRaises(Exception) as caught:
                task.handle_result()
            self.assertIn('4', str(caught.exception), '第 4 次连续失败才报错')
            self.assertEqual(len(clicks), 3, '报错那一次不该再点按钮')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_result_win_resets_failure_counter_and_counts_floors(self):
        """成功点「前往」算一层，并且把结算连续失败计数清零。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result', 'mission_started')}
        clicks = []
        try:
            task.config = {'结算失败重试次数': 3, '打几层': 0}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_WIN else None
            task.click_ui_coord = lambda coord, **kw: clicks.append(coord)
            task.wait_left_result = lambda *a, **kw: None
            task.current_floor = 0
            task.result_failures = 2
            self.assertFalse(task.handle_result())
            self.assertEqual(task.current_floor, 1)
            self.assertEqual(task.result_failures, 0, '点过「前往」就该清零')
            self.assertEqual(clicks, [COORD.THEATRE_RESULT_WIN])
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_floor_limit_stops_the_task(self):
        """「打几层」= 2：打完第 2 层就正常结束（停在结算页，不再点「前往」）。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'find_one', 'click_ui_coord', 'wait_left_result', 'mission_started')}
        clicks = []
        try:
            task.config = {'结算失败重试次数': 3, '打几层': 2}
            task.find_one = lambda name, *a, **kw: 'box' if name == RESULT_WIN else None
            task.click_ui_coord = lambda coord, **kw: clicks.append(coord)
            task.wait_left_result = lambda *a, **kw: None
            task.current_floor = 0
            self.assertFalse(task.handle_result(), '第 1 层还不该结束')
            self.assertTrue(task.handle_result(), '第 2 层打满就该结束')
            self.assertEqual(clicks, [COORD.THEATRE_RESULT_WIN], '打满之后不该再点「前往」')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_unlimited_floors_when_config_is_zero(self):
        task = self.task
        original = task.config
        try:
            task.config = {'开机关重试次数': 3}
            self.assertEqual(task.retry_limit('开机关重试次数', 3), 3)
            task.config = {'打几层': 0}
            self.assertEqual(task.target_floor(), 0, '0 = 无限循环')
            task.config = {'打几层': '5'}
            self.assertEqual(task.target_floor(), 5, '配置控件给字符串也要能读')
            task.config = {'打几层': 'x'}
            self.assertEqual(task.target_floor(), 0, '读不出来就当无限')
            task.config = {'开机关重试次数': 'x'}
            self.assertEqual(task.retry_limit('开机关重试次数', 3), 3, '读不出来就用默认值')
        finally:
            task.config = original

    # ---- 启动位置不对直接报错 ----

    def test_start_requires_known_screen(self):
        """停在游戏主界面/菜单里启动 -> 直接报错，不乱点。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('init_all', 'find_one', 'in_theatre_mission')}
        try:
            task.init_all = lambda: None
            task.find_one = lambda *a, **kw: None
            task.in_theatre_mission = lambda: False
            with self.assertRaises(Exception) as caught:
                task.do_run()
            self.assertIn('阵容页', str(caught.exception))
        finally:
            for name, value in original.items():
                setattr(task, name, value)


    # ---- 一层一次的技能计时器重置 / 挂机期间画面丢失的处理 ----

    def test_skill_tick_resets_every_level(self):
        """每进一层都要重新武装技能计时器（`skill_tick.reset()`），同一层内只重置一次。

        踩过的坑：`create_ticker` 的 `last_time` 初值 0 让第一次 tick 必触发，之后要等
        「释放频率 × 0.8~1.2」才再触发；`reset()` 才是把 `last_time` 置 -1（下一次立刻触发）。
        不重置的话，像「终结技 600 秒」这种长频率技能只会在第一层放一次，后面每一层都在
        等上一次的剩余间隔 —— 表现就是"第二层进去、已经开战、一个技能都不放"。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'wait_mission_loaded', 'walk_and_interact', 'sleep',
                     'fight_until_result', 'skill_tick', 'mission_started')}
        resets = []

        def fake_tick():
            pass

        fake_tick.reset = lambda: resets.append(1)
        try:
            task.find_one = lambda *a, **kw: None
            task.wait_mission_loaded = lambda *a, **kw: None
            task.walk_and_interact = lambda: None
            task.sleep = lambda seconds: None
            task.fight_until_result = lambda: None
            task.skill_tick = fake_tick
            for _ in range(3):                      # 连进三层
                task.mission_started = False
                task.handle_in_mission()
            self.assertEqual(len(resets), 3, '每层都要重新武装一次技能计时器')

            task.mission_started = True             # 同一层里再进一次
            task.handle_in_mission()
            self.assertEqual(len(resets), 3, '同一层内不该重复重置（否则技能会被反复插队）')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_walk_starts_one_second_after_the_level_is_loaded(self):
        """新关卡第 1 层：判据出来之后先稳 1 秒再走位。

        判据刚出现时角色还在落地/过场收尾，这时候按走位键会被吃掉前面一段 —— 表现就是
        "走位距离变短、走不到机关"，然后连续 4 次失败报错停止。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'wait_mission_loaded', 'walk_and_interact', 'sleep',
                     'fight_until_result', 'skill_tick', 'mission_started', 'log_info')}
        events = []

        def fake_tick():
            pass

        fake_tick.reset = lambda: None
        try:
            task.find_one = lambda *a, **kw: None
            task.wait_mission_loaded = lambda *a, **kw: events.append('loaded')
            task.sleep = lambda seconds: events.append(('sleep', seconds))
            task.walk_and_interact = lambda: events.append('walk')
            task.fight_until_result = lambda: None
            task.skill_tick = fake_tick
            task.log_info = lambda *a, **kw: None
            task.mission_started = False
            task.handle_in_mission()
            self.assertEqual(events, ['loaded', ('sleep', theatre_module.FIRST_LAYER_SETTLE), 'walk'],
                             '加载完 -> 稳 1 秒 -> 才开始走位')
            self.assertEqual(theatre_module.FIRST_LAYER_SETTLE, 1)
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 挂机：什么时候算结束、什么时候算没进战斗 ----

    def _fight_case(self, in_combat_seq, exit_at, seconds_per_poll):
        """跑一遍 fight_until_result，返回（返回值, 技能次数, 日志, 重开次数）。

        in_combat_seq 按轮次喂给 is_in_combat()，超出部分沿用最后一个值；
        第 exit_at 轮 find_one(RESULT_WIN) 命中（结算页出现），时钟每轮前进 seconds_per_poll 秒。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'is_in_combat', 'skill_tick', 'log_info', 'sleep',
                     'read_stage_text', 'restart_in_mission',
                     'no_combat_failures')}
        original_time = theatre_module.time
        seq = list(in_combat_seq)
        logs, skills, restarts = [], [], []
        win = {'n': 0}
        clock = {'now': 0.0}

        def fake_find_one(name, *args, **kwargs):
            if name == RESULT_WIN:
                win['n'] += 1
                return 'result' if win['n'] >= exit_at else None
            return None

        def fake_now():
            clock['now'] += seconds_per_poll
            return clock['now']

        try:
            task.find_one = fake_find_one
            task.is_in_combat = lambda: seq.pop(0) if seq else False
            task.skill_tick = lambda: skills.append(1)
            task.log_info = lambda message, *args, **kwargs: logs.append(message)
            task.sleep = lambda seconds: None
            task.read_stage_text = lambda: None
            task.restart_in_mission = lambda *args, **kwargs: restarts.append(1)
            task.no_combat_failures = 0
            theatre_module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})
            return task.fight_until_result(), skills, logs, restarts
        finally:
            theatre_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    def test_fight_returns_true_on_result_screen(self):
        """出现结算页 = 这一局打完：返回 True（交给主循环去点「前往」）。"""
        result, skills, logs, restarts = self._fight_case([True, True, True], exit_at=3,
                                                         seconds_per_poll=0.5)
        self.assertTrue(result)
        self.assertEqual(len(skills), 2, '结算页出现之前一直在放技能')
        self.assertEqual(logs, [])
        self.assertEqual(restarts, [])

    def test_fight_never_pauses_when_the_diamond_blinks(self):
        """进战斗后一律算战斗：红菱形闪了也照常放技能，也不打任何日志。"""
        result, skills, logs, restarts = self._fight_case([False, True, True], exit_at=3,
                                                         seconds_per_poll=0.5)
        self.assertTrue(result)
        self.assertEqual(len(skills), 2, '闪一下的那一轮也必须放技能')
        self.assertEqual(logs, [], '挂机期间不该打日志')
        self.assertEqual(restarts, [], '闪一下不算"没进战斗"')

    def test_fight_keeps_firing_without_red_until_timeout(self):
        """红菱形不在也只管放技能，没到超时上限就不重开、不刷日志。"""
        result, skills, logs, restarts = self._fight_case([False, False, False, True, True],
                                                         exit_at=5, seconds_per_poll=2.0)
        self.assertTrue(result)
        self.assertEqual(len(skills), 4, '每一轮都要放技能')
        self.assertEqual(logs, [], '没到超时上限就不该打日志')
        self.assertEqual(restarts, [])

    def test_fight_restarts_after_no_combat_timeout(self):
        """红菱形连续消失 NO_COMBAT_TIME_OUT 秒 = 没进战斗：重开一局，不报错。"""
        result, skills, logs, restarts = self._fight_case([False] * 20, exit_at=99,
                                                         seconds_per_poll=5.0)
        self.assertFalse(result, '该重开一局：返回 False，让调用方退回第 1 层')
        self.assertEqual(len(restarts), 1, '只重开一次，剩下的交给外层重走第 1 层')
        self.assertTrue(any(str(theatre_module.NO_COMBAT_TIME_OUT) in message for message in logs),
                        f'日志要写清楚是 {theatre_module.NO_COMBAT_TIME_OUT} 秒没进战斗')

    def test_fight_stops_after_too_many_no_combat_restarts(self):
        """一直开不了战（超过「开机关重试次数」）就报错停止，不能无限重开。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'is_in_combat', 'skill_tick', 'log_info', 'sleep',
                     'read_stage_text', 'restart_in_mission',
                     'no_combat_failures', 'config')}
        original_time = theatre_module.time
        clock = {'now': 0.0}

        def fake_now():
            clock['now'] += 40.0                    # 每次都超过上限
            return clock['now']

        try:
            task.find_one = lambda *args, **kwargs: None
            task.is_in_combat = lambda: False
            task.skill_tick = lambda: None
            task.log_info = lambda *args, **kwargs: None
            task.sleep = lambda seconds: None
            task.read_stage_text = lambda: None
            task.restart_in_mission = lambda *args, **kwargs: None
            task.config = {'开机关重试次数': 2}
            task.no_combat_failures = 2                 # 已经重开过两次
            theatre_module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})
            with self.assertRaises(Exception) as caught:
                task.fight_until_result()
            self.assertIn('开不了战', str(caught.exception))
        finally:
            theatre_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    def test_fight_handles_stage_switch_without_counting(self):
        """关号变了就地处理：按「挂机模式」动一次角色位置，然后接着挂（不数层）。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('find_one', 'is_in_combat', 'skill_tick', 'log_info', 'sleep',
                     'read_stage_text', 'apply_afk_mode',
                     'no_combat_failures')}
        original_time = theatre_module.time
        texts = ['第一试炼', '第二试炼', '第二试炼', '第二试炼']
        clock = {'now': 0.0}
        afk, logs = [], []

        def fake_now():
            clock['now'] += 0.5
            return clock['now']

        try:
            task.is_in_combat = lambda: True
            task.skill_tick = lambda: None
            task.log_info = lambda message, *args, **kwargs: logs.append(message)
            task.sleep = lambda seconds: None
            task.apply_afk_mode = lambda: afk.append(1)
            task.no_combat_failures = 0
            task.reset_stage_detector()
            task.read_stage_text = lambda: texts.pop(0) if texts else None
            # 关号读完后让结算页命中，退出循环
            task.find_one = lambda name, *args, **kwargs: 'result' if not texts else None
            theatre_module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})

            self.assertTrue(task.fight_until_result())
            self.assertEqual(len(afk), 1, '确认切层后按挂机模式处理一次角色位置')
            self.assertTrue(any('检测到切层' in message for message in logs))
        finally:
            theatre_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 切层检测（关号 OCR）----

    def test_stage_text_box_is_the_annotation(self):
        """OCR 用的是 `theatre_stage` 的标注框（只当区域，不做模板匹配），1 秒最多读一次。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('get_box_by_name', 'ocr')}
        original_time = theatre_module.time
        clock = {'now': 0.0}
        seen = []

        def fake_now():
            clock['now'] += 0.1
            return clock['now']

        try:
            task.reset_stage_detector()
            task.get_box_by_name = lambda name: seen.append(name) or 'stage_box'
            task.ocr = lambda box=None, **kw: [SimpleNamespace(name='第一试炼', confidence=0.99)]
            theatre_module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})
            self.assertEqual(task.read_stage_text(), '第一试炼')
            self.assertEqual(seen, ['theatre_stage'], '要按 label 取搜索框')
            self.assertIsNone(task.read_stage_text(), '间隔没到就不该再读（0.1 秒 < 1 秒）')
            clock['now'] += 2.0
            self.assertEqual(task.read_stage_text(), '第一试炼')
        finally:
            theatre_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    def test_stage_text_filters_noise(self):
        """认不出来（菜单/结算页）和低分的噪声读数都算"没读到"，不能当成切层。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('get_box_by_name', 'ocr')}
        original_time = theatre_module.time
        clock = {'now': 0.0}

        def fake_now():
            clock['now'] += 2.0
            return clock['now']

        try:
            task.get_box_by_name = lambda name: 'stage_box'
            theatre_module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})
            for texts in ([],                                                    # 读不出文字
                          [SimpleNamespace(name='-', confidence=0.65)],          # 结算页的噪声
                          [SimpleNamespace(name='试', confidence=0.99)],         # 只读到一个字
                          [SimpleNamespace(name='第一试炼', confidence=0.5)]):    # 分数太低
                task.reset_stage_detector()
                task.ocr = lambda box=None, **kw: texts
                self.assertIsNone(task.read_stage_text(), f'{texts} 不该被当成有效读数')
            task.reset_stage_detector()
            task.ocr = lambda box=None, **kw: [SimpleNamespace(name='第一试炼', confidence=0.9)]
            self.assertEqual(task.read_stage_text(), '第一试炼', '刚够阈值就该认')
        finally:
            theatre_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)

    def test_same_stage_text_ignores_the_unlock_prefix(self):
        """按 F 开战会让关号从「开启第一试炼」变成「第一试炼」：互相包含就算同一关。"""
        task = self.task
        self.assertTrue(task.same_stage_text('开启第一试炼', '第一试炼'))
        self.assertTrue(task.same_stage_text('第一试炼', '开启第一试炼'))
        self.assertTrue(task.same_stage_text('第一试炼', '第一试炼'))
        self.assertFalse(task.same_stage_text('第一试炼', '第二试炼'))
        self.assertFalse(task.same_stage_text('开启第二试炼', '第一试炼'))

    def test_first_stage_never_triggers_a_switch(self):
        """第一层只当基准点：怎么读都不算切层（所以第一层不会执行移动/复位配置）。"""
        task = self.task
        task.reset_stage_detector()
        for text in ('开启第一试炼', '第一试炼', '第一试炼', '第一试炼', '试炼', None):
            self.assertFalse(task.update_stage_text(text), f'{text} 不该触发切层')

    def test_partial_read_does_not_shrink_the_baseline(self):
        """半截读数（只认出「试炼」）不能把基准点缩成后缀，否则后面每次切层都会被吞掉。

        实机踩过的坑：OCR 偶尔只认出「试炼」两个字，基准点被改写成「试炼」之后，
        「第三试炼」「第四试炼」全都包含它 → 一局下来一次切层都没确认到，
        层与层之间的移动/复位全没执行。
        """
        task = self.task
        task.reset_stage_detector()
        task.update_stage_text('第一试炼')
        self.assertFalse(task.update_stage_text('试炼'), '半截读数算同一层')
        self.assertEqual(task.stage_text, '第一试炼', '基准点不能被半截读数缩短')
        self.assertFalse(task.update_stage_text('第三试炼'), '和基准点是不同层，要开始计数')
        self.assertFalse(task.update_stage_text('第三试炼'))
        self.assertTrue(task.update_stage_text('第三试炼'), '连续 3 次就该确认切层')

    def test_unlock_prefix_transition_is_not_a_switch(self):
        """走位态「开启第一试炼」-> 开战态「第一试炼」不该触发切层。"""
        task = self.task
        task.reset_stage_detector()
        self.assertFalse(task.update_stage_text('开启第一试炼'))
        for _ in range(5):
            self.assertFalse(task.update_stage_text('第一试炼'), '开战那一下不是切层')

    def test_switch_needs_three_consecutive_reads(self):
        """文字先变、层后切，中间有半截读数：连续 3 次读到同一个新关号才算切层。"""
        task = self.task
        task.reset_stage_detector()
        task.update_stage_text('第一试炼')
        self.assertFalse(task.update_stage_text('开启第二试炼'))
        self.assertFalse(task.update_stage_text('开启第二试炼'))
        self.assertFalse(task.update_stage_text('第二试炼'), '中间夹一个半截读数要重新数')
        self.assertFalse(task.update_stage_text('第二试炼'))
        self.assertTrue(task.update_stage_text('第二试炼'), '第 3 次连续才确认')
        self.assertFalse(task.update_stage_text('第二试炼'), '确认过后同一个值不再触发')

    def test_switch_pending_resets_when_reading_flips(self):
        """读数来回跳（B/C 交替）永远凑不满连续次数，不该误判切层。"""
        task = self.task
        task.reset_stage_detector()
        task.update_stage_text('第一试炼')
        for text in ('第二试炼', '第三试炼', '第二试炼', '第三试炼', None, '第二试炼'):
            self.assertFalse(task.update_stage_text(text))

    def test_advance_failed_does_not_give_up(self):
        """戏剧里没有「放弃挑战」：自动前进到开战超时只记日志继续挂机，不去点放弃。"""
        task = self.task
        original = {name: getattr(task, name) for name in ('give_up_mission', 'log_info')}
        gave_up = []
        try:
            task.give_up_mission = lambda *a, **kw: gave_up.append(1)
            task.log_info = lambda *a, **kw: None
            self.assertTrue(task.advance_failed(), '返回 True 让调用方继续挂机')
            self.assertEqual(gave_up, [], '戏剧菜单里没有「放弃挑战」')
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    # ---- 挂机相关配置（照搬委托任务的形态）与 apply_afk_mode 分派 ----

    def test_afk_config_shape(self):
        """「随机游走 / 挂机模式 / 开局向前走」原样照搬，切层时复用同一份配置。"""
        config = self.task.default_config
        self.assertIn('随机游走', config)
        self.assertIn('挂机模式', config)
        self.assertIn('开局向前走', config)
        self.assertEqual(self.task.config_type['挂机模式']['options'],
                         ['开局重置角色位置', '开局向前走', '自动前进到开战'])
        self.assertIn('是否在任务中随机移动', self.task.config_description['随机游走'])
        self.assertIn('开局向前走几秒', self.task.config_description['开局向前走'])

    def test_apply_afk_mode_dispatch(self):
        """三种挂机模式各自的动作：复位角色(+防卡墙) / 向前走 N 秒 / 前进到开战。

        复位失败（`reset_and_transport()` 返回 False）要把 False 传出去，
        不能让上层以为开局成功 —— 那时人已经不在队伍界面了。
        """
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'reset_and_transport', 'send_key', 'advance_until_combat')}
        keys = []
        try:
            task.reset_and_transport = lambda: keys.append('reset') or True
            task.send_key = lambda key, **kw: keys.append(f'{key} {kw.get("down_time")}')
            task.advance_until_combat = lambda: keys.append('advance')

            task.config = {'挂机模式': '开局重置角色位置'}
            self.assertTrue(task.apply_afk_mode())
            self.assertEqual(keys, ['reset', 'w 0.5'], '复位角色之后要防卡墙往前走一点')

            keys.clear()
            task.config = {'挂机模式': '开局向前走', '开局向前走': 3}
            self.assertTrue(task.apply_afk_mode())
            self.assertEqual(keys, ['w 3'])

            keys.clear()
            task.config = {'挂机模式': '开局向前走', '开局向前走': 0}
            self.assertTrue(task.apply_afk_mode())
            self.assertEqual(keys, [], '时长 0 就不走')

            keys.clear()
            task.config = {'挂机模式': '自动前进到开战'}
            self.assertFalse(task.apply_afk_mode(), '前进到开战失败要原样把 False 传出去')
            self.assertEqual(keys, ['advance'])
        finally:
            for name, value in original.items():
                setattr(task, name, value)

    def test_move_on_begin_still_runs_only_once(self):
        """开局处理仍然只做一次：抽成 apply_afk_mode 之后不能变成每次进局内都跑。"""
        task = self.task
        original = {name: getattr(task, name) for name in
                    ('config', 'send_key', '_mission_started', 'external_movement')}
        keys = []
        try:
            task.config = {'挂机模式': '开局向前走', '开局向前走': 2}
            task.send_key = lambda key, **kw: keys.append(f'{key} {kw.get("down_time")}')
            task.external_movement = commissions_module._default_movement
            task._mission_started = False
            self.assertTrue(task.move_on_begin())
            self.assertTrue(task.move_on_begin())
            self.assertEqual(keys, ['w 2'], '第二次开局不该再走一遍')
        finally:
            for name, value in original.items():
                setattr(task, name, value)


if __name__ == '__main__':
    unittest.main()
