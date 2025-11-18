import time

from ok import Logger, TaskDisabledException
from qfluentwidgets import FluentIcon

from src.tasks.AutoExploration import AutoExploration
from src.tasks.CommissionsTask import CommissionsTask, QuickMoveTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.trigger.AutoPuzzleTask import AutoPuzzleTask
from src.tasks.trigger.AutoWheelTask import AutoWheelTask
from src.tasks.BaseCombatTask import BaseCombatTask

logger = Logger.get_logger(__name__)
DEFAULT_ACTION_TIMEOUT = 10


class AutoExploration_Fast(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """全自动探险/无尽，感谢群友的行动逻辑"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.group_icon = FluentIcon.CAFE
        self.name = "自动探险/无尽"
        self.description = "需要巧手可后台全自动，不要使用小体型自机"
        self.group_name = "全自动"
        self.default_config.update({
            '轮次': 3,
            '超时时间': 120,
            '解密失败自动重开': True,
        })
        self.config_description.update({
            '轮次': '打几个轮次',
            '超时时间': '超时后将发出提示',
            '解密失败自动重开': '不重开时会发出声音提示',
        })
        self.setup_commission_config()
        keys_to_remove = ["启用自动穿引共鸣"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)
        self.action_timeout = DEFAULT_ACTION_TIMEOUT
        self.quick_move_task = QuickMoveTask(self)

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        _to_do_task = self
        try:
            _to_do_task = self.get_task_by_class(AutoExploration)
            _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            return _to_do_task.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error('AutoDefence error', e)
            raise

    def walk_to_aim(self):
        if self.find_track_point(0.50,0.69,0.56,0.77):
            #30探险-电梯
            self.reset_and_transport()
            self.send_key_down("lalt")
            self.sleep(0.05)
            self.send_key_down("a")
            self.sleep(0.1)
            self.send_key_down(self.get_dodge_key())
            self.sleep(0.8)
            self.send_key(self.get_dodge_key(), down_time=0.2,after_sleep=0.8)
            self.send_key(self.get_dodge_key(), down_time=0.2,after_sleep=1.6)
            self.send_key_down("s")
            self.send_key_up("a")
            self.sleep(0.3)
            self.send_key("space", down_time=0.1,after_sleep=0.4)
            self.send_key("space", down_time=0.1,after_sleep=0.4)
            self.send_key("space", down_time=0.1,after_sleep=0.7)
            self.send_key_up(self.get_dodge_key())
            self.send_key_up("s")
            self.sleep(0.6)
            self.send_key(self.get_interact_key(), down_time=0.1,after_sleep=0.8)
            if not self.try_solving_puzzle():
                return True
            self.send_key_down("a")
            self.sleep(0.1)
            self.send_key(self.get_dodge_key(), down_time=0.2,after_sleep=0.6)
            self.send_key_down(self.get_dodge_key())
            self.sleep(0.9)
            self.send_key_down("w")
            self.sleep(0.2)
            self.send_key_up("a")
            self.sleep(0.1)
            self.send_key_up(self.get_dodge_key())
            self.send_key_up("w")
            self.sleep(0.2)
            self.send_key_up("lalt")
            return True

        if self.find_track_point(0.29,0.54,0.34,0.62):
            #40探险-高台
            self.send_key_down("lalt")
            self.sleep(0.05)
            self.send_key_down("w")
            self.sleep(0.1)
            self.send_key_down(self.get_dodge_key())
            self.sleep(1.2)
            self.send_key(self.get_dodge_key(),  down_time=0.2,after_sleep=0.3)
            self.send_key_down(self.get_dodge_key())
            self.sleep(0.1)
            self.send_key_down("a")
            self.sleep(0.1)
            self.send_key("space", down_time=0.1,after_sleep=0.1)
            self.send_key(self.get_dodge_key(),  down_time=0.2,after_sleep=0.3)
            self.send_key("space", down_time=0.1,after_sleep=0.7)
            self.send_key_up(self.get_dodge_key())
            self.send_key_up("w")
            self.sleep(0.1)
            self.send_key_up("a")
            self.sleep(0.6)
            self.send_key(self.get_interact_key(), down_time=0.1,after_sleep=0.8)
            logger.info("到达高台，尝试解密")
            if not self.try_solving_puzzle():
                logger.info("解密失败")
                return True
            logger.info("解密完成，继续前进")
            self.send_key_down("d")
            self.sleep(0.1)
            self.send_key(self.get_dodge_key(),  down_time=0.2)
            self.sleep(0.1)
            self.send_key_up("d")
            self.sleep(0.1)
            self.send_key_down("s")
            self.sleep(0.1)
            self.send_key_up(self.get_dodge_key())
            self.send_key_up("s")
            self.sleep(0.2)
            self.middle_click()
            self.send_key_up("lalt")
            return True
            
        if self.find_track_point(0.44,0.28,0.49,0.34):
            #40探险-平地
            self.reset_and_transport()
            self.send_key_down("lalt")
            self.sleep(0.05)
            self.send_key_down("a")
            self.sleep(0.1)
            self.send_key(self.get_dodge_key(), down_time=1.1)
            self.send_key_up("a")
            self.sleep(0.6)
            self.send_key(self.get_interact_key(), down_time=0.1,after_sleep=0.8)
            if not self.try_solving_puzzle():
                return True
            self.send_key('d',down_time=0.8,after_sleep=0.1)
            self.middle_click()
            self.send_key_up("lalt")
            return True
            
            
    def find_track_point(self, x1, y1, x2, y2) -> bool:
        box = self.box_of_screen_scaled(2560, 1440, 2560*x1, 1440*y1, 2560*x2, 1440*y2, name="find_track_point", hcenter=True)
        return super().find_track_point(threshold=0.7, box=box)
        
    def try_solving_puzzle(self):
        puzzle_task1 = self.get_task_by_class(AutoPuzzleTask)
        puzzle_task2 = self.get_task_by_class(AutoWheelTask)
        if not self.wait_until(
            self.in_team, 
            post_action = lambda: self.send_key(self.get_interact_key(), after_sleep=0.1),
            time_out = 1.5
        ):
            logger.info("尝试迷宫解密")
            puzzle_task1.run()
            if not self.wait_until(self.in_team, time_out=1.5):
                logger.info("尝试转盘解密")
                puzzle_task2.run()
                if not self.wait_until(self.in_team, time_out=1.5):
                    if self.config.get("解密失败自动重开", True):                    
                        self.log_info("未成功处理解密，等待重开")
                        self.open_in_mission_menu()
                    else:
                        self.log_info_notify("未成功处理解密，请求人工接管")
                        self.soundBeep()
                        self.wait_until(self.in_team, time_out = 60)
                    return False
        else:
            logger.info("已经退出界面无需解密") 
        return True
        
    