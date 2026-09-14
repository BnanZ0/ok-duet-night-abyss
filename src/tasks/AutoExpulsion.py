from qfluentwidgets import FluentIcon
import time
import random

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.CommissionsTask import CommissionsTask, Mission

logger = Logger.get_logger(__name__)


class AutoExpulsion(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动驱离"
        self.description = "全自动"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        self.setup_commission_config()
        self.setup_mission_start_config()
        keys_to_remove = ["轮次"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        # 云游戏实拍帧糊、模板分低，识别弹窗会有假阴性，给足重试轮次
        self.action_timeout = 20
        
        self.skill_tick = self.create_skill_ticker()
        self.random_walk_tick = self.create_random_walk_ticker()

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoExpulsion error", e)
            raise

    def do_run(self):
        self.init_all()
        self.load_char()
        self.count = 0
        while True:
            if self.in_team():
                self.handle_in_mission()

            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=30)
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
        self._mission_started = False

    def init_for_next_round(self):
        self.init_runtime_state()

    def init_runtime_state(self):
        self.runtime_state = {"start_time": 0}
        self.random_walk_tick.reset()

    def handle_in_mission(self):
        if self.runtime_state["start_time"] == 0:
            if not self.move_on_begin():
                return
            self.runtime_state["start_time"] = time.time()
            self.count += 1

        if time.time() - self.runtime_state["start_time"] >= self.config.get("超时时间", 120):
            logger.info("已经超时，重开任务...")
            self.give_up_mission()
            return

        self.random_walk_tick()
        self.skill_tick()

    def handle_mission_start(self):
        self.sleep(2)
        self.log_info("任务开始")
    
    def stop_func(self):
        pass

    def create_random_walk_ticker(self):
        """创建一个随机游走的计时器函数。"""
        def action():
            if not self.config.get("随机游走", False):
                return
            duration = random.uniform(0, 1)
            direction = random.choice(["w", "a", "s", "d"])
            self.send_key(direction, down_time=duration)

        return self.create_ticker(action, interval=5, interval_random_range=(0.8, 2))