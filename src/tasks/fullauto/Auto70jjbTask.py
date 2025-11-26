from qfluentwidgets import FluentIcon
import re
import time
import win32con
import win32gui
import cv2

from ok import Logger, TaskDisabledException, Box
from ok import find_boxes_by_name
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask, Mission, QuickMoveTask
from src.tasks.BaseCombatTask import BaseCombatTask

from src.tasks.AutoDefence import AutoDefence

logger = Logger.get_logger(__name__)


class Auto70jjbTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动70级皎皎币本"
        self.description = "全自动"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        self.default_config.update({
            '轮次': 1,
        })

        self.setup_commission_config()
        keys_to_remove = ["启用自动穿引共鸣"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.config_description.update({
            '轮次': '打几个轮次',
        })

        self.action_timeout = 10
        self.quick_move_task = QuickMoveTask(self)

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            _to_do_task = self.get_task_by_class(AutoDefence)
            _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            return _to_do_task.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error('AutoDefence error', e)
            raise

    # def do_run(self):
    #     self.init_param()
    #     self.load_char()
    #     _wave = -1
    #     _wait_next_wave = False
    #     _wave_start = 0
    #     if self.in_team():
    #         self.open_in_mission_menu()
    #         self.sleep(0.5)
    #     while True:
    #         if self.in_team():
    #             self.get_wave_info()
    #             if self.current_wave != -1:
    #                 if self.current_wave != _wave:
    #                     _wave = self.current_wave
    #                     _wave_start = time.time()
    #                     _wait_next_wave = False
    #                 self.skill_time = self.use_skill(self.skill_time)
    #                 if not _wait_next_wave and time.time() - _wave_start >= self.config.get('超时时间', 120):
    #                     self.log_info('任务超时')
    #                     self.open_in_mission_menu()
    #                     self.sleep(0.5)
    #                     _wait_next_wave = True

    #         _status = self.handle_mission_interface(stop_func=self.stop_func)
    #         if _status == Mission.START or _status == Mission.STOP:
    #             if _status == Mission.STOP:
    #                 self.quit_mission()
    #                 self.log_info('任务中止')
    #                 self.init_param()
    #                 continue
    #             else:
    #                 self.log_info('任务完成')
    #             self.wait_until(self.in_team, time_out=30)
    #             self.init_param()
    #             self.send_key_down("lalt")
    #             self.sleep(2)
    #             self.walk_to_aim()
    #             self.send_key_up("lalt")
    #             _wave_start = time.time()

    #             self.reset_wave_info()
    #             while self.current_wave == -1 and time.time() - _wave_start < 2:
    #                 self.get_wave_info()
    #                 self.sleep(0.2)
    #             if self.current_wave == -1:
    #                 self.log_info('未正确到达任务地点')
    #                 self.open_in_mission_menu()
    #                 self.sleep(0.5)
    #         elif _status == Mission.CONTINUE:
    #             self.log_info('任务继续')
    #             self.wait_until(self.in_team, time_out=30)
    #             self.reset_wave_info()
    #         self.sleep(0.2)

    # def init_param(self):
    #     self.stop_mission = False
    #     self.current_round = 0
    #     self.reset_wave_info()
    #     self.skill_time = 0

    # def stop_func(self):
    #     self.get_round_info()
    #     n = self.config.get('轮次', 3)
    #     if self.current_round >= n:
    #         return True

    def find_track_point(self, x1, y1, x2, y2) -> bool:
        box = self.box_of_screen_scaled(2560, 1440, 2560 * x1, 1440 * y1, 2560 * x2, 1440 * y2, name="find_track_point",
                                        hcenter=True)
        return super().find_track_point(threshold=0.7, box=box)
    
    def _release_all_move_keys(self):
        """释放所有移动相关按键，防止卡键"""
        keys = ['w', 'a', 's', 'd', 'lalt', self.get_dodge_key()]
        for k in keys:
            self.send_key_up(k)

    def _path_no_elevator(self):
        """路径逻辑：70皎皎币-无电梯"""
        self.send_key_down("w")
        self.sleep(0.1)
        self.send_key_down("a")
        self.sleep(0.1)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2.2)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2.2)        
        self.send_key_up("w")
        self.sleep(1)
        self.send_key("space", down_time=0.1)
        self.sleep(1)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(1.8)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2.2)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key_up("a")

        # 检查是否到达
        start = time.time()
        self.reset_wave_info()
        while self.current_wave == -1 and time.time() - start < 2:
            self.get_wave_info()
            self.sleep(0.2)
        
        # 未到达的补救措施
        if self.current_wave == -1:
            self.send_key_down('a')
            self.sleep(0.2)
            self.send_key_down(self.get_dodge_key())
            self.sleep(1)
            self.send_key('space', down_time=0.2, after_sleep=1.8)
            self.send_key_up(self.get_dodge_key())
            self.sleep(0.1)
            self.send_key_up('a')

    def _path_elevator_right(self):
        """路径逻辑：70皎皎币-电梯右"""
        self.reset_and_transport()
        self.send_key('s', down_time=0.2, after_sleep=0.2)
        self.middle_click(after_sleep=0.2)
        
        # 重新按住奔跑，防止传送后松开
        self.send_key_down("lalt") 
        self.sleep(0.05)
        
        self.send_key_down('a')
        self.sleep(0.2)
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.4)
        self.send_key_down('w')
        self.sleep(0.7)
        self.send_key_up('lshift') # 原代码有这个，保留
        self.sleep(0.1)
        self.send_key_up("a")
        self.sleep(0.1)
        
        self.send_key('space', down_time=0.3, after_sleep=0.2)
        self.send_key('space', down_time=0.3, after_sleep=0.4)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2.2)        
        self.send_key_down('d')
        self.sleep(0.1)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.2)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.1)
        self.send_key_up("w")
        self.sleep(0.7)
        
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.5)
        self.send_key_down('w')
        self.sleep(1)
        self.send_key_up('d')
        self.sleep(0.7)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2.5)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.2)
        self.send_key_up('w')
        
        self._release_all_move_keys()
        self.reset_and_transport()

    def _path_elevator_left(self):
        """路径逻辑：70皎皎币-电梯左"""
        self.reset_and_transport()
        self.send_key_down("lalt")
        self.sleep(0.05)
        self.send_key_down('w')
        self.sleep(0.2)
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.6)
        self.send_key_down("a")
        self.sleep(0.6)
        self.send_key_up('a')
        self.sleep(0.8)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(2)
        self.send_key_down("d")
        self.sleep(1)
        self.send_key_up('d')
        self.sleep(0.8)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.8)
        self.send_key_down(self.get_dodge_key())
        self.sleep(1)
        self.send_key_down("d")
        self.sleep(0.5)
        self.send_key_up('d')
        self.sleep(3.6) # 长时间滑行
        
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.2)
        self.send_key_up('w')

        self._release_all_move_keys()
        self.reset_and_transport()

    def _path_elevator_center(self):
        """路径逻辑：70皎皎币-电梯中"""
        self.reset_and_transport()
        self.send_key_down("lalt")
        self.sleep(0.05)
        self.send_key_down('w')
        self.sleep(0.2)
        self.send_key_down('d')
        self.sleep(0.2)
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.7)
        self.send_key_up('w')
        self.sleep(1.2)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.2)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(0.4)
        self.send_key_down('s')
        self.sleep(0.3)
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.4)
        self.send_key_up('s')
        self.sleep(1)
        self.send_key(self.get_dodge_key(), down_time=0.2)
        self.sleep(2) # 这里等待较长
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.1)
        self.send_key_up('d')

        self._release_all_move_keys()
        self.reset_and_transport()

    def walk_to_aim(self):
        """
        主寻路函数：根据识别到的坐标选择路径
        """
        try:
            self.send_key_down("lalt")
            self.sleep(2) # 保持原有的启动延迟

            # 使用 if-elif 结构，优先级清晰，且只执行一个分支
            if self.find_track_point(0.20, 0.54, 0.22, 0.59):
                # 分支1：无电梯
                self._path_no_elevator()
                
            elif self.find_track_point(0.66, 0.67, 0.69, 0.72):
                # 分支2：电梯右
                self._path_elevator_right()
                
            elif self.find_track_point(0.32, 0.67, 0.35, 0.73):
                # 分支3：电梯左
                self._path_elevator_left()
                
            elif self.find_track_point(0.50, 0.71, 0.53, 0.76):
                # 分支4：电梯中
                self._path_elevator_center()

        except Exception as e:
            logger.error("Error in walk_to_aim", e)
            # 可以在这里添加日志记录
        finally:
            self._release_all_move_keys()
