# 界面判据模板匹配测试
import unittest

from src.config import config
from ok.test.TaskTestCase import TaskTestCase

from src.tasks.CommissionsTask import CommissionsTask
from src.tasks.config.CommissionConfig import LETTER_HANDLE_AUTO_SELECT_FIRST
from src.dna_ui.Defs import COORD, DISCRIMINATORS

IMAGES = 'tests/images/'


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
        """除局内 HUD 外，全部 25 张截图都必须判为**非局内**。

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


if __name__ == '__main__':
    unittest.main()
