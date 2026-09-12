from ok import Logger, TaskDisabledException
from qfluentwidgets import FluentIcon

from src.dna_ui.Defs import REF_WIDTH, REF_HEIGHT
from src.tasks.AutoExploration import AutoExploration
from src.tasks.CommissionsTask import CommissionsTask, QuickAssistTask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.trigger.AutoMazeTask import AutoMazeTask
from src.tasks.trigger.AutoRouletteTask import AutoRouletteTask
from src.tasks.BaseCombatTask import BaseCombatTask

logger = Logger.get_logger(__name__)
DEFAULT_ACTION_TIMEOUT = 10


class MapDetectionError(Exception):
    """地图识别错误异常"""
    pass


class AutoExploration_Fast(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """全自动探险/无尽，感谢群友的行动逻辑"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.group_icon = FluentIcon.CAFE
        self.name = "自动探险/无尽"
        self.description = "全自动"
        self.group_name = "全自动"
        self.default_config.update({
            '轮次': 3,
            '超时时间': 120,
            '解密失败自动重开': True,
            '地图选择': ["探险电梯", "探险高台", "探险平地"],
        })
        self.config_description.update({
            '轮次': '打几个轮次',
            '超时时间': '超时后将发出提示',
            '解密失败自动重开': '不重开时会发出声音提示',
            '地图选择': '选择要自动执行的地图类型',
        })
        self.setup_commission_config()
        
        # 设置地图选择为下拉选择
        self.config_type["地图选择"] = {
            "type": "multi_selection",
            "options": ["探险电梯", "探险高台", "探险平地"],
        }
        self.action_timeout = DEFAULT_ACTION_TIMEOUT
        self.quick_assist_task = QuickAssistTask(self)
        
        # 地图检测点和执行函数的映射字典
        self.map_configs = {
            "探险电梯": {
                "track_point": (0.50, 0.69, 0.56, 0.77),
                "execute_func": self.execute_elevator_map
            },
            "探险高台": {
                "track_point": (0.29, 0.54, 0.34, 0.62),
                "execute_func": self.execute_platform_map
            },
            "探险平地": {
                "track_point": (0.44, 0.28, 0.49, 0.34),
                "execute_func": self.execute_ground_map
            }
        }

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            _to_do_task = self.get_task_by_class(AutoExploration)
            _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            original_info_set = _to_do_task.info_set
            _to_do_task.info_set = self.info_set
            while True:
                try:
                    return _to_do_task.do_run()
                except MapDetectionError as e:
                    # 地图识别错误，记录日志并重试
                    self.log_info(f"地图识别错误: {e}，重新开始任务")
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error('AutoDefence error', e)
            raise
        finally:
            if _to_do_task is not self:
                _to_do_task.info_set = original_info_set

    def walk_to_aim(self, delay=0):
        try:
            self.send_key_down("lalt")
            self.sleep(delay)
            map_selection = self.config.get("地图选择", [])
            current_map = self.detect_current_map()

            # 如果检测到未知地图，抛出地图识别错误
            if current_map == "未知地图":
                raise MapDetectionError("无法识别当前地图类型")
            
            # 如果选择了特定地图，但当前不是该地图，抛出地图识别错误
            if len(map_selection) != 0 and current_map not in map_selection:
                raise MapDetectionError(f"当前地图[{current_map}]不匹配选择的地图{map_selection}")
            
            # 执行对应地图的移动逻辑
            if current_map in self.map_configs:
                self.log_info(f"识别到地图类型：{current_map}，开始执行移动逻辑")
                return self.map_configs[current_map]["execute_func"]()
            else:
                # 这种情况理论上不应该发生，因为current_map是从map_configs中检测出来的
                raise MapDetectionError(f"地图配置不一致，检测到地图[{current_map}]但找不到对应的执行函数")
        finally:
            self.send_key_up("lalt")
    
    def detect_current_map(self):
        """检测当前地图类型"""
        detected_maps = []
        
        for map_name, config in self.map_configs.items():
            x1, y1, x2, y2 = config["track_point"]
            if self.find_track_point(x1, y1, x2, y2):
                detected_maps.append(map_name)
                self.log_info(f"检测到地图标记：{map_name} at ({x1}, {y1}, {x2}, {y2})")
        
        if len(detected_maps) == 0:
            logger.warning("地图检测失败：未检测到任何已知的地图标记")
            return "未知地图"
        elif len(detected_maps) == 1:
            return detected_maps[0]
        else:
            # 检测到多个地图标记，记录日志并返回第一个检测到的
            logger.warning(f"地图检测冲突：同时检测到多个地图标记 {detected_maps}，使用第一个检测到的地图")
            return detected_maps[0]
    
    def execute_elevator_map(self):
        """执行探险电梯地图的移动逻辑"""
        self.log_info("执行探险电梯地图移动")
        self.reset_and_transport()
        self.send_key_down("lalt")
        self.sleep(0.1)
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
        return True
    
    def execute_platform_map(self):
        """执行探险高台地图的移动逻辑"""
        self.log_info("执行探险高台地图移动")
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
        if not self.try_solving_puzzle():
            return True
        self.send_key_down("lalt")
        self.sleep(0.1)
        self.send_key_down("s")
        self.sleep(0.5)
        self.send_key_up("s")
        self.send_key_down("d")
        self.sleep(0.1)
        self.send_key("space", down_time=0.1,after_sleep=0.1)
        self.send_key(self.get_dodge_key(),  down_time=0.2,after_sleep=0.3)
        self.send_key("space", down_time=0.1,after_sleep=0.7)
        self.sleep(0.2)
        self.send_key_up("d")
        self.send_key_down("s")
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(),  down_time=0.2,after_sleep=0.3)
        self.sleep(0.2)
        self.send_key_up("s")
        self.send_key_down("d")
        self.sleep(0.1)
        self.send_key("space", down_time=0.1,after_sleep=0.1)
        self.sleep(0.1)
        self.send_key_up("d")
        self.sleep(1)
        self.send_key_down("w")
        self.sleep(2)
        self.send_key_down("d")
        self.sleep(0.2)
        self.send_key("space", down_time=0.1,after_sleep=0.1)
        self.send_key("space", down_time=0.5,after_sleep=0.7)
        self.sleep(0.2)
        self.send_key_up("d")
        self.sleep(0.2)
        self.send_key("space", down_time=0.1,after_sleep=0.1)
        self.send_key("space", down_time=0.7,after_sleep=0.7)
        self.sleep(0.5)
        self.send_key_up("w")
        self.middle_click()
        return True
    
    def execute_ground_map(self):
        """执行探险平地地图的移动逻辑"""
        self.log_info("执行探险平地地图移动")
        self.reset_and_transport()
        self.send_key_down("lalt")
        self.sleep(0.1)
        self.send_key_down("a")
        self.sleep(0.1)
        self.send_key(self.get_dodge_key(), down_time=1.1)
        self.send_key_up("a")
        self.sleep(0.6)
        self.send_key(self.get_interact_key(), down_time=0.1,after_sleep=0.8)
        if not self.try_solving_puzzle():
            return True
        self.send_key_down("lalt")
        self.sleep(0.1)
        self.send_key_down("w")
        self.sleep(0.1)
        self.send_key_down(self.get_dodge_key())
        self.sleep(1.2)
        self.send_key_up("w")
        self.send_key_down("d")
        self.sleep(0.8)
        self.send_key_up("d")
        self.send_key_down("w")
        self.sleep(0.1)
        self.send_key_down(self.get_dodge_key())
        self.sleep(1.5)
        self.send_key_up("w")
        self.sleep(0.1)
        self.send_key_down("a")
        self.sleep(0.3)
        self.send_key_up("a")
        self.send_key_down("s")
        self.sleep(0.1)
        self.send_key_up("s")
        self.sleep(0.1)
        self.middle_click()
        return True

    def find_track_point(self, x1, y1, x2, y2) -> bool:
        box = self.box_of_screen_scaled(REF_WIDTH, REF_HEIGHT, REF_WIDTH * x1, REF_HEIGHT * y1,
                                                       REF_WIDTH * x2, REF_HEIGHT * y2,
                                                       name="find_track_point", hcenter=True)
        result = super().find_track_point(threshold=0.7, box=box)
        # 调试信息：记录检测结果
        logger.debug(f"地图检测点 ({x1}, {y1}, {x2}, {y2}) 检测结果: {result}")
        return result
        
    def try_solving_puzzle(self):
        maze_task = self.get_task_by_class(AutoMazeTask)
        roulette_task = self.get_task_by_class(AutoRouletteTask)
        if not self.wait_until(
            self.in_team, 
            post_action = lambda: self.send_key(self.get_interact_key(), after_sleep=0.1),
            time_out = 1.5
        ):
            maze_task.run()
            roulette_task.run()
            if not self.wait_until(self.in_team, time_out=1.5):           
                if self.config.get("解密失败自动重开", True):                    
                    self.log_info("未成功处理解密，等待重开")
                    self.open_in_mission_menu()
                else:
                    self.log_info_notify("未成功处理解密，请求人工接管")
                    self.soundBeep()
                    self.wait_until(self.in_team, time_out = 60)
                return False               
        return True
        
    
