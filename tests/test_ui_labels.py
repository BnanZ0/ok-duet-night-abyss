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

    # ---- 局内判定 in_team()：lv_text 或 Q 键图标 ----

    def test_in_team_on_hud(self):
        self._check('hud_explore_round1.png', self.task.in_team)

    def test_in_team_not_on_start_screen(self):
        """开始界面同位置是委托报酬面板，不能判成局内（不然会去按 ESC 找局内菜单）。"""
        for shot in ('start_screen_expel.png', 'start_screen_letter.png', 'start_screen_defence.png',
                     'start_screen_hedge.png', 'start_screen_survey.png', 'start_screen_explore_attr.png'):
            self._check(shot, self.task.in_team, expected=False)

    def test_in_team_not_on_result(self):
        for shot in ('result_expel.png', 'result_explore.png'):
            self._check(shot, self.task.in_team, expected=False)

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
