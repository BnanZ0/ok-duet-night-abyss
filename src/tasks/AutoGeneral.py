from qfluentwidgets import FluentIcon
from typing import Callable

from ok import Logger, TaskDisabledException
from src.tasks.CommissionsTask import CommissionsTask, QuickAssistTask, Mission, _default_movement
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.trigger.AutoMazeTask import AutoMazeTask
from src.tasks.trigger.AutoRouletteTask import AutoRouletteTask

logger = Logger.get_logger(__name__)

DEFAULT_ACTION_TIMEOUT = 10


class AutoGeneral(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "通用型半自动"
        self.description = "半自动 (只有基础操作)"
        self.group_name = "半自动"
        self.group_icon = FluentIcon.VIEW

        self.setup_commission_config()
        self.setup_mission_start_config()
        keys_to_remove = ["超时时间"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.default_config.update({
            "启动机关解锁": True,
        })

        self.action_timeout = DEFAULT_ACTION_TIMEOUT
        self.quick_assist_task = QuickAssistTask(self)
        self.maze_task = self.get_task_by_class(AutoMazeTask)
        self.roulette_task = self.get_task_by_class(AutoRouletteTask)
        self.external_movement = _default_movement
        self.external_movement_evac = _default_movement
        self._external_config = None
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

    def config_external_movement(self, approach: Callable, config: dict, evacuation: Callable = _default_movement):
        if callable(approach):
            self.external_movement = approach
        else:
            self.external_movement = _default_movement
        if callable(evacuation):
            self.external_movement_evac = evacuation
        else:
            self.external_movement_evac = _default_movement
        self._merged_config_cache = None
        self._external_config = config

    def run(self):
        self.enable_fidget_action = False
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
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
                if self.move_on_begin():
                    self.handle_in_mission()
            else:
                if self.config.get("启动机关解锁", False):
                    self.maze_task.run()
                    self.roulette_task.run()

            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=DEFAULT_ACTION_TIMEOUT)
                self.sleep(2)
                self.init_all()
                self.handle_mission_start()
            elif _status == Mission.STOP:
                pass
            elif _status == Mission.CONTINUE:
                pass

            self.sleep(0.1)        

    def init_all(self):
        self.init_for_next_round()
        self.current_round = 0
        self._mission_started = False

    def init_for_next_round(self):
        self.init_runtime_state()

    def init_runtime_state(self):
        pass

    def handle_in_mission(self):
        self.quick_assist_task.run()
    
    def handle_mission_start(self):
        pass

    def stop_func(self):
        self.get_round_info()
        if self.current_round >= self.config.get("轮次", 3):
            return True