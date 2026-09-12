from qfluentwidgets import FluentIcon
import time
from typing import Callable

from ok import Logger, TaskDisabledException
from src.tasks.CommissionsTask import CommissionsTask, QuickAssistTask, Mission, _default_movement
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask

logger = Logger.get_logger(__name__)


class AutoExploration(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动探险"
        self.description = "半自动"
        self.group_name = "半自动"
        self.group_icon = FluentIcon.VIEW

        self.setup_commission_config()

        self.config_description.update({
            '超时时间': '超时后将发出提示',
        })

        self.quick_assist_task = QuickAssistTask(self)
        self.external_movement = _default_movement
        self._external_config = None
        self.skill_tick = self.create_skill_ticker()
        self._merged_config_cache = None

    @property
    def config(self):
        if self.external_movement == _default_movement or not self._external_config:
            return getattr(self, '_base_config', None)

        if self._merged_config_cache is None:
            base = getattr(self, '_base_config', {})
            self._merged_config_cache = base.copy() if base else {}
            self._merged_config_cache.update(self._external_config)
        return self._merged_config_cache

    @config.setter
    def config(self, value):
        self._base_config = value
        self._merged_config_cache = None

    def config_external_movement(self, func: Callable, config: dict):
        if callable(func):
            self.external_movement = func
        else:
            self.external_movement = _default_movement
        self._merged_config_cache = None
        self._external_config = config

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        self.external_movement = _default_movement
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoExploration error", e)
            raise

    def do_run(self):
        self.init_all()
        self.load_char()

        if self.external_movement is not _default_movement and self.in_team():
            self.open_in_mission_menu()

        while True:
            if self.in_team():
                self.handle_in_mission()

            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=30)
                self.init_all()
                self.handle_mission_start()
            elif _status == Mission.STOP:
                self.log_info("任务中止")
                self.quit_mission()
            elif _status == Mission.CONTINUE:
                self.log_info("任务继续")
                self.init_for_next_round()
                self.wait_until(self.in_team, time_out=self.action_timeout)

            self.sleep(0.1)

    def init_all(self):
        self.init_for_next_round()
        self.skill_tick.reset()
        self.current_round = 0

    def init_for_next_round(self):
        self.init_runtime_state()

    def init_runtime_state(self):
        self.runtime_state = {"start_time": 0, "wait_next_round": False}

    def handle_in_mission(self):
        if self.find_serum():
            if self.runtime_state["start_time"] == 0:
                self.runtime_state["start_time"] = time.time()
                self.quick_assist_task.reset()

            if not self.runtime_state["wait_next_round"] and time.time() - self.runtime_state["start_time"] >= self.config.get("超时时间", 120):
                if self.external_movement is not _default_movement:
                    self.log_info("任务超时")
                    self.give_up_mission()
                    return
                else:
                    self.log_info_notify("任务超时")
                    self.soundBeep()
                    self.runtime_state["wait_next_round"] = True

            if not self.runtime_state["wait_next_round"]:
                self.skill_tick()
        else:
            if self.runtime_state["start_time"] > 0:
                self.init_runtime_state()
            self.quick_assist_task.run()

    def handle_mission_start(self):
        if self.external_movement is not _default_movement:
            self.log_info("任务开始")
            self.external_movement(delay=2)
            time_out = self.action_timeout + 10
            self.log_info(f"外部移动执行完毕，等待战斗开始，{time_out}秒后超时")
            if not self.wait_until(lambda: self.find_serum() or self.find_esc_menu(), time_out=time_out):
                self.log_info("超时重开")
                self.open_in_mission_menu()
            else:
                self.log_info("战斗开始")
        else:
            self.sleep(2)
            self.log_info_notify("任务开始")
            self.soundBeep()

    def stop_func(self):
        self.get_round_info()
        if self.current_round >= self.config.get("轮次", 3):
            return True

    def find_serum(self):
        # 判据：局内左侧的"血清水滴"图标（进战斗后才出现，用来判断是否已进入战斗）
        # 标注在新截图上：bbox (28,332,30,52) @1600x900
        # 搜索框 = bbox 外扩，必须**包住** bbox，否则永远匹配不到（旧代码这里就是错位的）
        box = self.screen_box('SERUM_ICON')
        if self.width < 1920 and self.height < 1080:
            threshold = 0.7
        else:
            threshold = 0
        return bool(self.find_one("serum_icon", box=box, threshold=threshold))
