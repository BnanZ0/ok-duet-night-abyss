from qfluentwidgets import FluentIcon
import time
import re
import cv2
from typing import Callable

from ok import Logger, TaskDisabledException
from src.tasks.CommissionsTask import CommissionsTask, QuickAssistTask, Mission, _default_movement
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.trigger.AutoRouletteTask import AutoRouletteTask
from src.tasks.trigger.AutoMazeTask import AutoMazeTask

logger = Logger.get_logger(__name__)


class AutoHedge(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动避险"
        self.description = "半自动"
        self.group_name = "半自动"
        self.group_icon = FluentIcon.VIEW

        self.setup_commission_config()
        keys_to_remove = ["轮次"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.config_description.update({
            '超时时间': '超时后将发出提示',
        })

        self.quick_assist_task = QuickAssistTask(self)
        self.external_movement = _default_movement
        self.external_movement_evac = _default_movement
        self._external_config = None
        self._merged_config_cache = None
        self.skill_tick = self.create_skill_ticker()

        self.track_point_pos = 0
        self.mission_complete = False
        self.ocr_future = None
        self.last_ocr_result = -1
        self.roulette_task = None
        self.maze_task = None


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

    def config_external_movement(self, approach: Callable, evacuation: Callable, config: dict):
        if callable(approach) and callable(evacuation):
            self.external_movement = approach
            self.external_movement_evac = evacuation
        else:
            self.external_movement = _default_movement
            self.external_movement_evac = _default_movement
        self._merged_config_cache = None
        self._external_config = config

    def run(self):
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
        self.init_task()
        self.init_all()
        self.load_char()

        if self.external_movement is not _default_movement and self.in_team():
            self.open_in_mission_menu()

        while True:
            if self.in_team():
                self.handle_in_mission()
            else:
                self.roulette_task.run()
                self.maze_task.run()

            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=self.action_timeout)
                self.init_all()
                self.handle_mission_start()
            elif _status == Mission.STOP:
                pass
            elif _status == Mission.CONTINUE:
                pass

            self.sleep(0.1)

    def init_all(self):
        self.init_for_next_round()
        self.skill_tick.reset()
        self.current_round = 0
        self.track_point_pos = 0
        self.mission_complete = False
        self.ocr_future = None
        self.last_ocr_result = -1

    def init_for_next_round(self):
        self.init_runtime_state()

    def init_runtime_state(self):
        self.runtime_state = {"start_time": 0, "in_progress": False, "wait_next_round": False}

    def handle_in_mission(self):
        self.update_mission_status()
        if self.runtime_state["in_progress"]:
            if self.runtime_state["start_time"] == 0:
                self.runtime_state["start_time"] = time.time()
                self.quick_assist_task.reset()

            if not self.runtime_state["wait_next_round"] and time.time() - self.runtime_state[
                "start_time"] >= self.config.get("超时时间", 120):
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
                if self.external_movement_evac is not _default_movement:
                    self.log_info("任务结束")
                    self.external_movement_evac()
                    self.log_info("外部移动执行完毕。")
                    self.wait_until(lambda: not self.in_team(), time_out=30)
                    return
                else:
                    self.log_info_notify("任务结束")
                    self.soundBeep()
            self.quick_assist_task.run()

    def handle_mission_start(self):
        if self.external_movement is not _default_movement:
            self.log_info("任务开始")
            self.external_movement(delay=2)
            time_out = self.action_timeout + 10
            self.log_info(f"外部移动执行完毕，等待战斗开始，{time_out}秒后超时")
            if not self.wait_until(lambda: self.runtime_state["in_progress"] or self.find_esc_menu(), post_action=self.update_mission_status,
                                   time_out=time_out):
                self.log_info("超时重开")
                self.open_in_mission_menu()
                return
            else:
                self.log_info("战斗开始")
        else:
            self.sleep(2)
            self.log_info_notify("任务开始")
            self.soundBeep()

    def stop_func(self):
        pass

    def update_mission_status(self):
        if self.mission_complete:
            return
        percentage = self.get_serum_process_info()
        if percentage == 100:
            self.runtime_state["in_progress"] = False
            self.mission_complete = True
        elif percentage >= 0:
            self.runtime_state["in_progress"] = True
        if not self.runtime_state["in_progress"] and not self.mission_complete:
            _track_point = self.find_top_right_track_pos()
            if _track_point < 0:
                return
            if self.track_point_pos == 0:
                self.track_point_pos = _track_point
            elif (rpd := abs(_track_point - self.track_point_pos) / self.track_point_pos) > 0.02:
                self.log_debug(f"track point diff pct {rpd}")
                self.runtime_state["in_progress"] = True

    def get_serum_process_info(self):
        if self.ocr_future and self.ocr_future.done():
            texts = self.ocr_future.result()
            self.ocr_future = None
            if texts and getattr(texts[0], "name", None):
                if (m := re.search(r"(\d{1,3})\s*[％%]", texts[0].name)):
                    pct = int(m.group(1))
                    if pct > self.last_ocr_result and pct <= 100:
                        self.last_ocr_result = pct
            return self.last_ocr_result
        if self.ocr_future is None:
            box = self.box_of_screen_scaled(3840, 2160, 12, 494, width_original=625, height_original=508, name="process_info", hcenter=True)
            frame = self.frame.copy()
            self.ocr_future = self.thread_pool_executor.submit(self.ocr, frame=frame, box=box, match=re.compile(r"\d{1,3}\s*[％%]"))
        return self.last_ocr_result

    def find_top_right_track_pos(self):
        box = self.box_of_screen_scaled(2560, 1440, 2183, 82, 2414, 140, name="track_point", hcenter=True)
        template = cv2.resize(self.get_feature_by_name("track_point").mat, None, fx=0.79, fy=0.79,
                              interpolation=cv2.INTER_LINEAR)
        ret = -1
        box = self.find_track_point(box=box, template=template, filter_track_color=True)
        if box is not None:
            ret = box.x
        return ret

    def init_task(self):
        if self.roulette_task is None:
            self.roulette_task = self.get_task_by_class(AutoRouletteTask)
        if self.maze_task is None:
            self.maze_task = self.get_task_by_class(AutoMazeTask)
