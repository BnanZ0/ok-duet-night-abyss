import re
import time
import cv2
from enum import Enum

from ok import find_boxes_by_name, TaskDisabledException
from src.tasks.BaseDNATask import BaseDNATask, isolate_white_text_to_black


class Mission(Enum):
    START = 1
    CONTINUE = 2
    STOP = 3
    GIVE_UP = 4


class CommissionsTask(BaseDNATask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_round = -1
        self.current_wave = -1
        self.mission_status = None

    def setup_commission_config(self):
        self.default_config.update({
            '超时时间': 120,
            "委托手册": "不使用",
            "使用技能": "不使用",
            "技能释放频率": 5.0,
            "启用自动穿引共鸣": True,
            "发出声音提醒": True,
            "自动选择首个密函和密函奖励": True,
        })
        self.config_description.update({
            "超时时间": "超时后将重启任务",
            "技能释放频率": "毎几秒释放一次技能",
            "启用自动穿引共鸣": "在需要跑图时时启用触发任务的自动穿引共鸣",
            "发出声音提醒": "在需要时发出声音提醒",
            "自动选择首个密函和密函奖励": "刷武器密函时不建议使用",
        })
        self.config_type["委托手册"] = {
            "type": "drop_down",
            "options": ["不使用", "100%", "200%", "800%", "2000%"],
        }
        self.config_type["使用技能"] = {
            "type": "drop_down",
            "options": ["不使用", "战技", "终结技"],
        }

    def find_quit_btn(self, threshold = 0):
        return self.find_one("ingame_quit_icon", threshold=threshold)

    def find_continue_btn(self, threshold = 0):
        return self.find_one("ingame_continue_icon", threshold=threshold)

    def find_bottom_start_btn(self, threshold = 0):
        return self.find_start_btn(threshold=threshold, box=self.box_of_screen_scaled(2560, 1440, 2094, 1262, 2153, 1328, name="start_mission", hcenter=True))
    
    def find_big_bottom_start_btn(self, threshold = 0):
        return self.find_start_btn(threshold=threshold, box=self.box_of_screen_scaled(2560, 1440, 1667, 1259, 1728, 1328, name="start_mission", hcenter=True))

    def find_letter_btn(self, threshold = 0):
        return self.find_start_btn(threshold=threshold, box=self.box_of_screen_scaled(2560, 1440, 1630, 852, 1884, 920, name="letter_btn", hcenter=True))

    def find_letter_reward_btn(self, threshold = 0):
        return self.find_start_btn(threshold=threshold, box=self.box_of_screen_scaled(2560, 1440, 1071, 1160, 1120, 1230, name="letter_reward_btn", hcenter=True))

    def find_drop_rate_btn(self, threshold=0):
        return self.find_start_btn(threshold=threshold, box=self.box_of_screen_scaled(2560, 1440, 1060, 935, 1420, 1000, name="drop_rate_btn", hcenter=True))

    def find_esc_menu(self, threshold=0):
        return self.find_one("quit_big_icon", threshold=threshold)

    def open_in_mission_menu(self, time_out=20, raise_if_not_found=True):
        if self.find_esc_menu():
            return True
        found = False
        start = time.time()
        while time.time() - start < time_out:
            self.send_key("esc")
            if self.wait_until(
                self.find_esc_menu, time_out=2, raise_if_not_found=False
            ):
                found = True
                break
        else:
            if raise_if_not_found:
                raise Exception("未找到任务菜单")
        self.sleep(0.2)
        return found

    def start_mission(self, timeout=10):
        action_timeout = self.safe_get("action_timeout", timeout)
        start_time = time.time()
        while time.time() - start_time < action_timeout:
            if btn := self.find_retry_btn() or self.find_bottom_start_btn() or self.find_big_bottom_start_btn():
                self.move_mouse_to_safe_position()
                self.click_box(btn, after_sleep=0)
                self.move_back_from_safe_position()
            self.sleep(0.2)
            if self.wait_until(condition=lambda: self.find_start_btn() or self.find_letter_btn(), time_out=1):
                break
            if self.find_retry_btn() and self.calculate_color_percentage(retry_btn_color, self.get_box_by_name("retry_icon")) < 0.05:
                self.soundBeep()
                self.log_info_notify("任务无法继续")
                raise TaskDisabledException
        else:
            raise Exception("等待开始任务超时")

    def quit_mission(self, timeout=10):
        action_timeout = self.safe_get("action_timeout", timeout)
        quit_btn = self.wait_until(
            self.find_quit_btn, time_out=action_timeout, raise_if_not_found=True
        )
        self.sleep(0.5)
        self.wait_until(
            condition=lambda: not self.find_quit_btn(),
            post_action=lambda: self.click_box(quit_btn, after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(1)
        self.wait_until(
            lambda: not self.in_team(), time_out=action_timeout, raise_if_not_found=True
        )

    def give_up_mission(self, timeout=10):
        action_timeout = self.safe_get("action_timeout", timeout)
        box = self.box_of_screen_scaled(2560, 1440, 1301, 776, 1365, 841, name="give_up_mission", hcenter=True)
        self.open_in_mission_menu()

        self.wait_until(
            condition=lambda: self.find_start_btn(box=box),
            post_action=lambda: self.click_relative(0.95, 0.91, after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(0.5)
        self.wait_until(
            condition=lambda: not self.find_start_btn(box=box),
            post_action=lambda: self.click_box(self.find_start_btn(box=box), after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(2)

    def continue_mission(self, timeout=10):
        if self.in_team():
            return False
        action_timeout = self.safe_get("action_timeout", timeout)
        continue_btn = self.wait_until(
            self.find_continue_btn, time_out=action_timeout, raise_if_not_found=True
        )
        self.wait_until(
            condition=lambda: not self.find_continue_btn(),
            post_action=lambda: self.click_box(continue_btn, after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )
        self.sleep(0.5)
        return True

    def choose_drop_rate(self, timeout=10):
        action_timeout = self.safe_get("action_timeout", timeout)
        self.sleep(0.5)
        self.choose_drop_rate_item()
        self.wait_until(
            condition=lambda: not self.find_drop_item(),
            post_action=lambda: self.click_box(self.find_drop_rate_btn(), after_sleep=0.25),
            time_out=action_timeout,
            raise_if_not_found=True,
        )

    def choose_drop_rate_item(self):
        if not hasattr(self, "config"):
            return
        drop_rate = self.config.get("委托手册", "不使用")
        if drop_rate == "不使用":
            return
        elif drop_rate == "100%":
            self.click_relative(0.40, 0.56)
        elif drop_rate == "200%":
            self.click_relative(0.50, 0.56)
        elif drop_rate == "800%":
            self.click_relative(0.59, 0.56)
        elif drop_rate == "2000%":
            self.click_relative(0.68, 0.56)
        self.log_info(f"使用委托手册: {drop_rate}")
        self.sleep(0.25)

    def choose_letter(self, timeout=10):
        if not hasattr(self, "config"):
            return
        action_timeout = self.safe_get("action_timeout", timeout)
        if self.config.get("自动选择首个密函和密函奖励", False):
            if self.find_letter_btn():
                self.move_mouse_to_safe_position()
                self.click(0.56, 0.5)
                self.move_back_from_safe_position()
                self.sleep(0.5)
                self.wait_until(
                    condition=lambda: not self.find_letter_btn(),
                    post_action=lambda: self.click(0.79, 0.61, after_sleep=0.25),
                    time_out=action_timeout,
                    raise_if_not_found=True,
                )
        else:
            self.log_info_notify("需自行选择密函")
            self.soundBeep()
            self.wait_until(
                lambda: not self.find_letter_btn(),
                time_out=300,
                raise_if_not_found=True,
            )

    def choose_letter_reward(self, timeout=10):
        if not hasattr(self, "config"):
            return
        action_timeout = self.safe_get("action_timeout", timeout)
        if self.config.get("自动选择首个密函和密函奖励", False):
            self.wait_until(
                condition=lambda: not self.find_letter_reward_btn(),
                post_action=lambda: self.click(0.50, 0.83, after_sleep=0.25),
                time_out=action_timeout,
                raise_if_not_found=True,
            )
        else:
            self.log_info_notify("需自行选择密函奖励")
            self.soundBeep()
            self.wait_until(
                lambda: not self.find_letter_reward_btn(),
                time_out=300,
                raise_if_not_found=True,
            )

    def use_skill(self, skill_time):
        if not hasattr(self, "config"):
            return
        if self.config.get(
            "使用技能", "不使用"
        ) != "不使用" and time.time() - skill_time >= self.config.get("技能释放频率", 5):
            skill_time = time.time()
            if self.config.get("使用技能") == "战技":
                self.get_current_char().send_combat_key()
            elif self.config.get("使用技能") == "终结技":
                self.get_current_char().send_ultimate_key()
        return skill_time

    def get_round_info(self):
        """获取并更新当前轮次信息。"""
        if self.in_team():
            return

        self.sleep(1)
        round_info_box = self.box_of_screen_scaled(2560, 1440, 531, 517, 618, 602, name="round_info", hcenter=True)
        texts = self.ocr(box=round_info_box)

        prev_round = self.current_round
        new_round_from_ocr = None
        if texts and texts[0].name.isdigit():
            new_round_from_ocr = int(texts[0].name)

        if new_round_from_ocr is not None:
            self.current_round = new_round_from_ocr
        elif self.current_round != -1:  # OCR失败，但之前已有轮次记录，则递增
            self.current_round += 1

        if prev_round != self.current_round:
            self.info_set("当前轮次", self.current_round)

    def get_wave_info(self):
        if not self.in_team():
            return
        mission_info_box = self.box_of_screen_scaled(2560, 1440, 275, 372, 360, 470, name="mission_info", hcenter=True)
        texts = self.ocr(
            box=mission_info_box,
            frame_processor=isolate_white_text_to_black,
            match=re.compile(r"\d/\d"),
        )
        if texts and len(texts) == 1:
            prev_wave = self.current_wave
            try:
                if m := re.match(r"(\d)/\d", texts[0].name):
                    self.current_wave = int(m.group(1))
            except:
                return
            if prev_wave != self.current_wave:
                self.info_set("当前波次", self.current_wave)

    def wait_until_get_wave_info(self):
        self.log_info("等待波次信息...")
        while self.current_wave == -1:
            self.get_wave_info()
            self.sleep(0.2)

    def handle_mission_interface(self, stop_func=lambda: False):
        if self.in_team():
            return False
        
        self.check_for_monthly_card()

        if self.find_letter_reward_btn():
            self.choose_letter_reward()
            return

        if self.find_letter_btn():
            self.choose_letter()
            return self.get_return_status()
        elif self.find_drop_item():
            self.choose_drop_rate()
            return self.get_return_status()

        if self.find_retry_btn() or self.find_bottom_start_btn() or self.find_big_bottom_start_btn():
            self.start_mission()
            self.mission_status = Mission.START
            return
        elif self.find_continue_btn():
            if stop_func():
                return Mission.STOP
            self.continue_mission()
            self.mission_status = Mission.CONTINUE
            return
        elif self.find_esc_menu():
            self.give_up_mission()
            return Mission.GIVE_UP
        return False

    def get_return_status(self):
        ret = self.mission_status if self.mission_status else Mission.START
        self.mission_status = None
        return ret

    def find_next_hint(self, x1, y1, x2, y2, s, box_name="hint_text"):
        texts = self.ocr(
            box=self.box_of_screen(x1, y1, x2, y2, hcenter=True),
            target_height=540,
            name=box_name,
        )
        fps_text = find_boxes_by_name(texts, re.compile(s, re.IGNORECASE))
        if fps_text:
            return True

    def reset_and_transport(self):
        self.open_in_mission_menu()
        self.sleep(0.8)
        self.wait_until(
            condition=lambda: not self.find_esc_menu(),
            post_action=self.click(0.73, 0.92, after_sleep=0.5),
            time_out=4,
        )
        setting_box = self.box_of_screen_scaled(2560, 1440, 738, 4, 1123, 79, name="other_section", hcenter=True)
        setting_other = self.wait_until(lambda: self.find_one("setting_other", box=setting_box), time_out=10, raise_if_not_found=True)
        self.wait_until(
            condition=lambda: self.calculate_color_percentage(setting_menu_selected_color, setting_other) > 0.24,
            post_action=self.click_box(setting_other, after_sleep=0.5),
            time_out=4,
        )
        confirm_box = self.box_of_screen_scaled(2560, 1440, 1298, 776, 1368, 843, name="confirm_btn", hcenter=True)
        self.wait_until(
            condition=lambda: self.find_start_btn(box=confirm_box),
            post_action=lambda: (
                self.move_mouse_to_safe_position(),
                self.click(0.60, 0.32),
                self.move_back_from_safe_position(),
                self.sleep(1),
            ),
            time_out=6,
        )
        if not self.wait_until(
            condition=self.in_team,
            post_action=self.click(0.59, 0.56, after_sleep=0.5),
            time_out=4,
        ):
            self.wait_until(self.in_team, post_action=self.send_key("esc", after_sleep=1), time_out=10)
            return False
        return True


class QuickMoveTask:
    def __init__(self, owner: CommissionsTask):
        self.owner = owner
        self.owner._move_task = None

    def run(self):
        if not hasattr(self.owner, "config"):
            return
        if self.owner.config.get("启用自动穿引共鸣", False):
            if not self.owner._move_task:
                from src.tasks.AutoMoveTask import AutoMoveTask

                self.owner._move_task = self.owner.get_task_by_class(AutoMoveTask)
            self.owner._move_task.run()

    def reset(self):
        if self.owner._move_task:
            self.owner._move_task.reset()


setting_menu_selected_color = {
    'r': (220, 255),  # Red range
    'g': (200, 255),  # Green range
    'b': (125, 250)  # Blue range
}

retry_btn_color = {
    'r': (220, 230),  # Red range
    'g': (175, 185),  # Green range
    'b': (79, 89)  # Blue range
}
