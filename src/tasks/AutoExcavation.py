from qfluentwidgets import FluentIcon
import time

from ok import Logger, TaskDisabledException, find_color_rectangles
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.CommissionsTask import CommissionsTask, QuickAssistTask, Mission

logger = Logger.get_logger(__name__)

class AutoExcavation(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动勘察"
        self.description = "半自动"
        self.group_name = "半自动"
        self.group_icon = FluentIcon.VIEW

        self.setup_commission_config()
        self.setup_mission_start_config()
        keys_to_remove = ["超时时间"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.quick_assist_task = QuickAssistTask(self)
        self.skill_tick = self.create_skill_ticker()

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoExcavation error", e)
            raise

    def do_run(self):
        self.init_all()
        self.load_char()

        while True:
            if self.in_team():
                if self.move_on_begin():
                    self.handle_in_mission()

            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=self.action_timeout)
                self.sleep(2)
                self.init_all()
                self.handle_mission_start()
            elif _status == Mission.STOP:
                self.log_info("任务中止")
                self.quit_mission()
            elif _status == Mission.CONTINUE:
                self.log_info("任务继续")
                self.init_for_next_round()
                self.wait_until(self.in_team, time_out=self.action_timeout)

                self.sleep(2)
                if not self.find_target_health_bar():
                    self.soundBeep(1)
                
            self.sleep(0.1)

    def init_all(self):
        self.init_for_next_round()
        self.skill_tick.reset()
        self.current_round = 0
        self._mission_started = False

    def init_for_next_round(self):
        self.init_runtime_state()
        self.excavator_count = 0

    def init_runtime_state(self):
        self.runtime_state = {"start_time": 0}

    def handle_in_mission(self):
        if self.find_target_health_bar():
            if self.runtime_state["start_time"] == 0:
                self.runtime_state["start_time"] = time.time()
                self.quick_assist_task.reset()
            self.skill_tick()
        else:
            if self.runtime_state["start_time"] > 0:
                if self.wait_until(lambda: self.find_target_health_bar(), time_out=2):
                    return
                self.init_runtime_state()
                self.excavator_count += 1
                if self.excavator_count < 3:
                    self.soundBeep(1)
            self.quick_assist_task.run()

    def handle_mission_start(self):
        self.log_info_notify("任务开始")
        self.soundBeep()

    def stop_func(self):
        self.get_round_info()
        if self.current_round >= self.config.get("轮次", 3):
            return True

    def is_in_combat(self):
        """自动前进到开战的停止判据：目标血条（它自己 skill_tick 的判据）。"""
        return bool(self.find_target_health_bar())

    def find_target_health_bar(self, threshold: float = 0.6):
        health_bar_box = self.screen_box('HEALTH_BAR')
        self.draw_boxes("health_bar", health_bar_box, color="blue")
        min_width = self.width_of_screen(100 / 2560)
        min_height = self.height_of_screen(4 / 1440)
        health_bar = find_color_rectangles(self.frame, green_health_bar_color, min_width, min_height,
                                           box=health_bar_box, threshold=threshold)
        self.draw_boxes(boxes=health_bar)
        return health_bar


green_health_bar_color = {
    "r": (135, 150),  # Red range
    "g": (200, 215),  # Green range
    "b": (150, 165),  # Blue range
}
