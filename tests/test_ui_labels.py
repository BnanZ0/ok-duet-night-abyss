# 界面判据模板匹配测试
import re
import unittest

import src.tasks.CommissionsTask as commissions_module
from src.config import config
from ok.test.TaskTestCase import TaskTestCase

from src.tasks.CommissionsTask import CommissionsTask, _default_movement, normalize_ocr_scale
from src.tasks.config.CommissionConfig import LETTER_HANDLE_AUTO_SELECT_FIRST
from src.dna_ui.Defs import COORD, DISCRIMINATORS, REWARD_COUNT_BOX, REWARD_SELECTED_BOX

IMAGES = 'tests/images/'


def read_reward_counts(case, image):
    """用真实 OCR 读三个奖励的持有数（三个固定区域各跑一次，正则只匹配数字，取第一个）。

    返回每个区域识别到的数字。OCR 在紧框里会把同一个数字重复检测成多个框，
    也可能把「持有数：」和数字切成两段，所以两种形态都按"取第一个数字"来读。
    """
    case.set_image(IMAGES + image)
    task = case.task
    reward_pattern = re.compile(r'[0-9]+')
    scale = max(1.0, 2.0 * 1600 / task.width)
    counts = []
    for index, area in enumerate(REWARD_COUNT_BOX, start=1):
        box = task.box_of_screen_scaled(1600, 900, *area, name='reward_count_%d' % index)
        found = task.ocr(box=box, match=reward_pattern,
                         frame_processor=lambda img: normalize_ocr_scale(img, scale))
        counts.append(int(reward_pattern.search(found[0].name).group()) if found else None)
    return counts


class TestUiLabels(TaskTestCase):
    task_class = CommissionsTask

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

    # ---- 开始界面：开始按钮 ----

    def test_start_btn_explore(self):
        self._check('start_screen_explore_attr.png', self.task.find_start_btn)

    def test_start_btn_survey(self):
        self._check('start_screen_survey.png', self.task.find_start_btn)

    def test_start_btn_defence(self):
        self._check('start_screen_defence.png', self.task.find_start_btn)

    def test_start_btn_hedge(self):
        self._check('start_screen_hedge.png', self.task.find_start_btn)

    def test_start_btn_expel(self):
        self._check('start_screen_expel.png', self.task.find_start_btn)

    def test_start_btn_letter(self):
        self._check('start_screen_letter.png', self.task.find_start_btn)

    # ---- 开始界面：另一套布局（◯ 图标位置不同，图标模板复用）----

    def test_start_btn2_other_layout(self):
        """另一套布局只有第 2 个搜索框命中，第 1 个不该命中。

        余量（离线实测）：框2 在新布局 0.9138、旧布局 0.2005；
        框1 在旧布局 1.0000、新布局 0.1765。两套布局不会互相串味。
        """
        self._check('start_screen_other_layout.png', self.task.find_start_btn2)
        self._check('start_screen_other_layout.png', self.task.find_start_btn, expected=False)

    def test_start_interface_covers_both_layouts(self):
        """两套布局的 `find_start_interface` 都要命中，旧的 6 张一个不能少。"""
        for shot in ('start_screen_other_layout.png', 'start_screen_letter.png',
                     'start_screen_explore_attr.png', 'start_screen_survey.png',
                     'start_screen_defence.png', 'start_screen_hedge.png',
                     'start_screen_expel.png'):
            self._check(shot, self.task.find_start_interface)

    def test_start_btn2_not_on_other_screens(self):
        """第 2 个搜索框只在另一套开始界面上命中，其余 27 张都不能命中。"""
        not_start2 = (
            'start_screen_letter.png', 'start_screen_explore_attr.png', 'start_screen_survey.png',
            'start_screen_defence.png', 'start_screen_hedge.png', 'start_screen_expel.png',
            'manual_select_from_start.png', 'manual_select_after_result.png',
            'manual_select_after_comm.png', 'manual_select_next_round.png',
            'action_dialog_explore.png', 'action_dialog_defence.png', 'action_dialog_letter.png',
            'action_dialog_calamity.png',
            'letter_select_from_start.png', 'letter_select_from_ingame.png',
            'letter_select_after_result.png', 'letter_reward.png',
            'result_explore.png', 'result_defence.png', 'result_expel.png',
            'result_commission.png', 'result_letter.png',
            'reset_confirm.png', 'esc_menu.png', 'settings_other.png',
            'hud_explore_round1.png',
        )
        self.assertEqual(len(not_start2), 27)
        for shot in not_start2:
            self._check(shot, self.task.find_start_btn2, expected=False)

    # ---- 委托手册弹窗 ----

    def test_manual_select_from_start(self):
        self._check('manual_select_from_start.png', self.task.find_manual_select_btn)

    def test_manual_select_after_result(self):
        self._check('manual_select_after_result.png', self.task.find_manual_select_btn)

    def test_manual_select_after_comm(self):
        self._check('manual_select_after_comm.png', self.task.find_manual_select_btn)

    def test_manual_select_next_round(self):
        self._check('manual_select_next_round.png', self.task.find_manual_select_btn)

    # ---- 行动抉择弹窗 ----

    def test_action_dialog_explore(self):
        self._check('action_dialog_explore.png', self.task.find_action_dialog_retreat)
        self._check('action_dialog_explore.png', self.task.find_action_dialog_continue)

    def test_action_dialog_defence(self):
        self._check('action_dialog_defence.png', self.task.find_action_dialog_retreat)
        self._check('action_dialog_defence.png', self.task.find_action_dialog_continue)

    def test_action_dialog_letter(self):
        self._check('action_dialog_letter.png', self.task.find_action_dialog_retreat)
        self._check('action_dialog_letter.png', self.task.find_action_dialog_continue)

    def test_action_dialog_calamity(self):
        """灾厄模式那套行动抉择弹窗（比常规布局上移 59px）也要能认出来。"""
        self._check('action_dialog_calamity.png', self.task.find_action_dialog_continue)
        self._check('action_dialog_calamity.png', self.task.find_action_dialog_continue2)

    def test_action_dialog_continue_layouts_do_not_cross(self):
        """两套「继续挑战」各自只在自己那套界面上命中。"""
        self._check('action_dialog_calamity.png', self.task.find_action_dialog_continue_normal, expected=False)
        self._check('action_dialog_explore.png', self.task.find_action_dialog_continue2, expected=False)

    # ---- 密函选择弹窗 ----

    def test_letter_select_from_start(self):
        self._check('letter_select_from_start.png', self.task.find_letter_interface)

    def test_letter_select_from_ingame(self):
        self._check('letter_select_from_ingame.png', self.task.find_letter_interface)

    def test_letter_select_after_result(self):
        self._check('letter_select_after_result.png', self.task.find_letter_interface)

    # ---- 密函奖励弹窗 ----

    def test_letter_reward(self):
        self._check('letter_reward.png', self.task.find_letter_reward_btn)

    # ---- 密函奖励：选中指示器 ✔ 只在被选中的那个奖励区域里 ----

    def test_reward_selected_only_in_selected_slot(self):
        """`letter_reward.png` 里选中的是第 1 个奖励 -> 只有第 1 个搜索框该命中。

        ✔ 的阈值余量（离线实测）：选中的框 1.0000，另外两个框 0.1728 / 0.1901（阈值 0.9）。
        """
        self.set_image(IMAGES + 'letter_reward.png')
        first = self.task.find_reward_selected(1)
        self.assertIsNotNone(first, '第 1 个奖励搜索框应命中 reward_selected')
        box = self.task.box_of_screen_scaled(1600, 900, *REWARD_SELECTED_BOX[0])
        self.assertTrue(box.x <= first.x <= box.x + box.width
                        and box.y <= first.y <= box.y + box.height,
                        '命中位置 %s 不在第 1 个搜索框 %s 内' % ((first.x, first.y), REWARD_SELECTED_BOX[0]))
        for index in (2, 3):
            self.assertIsNone(self.task.find_reward_selected(index),
                              '未选中的第 %d 个奖励不该命中 ✔' % index)

    def test_reward_selected_boxes_are_disjoint(self):
        """三个奖励搜索框是三个独立区域，✔ 出现在哪个框里就代表选中了哪个。"""
        for left, right in ((0, 1), (0, 2), (1, 2)):
            gap = REWARD_SELECTED_BOX[right][0] - REWARD_SELECTED_BOX[left][2]
            self.assertGreater(gap, 0, '第 %d 个和第 %d 个搜索框重叠（间隔 %d）'
                               % (left + 1, right + 1, gap))

    def test_reward_selected_not_on_other_screens(self):
        """奖励选中指示器只存在于密函奖励界面：其余 26 张截图上三个搜索框都必须不命中。

        余量（离线实测）：非奖励截图上最高只有 0.4188（start_screen_letter）。
        """
        not_reward = (
            'start_screen_expel.png', 'start_screen_letter.png', 'start_screen_defence.png',
            'start_screen_hedge.png', 'start_screen_survey.png', 'start_screen_explore_attr.png',
            'result_explore.png', 'result_defence.png', 'result_expel.png',
            'result_commission.png', 'result_letter.png',
            'manual_select_from_start.png', 'manual_select_after_result.png',
            'manual_select_after_comm.png', 'manual_select_next_round.png',
            'letter_select_from_start.png', 'letter_select_from_ingame.png',
            'letter_select_after_result.png',
            'action_dialog_explore.png', 'action_dialog_defence.png', 'action_dialog_letter.png',
            'action_dialog_calamity.png',
            'reset_confirm.png', 'esc_menu.png', 'settings_other.png',
            'hud_explore_round1.png',
        )
        self.assertEqual(len(not_reward), 26)
        for shot in not_reward:
            self.set_image(IMAGES + shot)
            for index in (1, 2, 3):
                self.assertIsNone(self.task.find_reward_selected(index),
                                  '%s 的第 %d 个奖励搜索框不该命中 ✔' % (shot, index))

    # ---- 密函奖励：三个 OCR 区域各出一个数字 ----

    def test_reward_count_from_fixture(self):
        """三个 OCR 区域各跑一次，每个区域都能读到一个数字，且是画面上的持有数。

        只认数字、取第一个：检测器会把「持有数：」和数字切成两段，也会把同一个数字
        重复检测成两个重叠的框（实机实测区域1 回 ['持有数：8', '8']），要求"恰好 1 个"
        或"多个必须一致"都会误报。
        """
        counts = read_reward_counts(self, 'letter_reward.png')
        self.assertEqual(counts, [22, 36440, 36440])

    def test_reward_count_boxes_are_disjoint(self):
        """三个 OCR 区域是三个独立区域，各自只圈住一张卡的「持有数：N」。"""
        for left, right in ((0, 1), (0, 2), (1, 2)):
            gap = REWARD_COUNT_BOX[right][0] - REWARD_COUNT_BOX[left][2]
            self.assertGreater(gap, 0, '第 %d 个和第 %d 个 OCR 区域重叠（间隔 %d）'
                               % (left + 1, right + 1, gap))

    def test_reward_count_not_on_other_screens(self):
        """三个 OCR 区域只在密函奖励界面有文字，其它 26 张截图上都不该读到数字。"""
        not_reward = (
            'start_screen_expel.png', 'start_screen_letter.png', 'start_screen_defence.png',
            'start_screen_hedge.png', 'start_screen_survey.png', 'start_screen_explore_attr.png',
            'result_explore.png', 'result_defence.png', 'result_expel.png',
            'result_commission.png', 'result_letter.png',
            'manual_select_from_start.png', 'manual_select_after_result.png',
            'manual_select_after_comm.png', 'manual_select_next_round.png',
            'letter_select_from_start.png', 'letter_select_from_ingame.png',
            'letter_select_after_result.png',
            'action_dialog_explore.png', 'action_dialog_defence.png', 'action_dialog_letter.png',
            'action_dialog_calamity.png',
            'reset_confirm.png', 'esc_menu.png', 'settings_other.png',
            'hud_explore_round1.png',
        )
        for shot in not_reward:
            counts = read_reward_counts(self, shot)
            self.assertEqual(counts, [None, None, None],
                             '%s 的 OCR 区域不该读到数字，实际 %s' % (shot, counts))

    # ---- ESC 菜单 ----

    def test_esc_menu(self):
        self._check('esc_menu.png', self.task.find_esc_menu)

    # ---- 重置位置二次确认 ----

    def test_reset_confirm(self):
        self._check('reset_confirm.png', self.task.find_reset_confirm)

    # ---- 结算界面：再次进行 ----

    def test_result_again_explore(self):
        self._check('result_explore.png', self.task.find_result_again_btn)

    def test_result_again_defence(self):
        self._check('result_defence.png', self.task.find_result_again_btn)

    def test_result_again_expel(self):
        self._check('result_expel.png', self.task.find_result_again_btn)

    def test_result_again_commission(self):
        self._check('result_commission.png', self.task.find_result_again_btn)

    def test_result_again_letter(self):
        self._check('result_letter.png', self.task.find_result_again_btn)

    # ---- 局内判定 in_team()：lv_text 或 Q 键图标，只有局内为真 ----

    def test_in_team_on_hud(self):
        self._check('hud_explore_round1.png', self.task.in_team, expected=True)

    def test_in_team_only_in_ingame(self):
        """除局内 HUD 外，全部 26 张截图都必须判为**非局内**。

        两个判据的余量（离线实测）：lv_text 局内 1.0000 / 反例最大 0.2322（阈值 0.8）；
        Q 键图标局内 1.0000 / 反例最大 0.4716（阈值 0.9）。

        为什么这条必须钉死：`in_team()` 一旦误报，任务会把准备界面/结算界面当成局内，
        直接去按 ESC 找局内菜单然后超时；`start_mission()` 也会提前误判为"已进入下一步"。
        """
        not_ingame = (
            # 开始界面（同位置是委托报酬面板，不是 Q 键图标）
            'start_screen_expel.png', 'start_screen_letter.png', 'start_screen_defence.png',
            'start_screen_hedge.png', 'start_screen_survey.png', 'start_screen_explore_attr.png',
            # 结算界面
            'result_explore.png', 'result_defence.png', 'result_expel.png',
            'result_commission.png', 'result_letter.png',
            # 弹窗
            'manual_select_from_start.png', 'manual_select_after_result.png',
            'manual_select_after_comm.png', 'manual_select_next_round.png',
            'letter_select_from_start.png', 'letter_select_from_ingame.png',
            'letter_select_after_result.png', 'letter_reward.png',
            'action_dialog_explore.png', 'action_dialog_defence.png', 'action_dialog_letter.png',
            'action_dialog_calamity.png',
            'reset_confirm.png',
            # 局内菜单 / 设置页（有 HUD 背景但已经不在战斗界面）
            'esc_menu.png', 'settings_other.png',
        )
        for shot in not_ingame:
            self._check(shot, self.task.in_team, expected=False)

    # ---- 开始任务：游戏内自动确认跳过中间弹窗时不能判定失败 ----

    def test_start_mission_accepts_auto_confirm_to_ingame(self):
        """点了「开始」之后中间弹窗被游戏自动确认跳过、直接进局内，也算成功。

        踩过的隐患：start_mission 的成功出口原本只有"看到手册弹窗或密函界面"。
        无尽模式开游戏内自动确认时那两个弹窗会被秒跳，脚本于是在这里反复点开始按钮，
        20 秒后误判「任务无法继续」并停掉任务 —— 而游戏其实已经跑起来了。
        """
        task = self.task
        calls = []

        def not_found(*a, **kw):
            return None

        def in_team_after_click(*a, **kw):
            # 点过按钮之后就已经在局内（游戏自动确认跳过了中间弹窗）
            return len(calls) >= 1

        def click(coord, **kw):
            calls.append(coord)
            # 封顶：没有 in_team() 出口时会反复点，这里拦住以免测试跑满整个超时
            if len(calls) > 20:
                raise AssertionError('start_mission 反复点击开始按钮，说明 in_team() 出口失效')

        original = (task.find_start_btn, task.find_result_again_btn,
                    task.find_manual_select_btn, task.find_letter_interface,
                    task.in_team, task.click_ui_coord)
        task.find_start_btn = lambda *a, **kw: 'start_btn'
        task.find_result_again_btn = not_found
        task.find_manual_select_btn = not_found
        task.find_letter_interface = not_found
        task.in_team = in_team_after_click
        task.click_ui_coord = click
        try:
            task.start_mission(timeout=5)          # 不应抛异常
        finally:
            (task.find_start_btn, task.find_result_again_btn,
             task.find_manual_select_btn, task.find_letter_interface,
             task.in_team, task.click_ui_coord) = original
        self.assertEqual(calls, [COORD.START_SCREEN_BTN],
                         '只应点一次开始按钮，不该反复点，实际: %s' % (calls,))

    # ---- 自动选择密函：走的是不依赖检测的固定区域 + 固定坐标 ----

    def test_choose_letter_auto_select_clicks_slot_once(self):
        """「自动选择第一个」分支必须真的点到第一个密函格和确认按钮。

        这个分支平时跑不到（默认配置是「直接开始」），踩过两个坑：
        调用了一个已被删除的点击方法（AttributeError，无人发现）；
        以及把点击框写成了 ⊘「不使用」那格的位置，等于主动选择"不用密函"。
        """
        # 先钉死"被调用的方法真的存在"——第一个坑就是漏了这一层
        for method in ('click_ui_area', 'click_ui_coord', 'click_box_random', 'screen_box'):
            self.assertTrue(callable(getattr(self.task, method, None)),
                            'CommissionsTask 缺少 %s' % method)
        # 第二个坑：点击框必须在 ⊘ 判据的**右边**，不能压在它身上
        not_use = DISCRIMINATORS['letter_select_not_use'][0]
        self.assertGreater(COORD.LETTER_FIRST[0], not_use[2],
                           'LETTER_FIRST %s 不在 ⊘ 判据 %s 右侧' % (COORD.LETTER_FIRST, not_use))
        task = self.task
        original = (type(task).commission_config, task.click_ui_area, task.click_ui_coord,
                    task.find_letter_interface)
        clicks = []
        type(task).commission_config = {'自动处理密函': LETTER_HANDLE_AUTO_SELECT_FIRST}
        task.mission_status = None
        task.click_ui_area = lambda area, **kw: clicks.append(('area', area))
        task.click_ui_coord = lambda coord, **kw: clicks.append(('coord', coord))
        task.find_letter_interface = lambda *a, **kw: len(clicks) < 2
        try:
            task.choose_letter(timeout=2)
        finally:
            (type(task).commission_config, task.click_ui_area, task.click_ui_coord,
             task.find_letter_interface) = original
        self.assertEqual([c[0] for c in clicks], ['area', 'coord'],
                         '应点一次密函格、再点一次确认，实际: %s' % (clicks,))
        self.assertEqual(clicks[0][1], COORD.LETTER_FIRST)
        self.assertEqual(clicks[1][1], COORD.LETTER_CONFIRM, '局外布局应点局外确认坐标')

    # ---- 对照：不该命中的场景 ----

    def test_hud_is_not_start_or_result(self):
        self._check('hud_explore_round1.png', self.task.find_start_btn, expected=False)
        self._check('hud_explore_round1.png', self.task.find_result_again_btn, expected=False)

    def test_letter_select_is_not_manual_select(self):
        self._check('letter_select_from_start.png', self.task.find_manual_select_btn, expected=False)

    def test_manual_select_is_not_letter_select(self):
        self._check('manual_select_from_start.png', self.task.find_letter_interface, expected=False)

    def test_esc_menu_is_not_settings_other(self):
        self._check('esc_menu.png', self.task.find_reset_confirm, expected=False)

    def test_settings_other_is_not_reset_confirm(self):
        self._check('settings_other.png', self.task.find_reset_confirm, expected=False)

    # ---- 开局处理（挂机模式）：每次进局内一次，且被录制走位驱动时整段跳过 ----

    def test_move_on_begin(self):
        """钉死开局处理的四套判据。

        1) 默认配置「开局重置角色位置」-> 调一次复位并补 0.5s 的 w 防卡墙
        2) 「开局向前走 N 秒」-> 只按一次 w，时长就是配置值
        3) 「自动前进到开战」-> 按住 w 前进到 is_in_combat() 为真为止，命中后还要
           再走 AUTO_ADVANCE_EXTRA_TIME 秒才松手；一直不进战斗就走满
           AUTO_ADVANCE_TIME_OUT 秒并放弃重开，返回 False 让调用方跳过局内逻辑
        4) 被注入录制走位（`external_movement` 换掉）-> 整段跳过。
           这条是"全自动执行逻辑完全不受影响"的保证：此时起点由录制路线决定，
           开局前进 / 复位传送会把路线起点带偏。
        """
        task = self.task
        names = ('config', 'external_movement', 'reset_and_transport', 'send_key',
                 'send_key_down', 'send_key_up', 'give_up_mission', 'next_frame', 'is_in_combat')
        original = {name: getattr(task, name) for name in names}
        original_time = commissions_module.time
        clock = {'now': 0.0}

        def fake_time():
            # 每次调用前进 1 秒：前进循环跑满 AUTO_ADVANCE_TIME_OUT 次就自然超时
            clock['now'] += 1.0
            return clock['now']

        def run_case(挂机模式, config=0.0, external=False, started=False, combat_at=1):
            calls = []
            task.config = {'挂机模式': 挂机模式, '开局向前走': config}
            # 注入录制走位时 config 走的是合并缓存，这里直接给同一份配置；
            # move_on_begin 只看 external_movement，不看 config 从哪来
            task.external_movement = object() if external else _default_movement
            task._mission_started = started
            task.reset_and_transport = lambda: calls.append('reset') or True
            task.send_key = lambda key, down_time=0: calls.append('w(%s)' % down_time)
            task.send_key_down = lambda key: calls.append('w down')
            task.send_key_up = lambda key: calls.append('w up')
            task.give_up_mission = lambda: calls.append('give_up')
            task.next_frame = lambda: calls.append('frame')
            probes = []

            def is_in_combat():
                probes.append(1)
                hit = len(probes) >= combat_at
                if hit:
                    calls.append('combat')
                return hit

            task.is_in_combat = is_in_combat
            result = task.move_on_begin()
            return calls, result

        def movement(events):
            """只看按键/放弃这类动作，忽略取帧和战斗判据探测。"""
            return [event for event in events if event not in ('frame', 'combat')]

        fake_time_module = type('FakeTime', (), {'time': staticmethod(fake_time)})
        try:
            commissions_module.time = fake_time_module
            self.assertEqual(run_case('开局重置角色位置', 0),
                             (['reset', 'w(0.5)'], True), '复位模式应复位并补 0.5s 防卡墙')
            self.assertEqual(run_case('开局向前走', 2.5), (['w(2.5)'], True),
                             '向前走模式应只按一次 w')
            self.assertEqual(run_case('开局向前走', 0), ([], True), '向前走 0 秒应什么都不做')

            events, result = run_case('自动前进到开战', combat_at=3)
            self.assertEqual(movement(events), ['w down', 'w up'], '前进到进入战斗就停，不该放弃')
            self.assertTrue(result)
            # 命中判据后还要继续走一段才松手（再多取一帧就是"多走了"的证据）
            hit = events.index('combat')
            self.assertEqual(events[hit + 1], 'frame', '进入战斗后应继续前进一小段')
            self.assertEqual(events[-1], 'w up', '不管成功失败都要松开 w')

            events, result = run_case('自动前进到开战', combat_at=9999)
            self.assertEqual(movement(events), ['w down', 'give_up', 'w up'],
                             '一直不进战斗就该走满超时并放弃重开')
            self.assertNotIn('combat', events, '走满超时说明判据一次都没命中')
            self.assertFalse(result, '放弃重开后调用方不该继续跑局内逻辑')

            self.assertEqual(run_case('开局重置角色位置', 0, external=True), ([], True),
                             '被注入录制走位时不该做任何开局处理')
            self.assertEqual(run_case('开局重置角色位置', 0, started=True), ([], True),
                             '同一次进局内只处理一次')
        finally:
            commissions_module.time = original_time
            for name, value in original.items():
                setattr(task, name, value)


if __name__ == '__main__':
    unittest.main()
