import re
import time
import numpy as np
import cv2
from enum import Enum
from functools import cached_property

from ok import TaskDisabledException
from src.tasks.BaseDNATask import BaseDNATask, isolate_white_text_to_black, color_filter
from src.dna_ui.Defs import (Ui, COORD, REF_WIDTH, REF_HEIGHT,
                             REWARD_COUNT_BOX, REWARD_SELECTED_BOX)
from src.tasks.config.CommissionConfig import (
    CommissionConfig,
    LETTER_HANDLE_AUTO_SELECT_FIRST,
    LETTER_HANDLE_START_DIRECTLY,
    LETTER_HANDLE_WAIT_USER,
    LETTER_HANDLE_MODES,
    LETTER_REWARD_DEFAULT,
    LETTER_REWARD_COUNT_ZERO,
    LETTER_REWARD_COUNT_MIN,
    LETTER_REWARD_COUNT_MAX,
    LETTER_REWARD_WAIT_USER,
)
from src.tasks.config.CommissionSkillConfig import CommissionSkillConfig

# 「自动前进到开战」的最长时间（秒）：走这么久还没进战斗就放弃重开
AUTO_ADVANCE_TIME_OUT = 20
# 检测到进入战斗后仍继续前进的秒数：战斗判据出现得比"走进交战区"早一点
AUTO_ADVANCE_EXTRA_TIME = 2


class Mission(Enum):
    START = 1
    CONTINUE = 2
    STOP = 3
    GIVE_UP = 4


class CommissionsTask(BaseDNATask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_round = 0
        self.current_wave = -1
        self.mission_status = None
        self.action_timeout = 15
        self.wave_future = None
        # 有没有被注入录制走位（`move_on_begin` 要判断它）。半自动任务会覆盖这个值，
        # 自动驱离没有录制机制，保留这里的默认空实现。
        self.external_movement = _default_movement

    @cached_property
    def commission_config(self):
        return self.get_task_by_class(CommissionConfig).config
    
    @cached_property
    def commission_skill_config(self):
        return self.get_task_by_class(CommissionSkillConfig).config

    def get_letter_handle_mode(self):
        mode = self.commission_config.get("自动处理密函", LETTER_HANDLE_AUTO_SELECT_FIRST)
        if mode in LETTER_HANDLE_MODES:
            return mode
        return LETTER_HANDLE_AUTO_SELECT_FIRST

    def setup_commission_config(self):
        self.default_config.update({
            "轮次": 5,
            "超时时间": 90,
        })
        self.config_description.update({
            "轮次": "打几个轮次",
            "超时时间": "超时后将重启任务",
        })

    def setup_mission_start_config(self):
        """开局挂机配置。定义只有这一份，手动半自动任务和自动驱离共用。"""
        self._mission_started = False
        self.default_config.update({
            "随机游走": False,
            "挂机模式": "开局重置角色位置",
            "开局向前走": 0.0,
        })
        self.config_description.update({
            "随机游走": "是否在任务中随机移动",
            "开局向前走": "开局向前走几秒",
        })
        self.config_type["挂机模式"] = {
            "type": "drop_down",
            "options": ["开局重置角色位置", "开局向前走", "自动前进到开战"],
        }

    def is_in_combat(self):
        """进入战斗的判据：任务信息栏出现波次「x/y」。

        子任务有更贴合的信号（血清、血条）时各自覆盖。
        """
        self.get_wave_info()
        return self.current_wave != -1

    def advance_until_combat(self):
        """按住 W 一直前进到进入战斗为止，再往前多走一小段，超时就用 ESC 菜单放弃并重开。

        目标点就在正前方、只有距离不定的副本用这个模式，不用配时长。战斗判据出现时
        人往往还差一点才走进交战区，所以判据成立后再走 AUTO_ADVANCE_EXTRA_TIME 秒。
        超时走 `advance_failed()`：默认放弃并重开（而不是只开 ESC 菜单 —— 菜单开着时
        in_team() 仍为真，主循环的 handle_mission_interface 会直接 return，菜单永远没人点）。
        """
        self.send_key_down("w")
        try:
            deadline = time.time() + AUTO_ADVANCE_TIME_OUT
            while time.time() < deadline:
                self.next_frame()
                if self.is_in_combat():
                    self.log_info(f"已进入战斗，再前进 {AUTO_ADVANCE_EXTRA_TIME} 秒")
                    # 多走这一段时继续取帧，松手时手里的画面是新的
                    extra_deadline = time.time() + AUTO_ADVANCE_EXTRA_TIME
                    while time.time() < extra_deadline:
                        self.next_frame()
                    return True
            return self.advance_failed()
        finally:
            self.send_key_up("w")

    def advance_failed(self):
        """「自动前进到开战」走满 AUTO_ADVANCE_TIME_OUT 秒还没进战斗。

        默认按委托的处理：放弃这次副本（返回 False）。
        没有「放弃挑战」按钮的模式（沉浸式戏剧）自己覆盖这个方法。
        """
        self.log_info(f"前进 {AUTO_ADVANCE_TIME_OUT} 秒仍未进入战斗，重开任务")
        self.give_up_mission()
        return False

    def move_on_begin(self):
        """开局处理：复位角色位置 / 向前走几秒 / 前进到进入战斗。每次进局内只做一次。

        返回 False 表示这次没能开局成功（已经放弃并退出副本），调用方不要继续
        跑局内逻辑。被全自动任务注入录制走位时整段跳过 —— 那时起点由录制路线
        决定，开局前进会把路线的起点带偏。
        """
        if self._mission_started or self.external_movement is not _default_movement:
            return True
        self._mission_started = True
        return self.apply_afk_mode()

    def apply_afk_mode(self):
        """按「挂机模式」配置处理角色当前的位置：复位角色 / 向前走几秒 / 前进到开战。

        原本只是 `move_on_begin()` 的开局处理，抽出来是因为沉浸式戏剧要在"层间切换"时再跑
        一次同样的处理 —— 那边由任务自己调用，不走 `move_on_begin` 的一次性开关。
        """
        mode = self.config.get("挂机模式")
        if mode == "开局重置角色位置":
            if not self.reset_and_transport():
                # 复位失败时人已经不在队伍界面了，别让上层以为开局成功
                return False
            # 防卡墙
            self.send_key("w", down_time=0.5)
        elif mode == "开局向前走":
            if (walk_sec := self.config.get("开局向前走", 0)) > 0:
                self.send_key("w", down_time=walk_sec)
        elif mode == "自动前进到开战":
            return self.advance_until_combat()
        return True

    # ------------------------------------------------------------------
    # 界面判据（唯一出处 src/ui/Defs.py）
    #   命名规则：find_<界面>_<元素>；判据命中 == 当前在这个界面上
    # ------------------------------------------------------------------
    def find_action_dialog_retreat(self, threshold=0):
        """行动抉择弹窗的「撤离」（原 find_ingame_quit_btn）。"""
        return self.find_ui(Ui.ACTION_DIALOG_RETREAT, threshold=threshold)

    def find_action_dialog_continue(self, threshold=0):
        """行动抉择弹窗的「继续挑战」（原 find_ingame_continue_btn）。"""
        return self.find_ui(Ui.ACTION_DIALOG_CONTINUE, threshold=threshold)

    def find_start_btn(self, threshold=0, box=None, template=None):
        """开始界面的「开始」按钮（新版只有一个位置，不再分 bottom/big）。"""
        return self.find_ui(Ui.START_SCREEN_START, threshold=threshold, box=box, template=template)

    def find_start_btn2(self, threshold=0):
        """另一套布局的开始界面「开始」按钮（◯ 图标位置不同，图标模板复用）。"""
        return self.find_ui(Ui.START_SCREEN_START_2, threshold=threshold)

    def find_start_interface(self, threshold=0):
        """开始界面 —— 两套布局任意一套命中都算。"""
        return self.find_start_btn(threshold=threshold) or self.find_start_btn2(threshold=threshold)

    def find_manual_select_btn(self, threshold=0):
        """委托手册弹窗（用 ⊘ 不使用当判据）。"""
        return self.find_ui(Ui.MANUAL_SELECT_NOT_USE, threshold=threshold)

    def find_letter_select_not_use(self, threshold=0):
        """密函选择弹窗的通用判据：卡牌矩阵第 1 格的 ⊘ 不使用图标。

        两套布局（局外/局内）里这个图标位置完全相同 -> 用来稳定回答
        "我现在是不是在密函选择界面"，不区分布局。
        """
        return self.find_ui(Ui.LETTER_SELECT_NOT_USE, threshold=threshold)

    def find_letter_reward_btn(self, threshold=0):
        """密函奖励弹窗。"""
        return self.find_ui(Ui.LETTER_REWARD_CONFIRM, threshold=threshold)

    def find_reward_selected(self, index, threshold=0.9):
        """第 index 个奖励是否已选中 —— 在它的底栏区域里找 ✔。

        选中哪个哪个才画 ✔，所以命中就代表"这个奖励选上了"，点一次没选上就再点。
        """
        box = self.box_of_screen_scaled(REF_WIDTH, REF_HEIGHT, *REWARD_SELECTED_BOX[index - 1],
                                        name='reward_card_%d' % index)
        return self.find_one('reward_selected', threshold=threshold, box=box)

    def find_esc_menu(self, threshold=0):
        """局内 ESC 菜单（用「设置」齿轮当判据）。"""
        return self.find_ui(Ui.ESC_MENU_SETTINGS, threshold=threshold)

    def find_reset_confirm(self, threshold=0):
        """屏幕中央确认弹窗的「确定」（用按钮左侧的金圈当判据）。

        只在需要"弹窗出现/消失"驱动的步骤里用（复位并传送、放弃挑战的二次确认），
        它不是"我在哪个界面"的判据，所以不参与 handle_mission_interface 的 if/elif 链。
        """
        return self.find_ui(Ui.RESET_CONFIRM_OK, threshold=threshold)

    def find_center_confirm(self, threshold=0):
        """屏幕中央的通用「确定」按钮（金圈）。

        与 find_reset_confirm 是同一个控件、同一个判据 —— 拆成两个名字是为了让调用点
        读起来清楚（这里是"放弃挑战的二次确认"，那里是"重置位置的二次确认"）。
        """
        return self.find_reset_confirm(threshold=threshold)

    def find_result_again_btn(self, threshold=0):
        """任务结算界面的「再次进行」按钮（金色环形图标），5 张结算界面位置一致。"""
        return self.find_ui(Ui.RESULT_AGAIN_BTN, threshold=threshold)


    def open_in_mission_menu(self, time_out=20, raise_if_not_found=True):
        if self.find_esc_menu():
            return True
        found = False
        start = time.time()
        while time.time() - start < time_out:
            self.send_key("esc")
            if self.wait_until(self.find_esc_menu, time_out=2, raise_if_not_found=False):
                found = True
                break
        else:
            if raise_if_not_found:
                raise Exception("未找到任务菜单")
        self.sleep(0.2)
        return found

    def start_mission(self, timeout=0):
        """点「开始 / 再次进行」，然后等进入下一步（手册弹窗或密函弹窗）。

        失败语义：
          * 从没见到按钮就超时 -> 抛普通 Exception（加载慢、云游戏卡顿属这类，可重试）；
          * 点过按钮却一直没进下一步 -> 响铃 + TaskDisabledException，让任务优雅停止。
        别把第一种抛成 TaskDisabledException，那会把瞬时卡顿变成永久停任务。
        """
        action_timeout = self.action_timeout if timeout == 0 else timeout
        box = self.screen_box('REWARD_DRAG_AREA')
        deadline = time.time() + action_timeout
        clicked = False

        while time.time() < deadline:
            if self.find_start_interface():
                self.click_ui_coord(COORD.START_SCREEN_BTN, name="start_mission",
                                    after_sleep=0.2, use_safe_move=True, safe_move_box=box)
                clicked = True
            elif self.find_result_again_btn():
                self.click_ui_coord(COORD.RESULT_AGAIN, name="start_mission_again",
                                    after_sleep=0.2, use_safe_move=True, safe_move_box=box)
                clicked = True
            elif self.find_manual_select_btn() or self.find_letter_interface() or self.in_team():
                # in_team() 也算"已进入下一步"：无尽模式可以开游戏内自动确认，
                # 中间的手册/密函弹窗会被系统秒确认跳过，直接进局内
                return              # 已经进入下一步
            else:
                self.next_frame()
                continue

            if self.wait_until(condition=lambda: self.find_manual_select_btn()
                                           or self.find_letter_interface()
                                           or self.in_team(),
                               time_out=2):
                return

        if clicked:
            self.soundBeep()
            self.log_info_notify("任务无法继续")
            raise TaskDisabledException
        raise Exception("等待开始任务超时")

    def quit_mission(self, timeout=0):
        action_timeout = self.action_timeout if timeout == 0 else timeout
        self.wait_until(self.find_action_dialog_retreat, time_out=action_timeout, raise_if_not_found=True)
        self.wait_until(
            condition=lambda: not self.find_action_dialog_retreat(),
            post_action=lambda: self.click_ui_coord(COORD.ACTION_RETREAT, name="quit_mission", after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(1)
        self.wait_until(lambda: not self.in_team(), time_out=action_timeout, raise_if_not_found=True)

    def give_up_mission(self, timeout=0):
        def is_mission_start_iface():
            return self.find_start_interface() or self.find_action_dialog_continue() or self.find_esc_menu()

        action_timeout = self.action_timeout if timeout == 0 else timeout

        if self.open_in_mission_menu(time_out=10, raise_if_not_found=False):
            # ESC 菜单里「放弃挑战」
            self.wait_until(
                condition=lambda: not self.find_esc_menu(),
                post_action=lambda: self.click_ui_coord(COORD.ESC_GIVEUP, name="esc_giveup", after_sleep=0.25),
                time_out=action_timeout,
                raise_if_not_found=True,
            )
            self.sleep(0.5)
            # 「放弃挑战」有二次确认弹窗，点弹出的「确定」直到它消失
            confirmed = {}

            def _click_giveup_confirm():
                confirmed['box'] = self.find_center_confirm(threshold=0.9)
                self._click_detected(confirmed.get('box'), name="giveup_confirm")

            self.wait_until(
                condition=lambda: not self.find_center_confirm(threshold=0.9),
                post_action=_click_giveup_confirm,
                time_out=action_timeout,
                raise_if_not_found=True,
            )
            self.sleep(0.5)

        self.wait_until(condition=is_mission_start_iface, time_out=60, raise_if_not_found=False)

    def continue_mission(self, timeout=0):
        if self.in_team():
            return False
        action_timeout = self.action_timeout if timeout == 0 else timeout
        self.wait_until(
            condition=lambda: not self.find_action_dialog_continue() and not self.find_action_dialog_retreat(),
            post_action=lambda: self.click_ui_coord(COORD.ACTION_CONTINUE, name="continue_mission", after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(0.5)
        return True

    def choose_drop_rate(self, timeout=0):
        """选委托手册：先按配置点格子，再点「开始挑战」/「确认选择」直到弹窗关闭。

        两套布局的确认按钮位置不同：
          * 双按钮版：[Esc] 取消 在左 + [Space] 开始挑战 在右 -> COORD.MANUAL_CONFIRM
          * 单按钮版（局内继续轮次）：只有居中的 [Space] 确认选择 -> COORD.MANUAL_CONFIRM_NEXT
        两套布局的 ⊘ 判据位置相同，光靠判据分不出来，用 mission_status 区分：
        只有"局内继续轮次"这一条路径会把 mission_status 置成 Mission.CONTINUE。
        """
        def click_confirm():
            if not self.find_manual_select_btn():
                return
            single_button = self.mission_status == Mission.CONTINUE
            coord = COORD.MANUAL_CONFIRM_NEXT if single_button else COORD.MANUAL_CONFIRM
            self.click_ui_coord(coord, name="manual_confirm", after_sleep=0.25)

        action_timeout = self.action_timeout if timeout == 0 else timeout
        self.sleep(0.5)
        self.choose_drop_rate_item()
        self.wait_until(
            condition=lambda: not self.find_manual_select_btn(),
            post_action=click_confirm,
            time_out=action_timeout,
            raise_if_not_found=True,
        )

    def choose_drop_rate_item(self):
        if not hasattr(self, "config"):
            return
        drop_rate = self.commission_config.get("委托手册", "不使用")
        if drop_rate == "不使用":
            return
        round_to_use = [int(num) for num in re.findall(r'\d+', self.commission_config.get("委托手册指定轮次", ""))]
        if len(round_to_use) != 0:
            if self.mission_status != Mission.CONTINUE:
                if 1 not in round_to_use:
                    return
            elif self.current_round == 0 or (self.current_round + 1) not in round_to_use:
                return
        coord = COORD.MANUAL_ITEM.get(drop_rate)
        if coord is not None:
            self.click_ui_coord(coord, name="manual_%s" % drop_rate)
        self.log_info(f"使用委托手册: {drop_rate}")
        self.sleep(0.25)

    def choose_letter(self, timeout=0):
        """点「⊘ 不使用」-> 点确认 -> 等密函界面消失。

        1) ⊘ 槽选中后外观不变，所以点一次就往下走，不拿"模板还在不在"当成功凭证。
        2) 确认按钮不做模板匹配（实拍帧上芯片只有 0.76，过不了 0.8 阈值），
           两套布局用 mission_status 区分，点击用 COORD 固定坐标。
        3) 「[Esc] 放弃」不标注、不匹配 —— 它与确认按钮同排相邻，照检测框点就是点放弃。
        """
        if not hasattr(self, "config"):
            return
        action_timeout = self.action_timeout if timeout == 0 else timeout
        mode = self.get_letter_handle_mode()
        if mode == LETTER_HANDLE_WAIT_USER:
            self.log_info_notify("需自行选择密函")
            self.soundBeep()
            self.wait_until(
                lambda: not self.find_letter_interface(),
                time_out=300,
                raise_if_not_found=True,
            )
            return
        if mode in (LETTER_HANDLE_AUTO_SELECT_FIRST, LETTER_HANDLE_START_DIRECTLY) and self.find_letter_interface():
            drag_box = self.screen_box('LETTER_DRAG_AREA')

            if mode == LETTER_HANDLE_AUTO_SELECT_FIRST:
                # 点第 2 格（第一个可选密函）；第 1 格是 ⊘ 不使用，点了等于不用密函
                self.sleep(0.1)
                self.click_ui_area(COORD.LETTER_FIRST, name="letter_first_slot",
                                   after_sleep=0.3, use_safe_move=True, safe_move_box=drag_box)

            # 确认按钮直接点固定坐标：局内继续轮次是 x1108，其余是 x1292
            def click_confirm():
                if self.mission_status == Mission.CONTINUE:
                    coord, name = COORD.LETTER_INGAME_CONFIRM, "letter_confirm_ingame"
                else:
                    coord, name = COORD.LETTER_CONFIRM, "letter_confirm_outgame"
                self.click_ui_coord(coord, name=name, after_sleep=1,
                                    use_safe_move=True, safe_move_box=drag_box)

            # 点是手段，"密函界面消失"才算过
            self.wait_until(
                condition=lambda: not self.find_letter_interface(),
                post_action=click_confirm,
                time_out=action_timeout,
                raise_if_not_found=True,
            )

    def read_reward_counts(self, attempt=3):
        """读三个奖励的持有数，返回 [卡1, 卡2, 卡3]。

        三个奖励各有一个固定的 OCR 区域，**各跑一次**，正则只匹配数字（`[0-9]+`），
        取第一个匹配到的就用。OCR 在紧框里可能把同一个数字重复检测成多个框
        （实测区域1 会回 ['持有数：8', '8']，两框还重叠），或者把「持有数：」和数字
        切成两段，所以不要求"恰好 1 个"，也不比较多个数字是否一致。

        每个区域先经 `normalize_ocr_scale` 归一化字号：1600x900 下单数字只有 16px 高，
        检测器会整个漏掉它（实测只剩「持有数：」）或把它认成别的数字；2K/4K 下本来就够大。
        """
        reward_pattern = re.compile(r'[0-9]+')
        # 1600x900 的字号太小，统一放大到它的 2 倍；高分辨率按比例少放或不放
        scale = max(1.0, 2.0 * REF_WIDTH / self.width)

        def read_once():
            counts = []
            for index, area in enumerate(REWARD_COUNT_BOX, start=1):
                box = self.box_of_screen_scaled(REF_WIDTH, REF_HEIGHT, *area,
                                                name='reward_count_%d' % index)
                self.draw_boxes(box.name, box, 'blue')
                found = self.ocr(box=box, match=reward_pattern,
                                 frame_processor=lambda img: normalize_ocr_scale(img, scale))
                if not found:
                    raise Exception("第 %d 个奖励持有数识别失败，这个区域一个数字都没识别到" % index)
                counts.append(int(reward_pattern.search(found[0].name).group()))
            return counts

        # 进这个界面时卡片还在做淡入/高亮动画，帧不稳定；等动画走完再开始识别。
        self.sleep(1)
        for attempt_index in range(1, attempt + 1):
            try:
                return read_once()
            except Exception as e:
                if attempt_index == attempt:
                    raise
                self.log_info(f"第 {attempt_index} 轮识别奖励持有数失败({e})，1 秒后重试")
                self.sleep(1)

    def choose_target_letter_reward(self):
        counts = self.read_reward_counts()
        strategy = self.commission_config.get("密函奖励偏好")
        self.log_info(f"当前识别到的奖励持有数: {counts}")

        if strategy == LETTER_REWARD_COUNT_ZERO:
            index = next((i for i, count in enumerate(counts, start=1) if count == 0), None)
            if index is None:
                self.log_info("未识别到持有数为0的奖励，使用默认奖励")
                return
        elif strategy == LETTER_REWARD_COUNT_MIN:
            index = counts.index(min(counts)) + 1
        elif strategy == LETTER_REWARD_COUNT_MAX:
            index = counts.index(max(counts)) + 1
        else:
            return

        self.log_info(f"策略[{strategy}] -> 选择第 {index} 个奖励，持有数: {counts[index - 1]}")
        # 点奖励区域本身：实测点卡片中间的图案只会弹出物品详情，不会改变选择
        area = REWARD_COUNT_BOX[index - 1]
        target_box = self.box_of_screen_scaled(REF_WIDTH, REF_HEIGHT, *area,
                                               name='letter_reward_%d' % index)

        # 点了不算成功：✔ 得出现在这一张的底栏才算选中，没出现就再点一次
        self.wait_until(
            condition=lambda: self.find_reward_selected(index) is not None,
            post_action=lambda: self.click_box_random(target_box, down_time=0.02, after_sleep=0.3),
            time_out=10,
            raise_if_not_found=True,
        )

    def choose_letter_reward(self, timeout=0):
        action_timeout = self.action_timeout if timeout == 0 else timeout
        reward_strategy = self.commission_config.get("密函奖励偏好", LETTER_REWARD_DEFAULT)
        if reward_strategy == LETTER_REWARD_WAIT_USER:
            self.log_info_notify("需自行选择密函奖励")
            self.soundBeep()
            self.wait_until(
                lambda: not self.find_letter_reward_btn(),
                time_out=300,
                raise_if_not_found=True,
            )
        else:
            if reward_strategy in (LETTER_REWARD_COUNT_ZERO, LETTER_REWARD_COUNT_MIN, LETTER_REWARD_COUNT_MAX):
                self.choose_target_letter_reward()
            self.wait_until(
                condition=lambda: not self.find_letter_reward_btn(),
                post_action=lambda: self.click_ui_coord(COORD.LETTER_REWARD_CONFIRM,
                                                        name="letter_reward_confirm",
                                                        down_time=0.02, after_sleep=0.25),
                time_out=action_timeout,
                raise_if_not_found=True,
            )
        self.sleep(0.1)
        self.wait_until(lambda: not self.in_team(), time_out=3, settle_time=0.5)

    def create_skill_ticker(self):
        skills = []
        def create_ticker(local_n):
            def action():
                self.log_onetime_info("全局技能设定: " + str(self.commission_skill_config), "全局技能设定")
                skill = self.commission_skill_config.get(f"技能{local_n}", "不使用")
                if skill == "不使用":
                    return
                after_sleep = self.commission_skill_config.get(f"技能{local_n}_释放后等待", 0.0)
                if skill == "战技":
                    self.get_current_char().send_combat_key()
                elif skill == "Ctrl+战技（赛琪专属）":
                    self.get_current_char().send_combat_key_with_ctrl()
                elif skill == "终结技":
                    self.get_current_char().send_ultimate_key()
                elif skill == "自动苏乙终结技":
                    on_result = self.find_one('suyi_q_on')
                    off_result = self.find_one('suyi_q_off')
                    on_conf = on_result.confidence if on_result else 0
                    off_conf = off_result.confidence if off_result else 0
                    if off_conf > on_conf:
                        self.get_current_char().send_ultimate_key()
                    else:
                        self.get_current_char().click()
                elif skill == "魔灵支援":
                    self.get_current_char().send_geniemon_key()
                elif skill == "普攻":
                    self.get_current_char().click()
                elif skill == "重击":
                    self.get_current_char().hold_normal_attack(
                        self.commission_skill_config.get("重击长按时间", 1.5))
                if after_sleep > 10:
                    self.log_onetime_info(f"检测到长延时：释放技能 {local_n} 后将等待 {after_sleep} 秒，可能影响脚本运行，请确认是否符合预期")
                self.sleep(after_sleep)

            return self.create_ticker(
                action, 
                interval=lambda: self.commission_skill_config.get(f"技能{local_n}_释放频率", 5.0), 
                interval_random_range=(0.8, 1.2)
            )
        
        for n in range(1, 5):
            skills.append(create_ticker(n))

        return self.create_ticker_group(skills)

    def get_round_info(self):
        """获取并更新当前轮次信息。"""
        if self.in_team():
            return
        box = self.box_of_screen(0.241, 0.361, 0.259, 0.394, name="green_mark", hcenter=True)
        self.wait_until(lambda: self.calculate_color_percentage(green_mark_color, box) > 0.135, time_out=1)
        round_info_box = self.screen_box('ROUND_INFO_OCR')
        # 加 \d+ 正则兜底：框里可能混进「：」等非数字碎片，
        # 只用 texts[0].name.isdigit() 会在 OCR 先返回碎片时静默失败（退化成 current_round += 1）
        texts = self.ocr(box=round_info_box, frame_processor=ocr_normalize, name="round_info",
                         match=re.compile(r'\d+'))
        # img = ocr_normalize(round_info_box.crop_frame(self.frame))
        # self.screenshot(name=f"round_info_ocr_{texts}", frame=img)

        prev_round = self.current_round
        new_round_from_ocr = None
        if texts and texts[0].name.isdigit():
            new_round_from_ocr = int(texts[0].name)
            self.log_debug(f"get_round_info ocr 轮次 {new_round_from_ocr}")

        if new_round_from_ocr is not None:
            self.current_round = new_round_from_ocr
        elif self.current_round != 0:  # OCR失败，但之前已有轮次记录，则递增
            self.current_round += 1

        if prev_round != self.current_round:
            self.info_set("当前轮次", self.current_round)

    def get_wave_info(self):
        if not self.in_team():
            return
        if self.wave_future and self.wave_future.done():
            texts = self.wave_future.result()
            self.wave_future = None
            if texts and len(texts) >= 1:
                prev_wave = self.current_wave
                if (m := re.match(r"(\d)/\d", texts[0].name)):
                    self.current_wave = int(m.group(1))
                else:
                    return
                if prev_wave != self.current_wave:
                    self.info_set("当前波次", self.current_wave)
            return
        if self.wave_future is None:
            mission_info_box = self.box_of_screen(0.107, 0.343, 0.174, 0.386, name="mission_info", hcenter=True)
            frame = self.frame.copy()
            self.wave_future = self.thread_pool_executor.submit(self.ocr, frame=frame,
                                                                box=mission_info_box,
                                                                frame_processor=isolate_white_text_to_black,
                                                                match=re.compile(r"\d/\d"))

    def reset_wave_info(self):
        if self.wave_future is not None:
            self.wave_future.cancel()
            self.wave_future = None
        self.current_wave = -1
        self.info_set("当前波次", self.current_wave)

    def wait_until_get_wave_info(self):
        self.log_info("等待波次信息...")
        while self.current_wave == -1:
            self.get_wave_info()
            self.sleep(0.2)

    def handle_mission_interface(self, stop_func=lambda: False):
        """每步操作后重新看画面：匹配到哪个元素，就执行哪一段逻辑（优先级从高到低）。"""
        if self.in_team():
            return False

        self.check_for_monthly_card()

        # 优先级 1：密函奖励（只在奖励弹窗出现时有意义）
        if self.find_letter_reward_btn():
            self.log_info("处理任务界面: 选择密函奖励")
            self.choose_letter_reward()
            return

        # 优先级 2：密函选择 / 委托手册
        if self.find_letter_interface():
            self.log_info("处理任务界面: 选择密函")
            self.choose_letter()
            return self.get_return_status()
        elif self.find_manual_select_btn():
            self.log_info("处理任务界面: 选择委托手册")
            self.choose_drop_rate()
            return self.get_return_status()

        # 优先级 3：开始 / 再次进行 / 继续 / 放弃
        # 「再次进行」只在结算界面出现，那里开始界面判据不命中，必须显式带上
        if self.find_start_interface() or self.find_result_again_btn():
            self.log_info("处理任务界面: 开始任务")
            self.start_mission()
            self.mission_status = Mission.START
            return
        elif self.find_action_dialog_continue() or self.find_action_dialog_retreat():
            if stop_func():
                self.log_info("处理任务界面: 终止任务")
                return Mission.STOP
            self.log_info("处理任务界面: 继续任务")
            self.continue_mission()
            self.mission_status = Mission.CONTINUE
            return
        elif self.find_esc_menu():
            self.log_info("处理任务界面: 放弃任务")
            self.give_up_mission()
            return Mission.GIVE_UP
        return False

    def get_return_status(self):
        ret = self.mission_status if self.mission_status else Mission.START
        self.mission_status = None
        return ret

    def reset_and_transport(self):
        # 1) 打开局内菜单(ESC 菜单)
        self.open_in_mission_menu()
        self.wait_until(
            condition=lambda: not self.find_esc_menu(),
            # 2) 点击"设置"入口, 点击后应关闭 ESC 菜单
            post_action=lambda: self.click_ui_coord(COORD.ESC_SETTINGS, name="esc_settings"),
            time_out=10,
        )
        # 搜索框取顶部页签栏中段，要包住「其他」页签的标注
        setting_box = self.screen_box('SETTING_OTHER_TAB')
        setting_other = self.wait_until(lambda: self.find_one("setting_other", box=setting_box), time_out=10,
                                        raise_if_not_found=True)
        # 云游戏局内打开菜单必然卡一下
        self.sleep(0.5)
        self.wait_until(
            condition=lambda: self.calculate_color_percentage(setting_menu_selected_color, setting_other) > 0.24,
            # 3) 点击“其他设置”页签(setting_other), 直到该页签呈选中状态(通过颜色占比判断)，点击不要那么频繁
            post_action=lambda: self.click_box_random(setting_other, after_sleep=0.5),
            time_out=10,
        )
        self.sleep(0.5)
        reset_area = self.screen_box('RESET_CHARACTER_AREA')
        safe_box2 = self.screen_box('RESET_OK_SAFE_BOX')

        def click_reset_entry():
            # 「复位角色」整条都能点，框内随机点
            self.click_box_random(reset_area, after_sleep=0.5,
                                  use_safe_move=True, safe_move_box=reset_area)

        def click_reset_ok():
            self.click_ui_coord(COORD.RESET_TRANSPORT_OK, name="reset_transport_ok",
                                after_sleep=0.5, use_safe_move=True, safe_move_box=safe_box2)

        # 4) 点「复位角色」，直到二次确认弹窗出现
        self.wait_until(condition=self.find_reset_confirm,
                        post_action=click_reset_entry, time_out=10)
        self.sleep(0.5)
        # 5) 点弹窗的「确定」，直到弹窗消失 —— 保证弹框流程真正走完
        self.wait_until(condition=lambda: not self.find_reset_confirm(),
                        post_action=click_reset_ok, time_out=10)
        if not self.wait_until(self.in_team, time_out=10):
            self.ensure_main()
            return False
        return True

    def find_letter_interface(self):
        """密函选择弹窗（局外/局内两套布局都算）—— 只用「⊘ 不使用」图标。

        它在两套布局里位置完全相同，对云游戏画面变糊也最鲁棒（实拍帧 0.9443）。
        底下的 [Esc] 放弃 / [Space] 确认选择不标注：前者会诱导代码点到"放弃"，
        后者实拍帧只有 0.7610（过不了 0.8）；"在哪套布局"由 mission_status 判。
        """
        return self.find_letter_select_not_use()


class QuickAssistTask:

    def __init__(self, owner: "CommissionsTask"):
        self._owner = owner
        self._move_task = None
        self._aim_task = None

    def run(self):
        if self._owner.commission_config.get("自动穿引共鸣", False):
            if not self._move_task:
                from src.tasks.trigger.AutoMoveTask import AutoMoveTask

                self._move_task = self._owner.get_task_by_class(AutoMoveTask)

            if self._move_task:
                self._move_task.try_connect_listener()
                self._move_task.run()
        
        if self._owner.commission_config.get("自动花弓", False):
            if not self._aim_task:
                from src.tasks.trigger.AutoAimTask import AutoAimTask

                self._aim_task = self._owner.get_task_by_class(AutoAimTask)

            if self._aim_task:
                self._aim_task.try_connect_listener()
                self._aim_task.run()

    def reset(self):
        if self._move_task:
            self._move_task.reset()
            self._move_task.try_disconnect_listener()
        if self._aim_task:
            self._aim_task.reset()
            self._aim_task.try_disconnect_listener()

def normalize_ocr_scale(cv_image, scale=1.0):
    """把 OCR 区域放大到固定字号再识别。

    区域坐标按 1600x900 定义，但运行分辨率可能是 1080p / 2K / 4K。实测 1600x900 下
    单个数字只有 16px 高，检测器会整个漏掉它（只剩「持有数：」）或把它认成别的数字；
    字号拉到 1600x900 的约 2 倍就全部稳定。所以按当前分辨率算放大倍数：
    1600x900 放 2 倍，2K 放约 1.1 倍，4K 本来就够大、不放大。
    """
    if scale <= 1.0:
        return cv_image
    return cv2.resize(cv_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def ocr_normalize(cv_image):
    cv_image = color_filter(cv_image, round_info_color)
    _, cv_image = cv2.threshold(cv_image, 127, 255, cv2.THRESH_BINARY)
    cv_image = cv2.resize(cv_image, None, fx=1, fy=0.75, interpolation=cv2.INTER_AREA)
    cv_image = cv2.erode(cv_image, np.ones((2, 2), np.uint8) , iterations=1)
    cv_image = cv2.bitwise_not(cv_image)
    return cv_image

setting_menu_selected_color = {
    'r': (220, 255),  # Red range
    'g': (200, 255),  # Green range
    'b': (125, 250)  # Blue range
}


green_mark_color = {
    'r': (40, 55),  # Red range
    'g': (165, 170),  # Green range
    'b': (120, 130)  # Blue range
}

round_info_color = {
    'r': (200, 255),  # Red range
    'g': (200, 255),  # Green range
    'b': (200, 255)  # Blue range
}


def _default_movement():
    pass
