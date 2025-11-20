from qfluentwidgets import FluentIcon
import re
import time
import win32con
import win32gui
import cv2
import os
import json
import numpy as np

from pathlib import Path
from PIL import Image
from ok import Logger, TaskDisabledException, GenshinInteraction
from ok import find_boxes_by_name
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask, Mission, QuickMoveTask
from src.tasks.BaseCombatTask import BaseCombatTask

from src.tasks.AutoDefence import AutoDefence
from src.tasks.AutoExpulsion import AutoExpulsion
from src.tasks.AutoExploration import AutoExploration
from src.tasks.trigger.AutoWheelTask import AutoWheelTask
from src.tasks.trigger.AutoPuzzleTask import AutoPuzzleTask 

logger = Logger.get_logger(__name__)


class MacroFailedException(Exception):
    """外部脚本失败异常。"""
    pass


class ImportTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "使用外部移动逻辑自动打本"
        self.description = "全自动"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE
        self.default_config.update({
            '轮次': 10,
            '外部文件夹': "",
            '副本类型': "默认",
            '内置解密失败自动重开': False,
        })
        self.config_type['外部文件夹'] = {
            "type": "drop_down",
            "options": self.load_direct_folder(f'{Path.cwd()}\mod'),
        }

        self.config_type['副本类型'] = {
            "type": "drop_down",
            "options": ["默认", "扼守无尽", "探险无尽"],
        }
        self.setup_commission_config()
        keys_to_remove = ["启用自动穿引共鸣"]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.config_description.update({
            '轮次': '如果是无尽关卡，选择打几个轮次',
            '外部文件夹': '选择mod目录下的外部逻辑',
            '内置解密失败自动重开': '完全依靠内部解密则打开此选项,有巧手或者外置脚本自行识图解密则关闭此选项',
        })

        self.action_timeout = 10
        self.quick_move_task = QuickMoveTask(self)

        self.sequence_timeout = 5 # 按键序列超时时间（秒）
        self.tasks_array = []
        task_classes = [AutoWheelTask, AutoPuzzleTask]
        for cls in task_classes:
            task = self.get_task_by_class(cls)
            if task is not None:  
                self.tasks_array.append(task)

    def load_direct_folder(self, path):
        folders = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and item != 'builtin':
                folders.append(item)
        return folders

    def run(self):
        path = Path.cwd()
        self.script = self.process_json_files(f'{path}\mod\{self.config.get("外部文件夹")}\scripts')
        self.img = self.load_png_files(f'{path}\mod\{self.config.get("外部文件夹")}\map')
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        _to_do_task = self
        try:
            if self.config.get('副本类型') == '扼守无尽':
                _to_do_task = self.get_task_by_class(AutoDefence)
                _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            elif self.config.get('副本类型') == '探险无尽':
                _to_do_task = self.get_task_by_class(AutoExploration)
                _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            elif self.config.get('副本类型') == '驱离':
                _to_do_task = self.get_task_by_class(AutoExpulsion)
                _to_do_task.config_external_movement(self.walk_to_aim, self.config)
            return _to_do_task.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error('AutoDefence error', e)
            raise

    def do_run(self):
        self.init_param()
        self.load_char()
        _wave = -1
        _wait_next_wave = False
        _wave_start = 0
        _delay_task_start = 0
        if self.in_team():
            self.open_in_mission_menu()
            self.sleep(0.5)
        while True:
            if self.in_team():
                self.get_wave_info()
                if self.current_wave != -1:
                    if self.current_wave != _wave:
                        _wave = self.current_wave
                        _wait_next_wave = False
                self.skill_time = self.use_skill(self.skill_time)
                if time.time() - _wave_start >= self.config.get('超时时间', 180):
                    self.log_info('任务超时')
                    self.open_in_mission_menu()
                    self.sleep(0.5)
                    _wait_next_wave = True
                if self.delay_index is not None and time.time() > _delay_task_start:
                    _delay_task_start += 1
                    if self.match_map(self.delay_index):
                        self.walk_to_aim(self.delay_index)
            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START or _status == Mission.STOP:
                if _status == Mission.STOP:
                    self.quit_mission()
                    self.log_info('任务中止')
                    self.init_param()
                    continue
                else:
                    self.log_info('任务完成')
                self.wait_until(self.in_team, time_out=30)
                self.init_param()
                self.sleep(2)
                self.walk_to_aim()
                _wave_start = time.time()
                _delay_task_start = _wave_start + 1
                self.reset_wave_info()
            elif _status == Mission.CONTINUE:
                self.log_info('任务继续')
                self.wait_until(self.in_team, time_out=30)
                self.reset_wave_info()
                _wave_start = time.time()
            self.sleep(0.2)

    def init_param(self):
        self.delay_index = None
        self.stop_mission = False
        self.current_round = 0
        self.reset_wave_info()
        self.skill_time = 0

        # 跨map_index的按键状态追踪
        self.reset_key_sequence()   

    def reset_key_sequence(self):   
        self.f_key_count = 0
        self.esc_pressed_in_sequence = False
        self.sequence_start_time = 0

    def try_to_solve_tasks(self):
        if len(self.tasks_array)>0 and not self.wait_until(self.in_team, time_out=1.5):      
            for task in self.tasks_array:
                        task.run()

            if not self.wait_until(self.in_team, time_out=20):           
                if self.config.get("内置解密失败自动重开", False):                    
                    self.log_info("未成功处理解密，等待重开")
                    self.open_in_mission_menu()
                else:
                    self.log_info_notify("未成功处理解密，忽略错误继续")
                    # self.soundBeep()
                    # self.wait_until(self.in_team, time_out = 60)
                return False    
        return True

    def stop_func(self):
        self.get_round_info()
        n = self.config.get('轮次', 3)
        if self.current_round >= n:
            return True

    def process_json_files(self, folder_path):
        json_files = {}
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        json_files[filename.removesuffix(".json")] = data
                        self.log_info(f"成功加载: {file_path}")
                except Exception as e:
                    self.log_info(f"加载失败 {file_path}: {e}")

        return json_files

    def load_png_files(self, folder_path):
        png_files = {}
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.png'):
                file_path = os.path.join(folder_path, filename)
                try:
                    pil_img = Image.open(file_path)
                    img_array = np.array(pil_img)
                    template = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                    if template is None:
                        raise FileNotFoundError(f"无法读取模板图像: {file_path}")
                    png_files[filename.removesuffix(".png")] = template
                    self.log_info(f"成功加载: {filename}")
                except Exception as e:
                    self.log_info(f"加载失败 {filename}: {e}")
        png_files = {key: png_files[key] for key in sorted(png_files.keys(), key=lambda x: (len(x), x))}
        return png_files

    def walk_to_aim(self, former_index=None):
        while True:
            start = time.time()
            map_index = None
            count = 0
            while map_index is None and time.time() - start < 5:
                map_index, count = self.match_map(former_index)
                if count == 0:
                    return True
            if map_index is not None:
                self.log_info(f'执行{map_index}')
                try:
                    self.play_macro_actions(map_index)
                except MacroFailedException:
                    return False
                except Exception as e:
                    logger.error("ImportTask error", e)
                    raise
                former_index = map_index
            else:
                return True

    def match_map(self, index, max_conf=0):
        box = self.box_of_screen_scaled(2560, 1440, 1, 1, 2559, 1439, name="full_screen", hcenter=True)
        count = 0
        max_index = None

        for i, name in enumerate(self.img):
            if index is None and not re.search(r'[a-zA-Z]$', name):
                continue
            if index is not None and not (index in name and len(name) - len(index) <= 3):
                continue
            if index is not None and index == name:
                continue
            count += 1
            img = self.img[name]

            cropped = box.crop_frame(self.frame)
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            result = cv2.matchTemplate(gray, img, cv2.TM_CCOEFF_NORMED)
            _, threshold, _, _, = cv2.minMaxLoc(result)
            if threshold > max_conf:
                max_conf = threshold
                max_index = name
            self.log_info(f"匹配: {name} confidence = {threshold}")
        #        feature = self.find_one(template=img, box=box, threshold=0.4)
        #        feature = self.find_one(img, box=self.box_of_screen(0.18, 0.1, 0.82, 0.81),
        #                              threshold=0.65, frame_processor=binarize_for_matching)
        #        if feature is None:
        #            self.log_info(f"匹配: {name} confidence < 0.4")
        #            continue
        #        self.log_info(f"匹配: {name} confidence = {feature.confidence}")
        #        if feature is not None and feature.confidence > max_conf:
        #            max_conf = feature.confidence
        #            max_index = name

        if max_index is not None:
            self.log_info(f"成功匹配: {max_index}")
        else:
            self.log_info("匹配失败")
        return max_index, count


    def play_macro_actions(self, map_index):
        actions = self.script[map_index]["actions"]
        start = time.time()
        
        for i, action in enumerate(actions):
            # 等待到动作执行时间
            while time.time() - start < action['time']:
                if self.check_for_monthly_card()[0]:
                    # 重置按键状态
                    self.reset_key_sequence()
                    raise MacroFailedException
                self.next_frame()
            
            # 检查序列是否超时
            current_time =time.time()
            if self.f_key_count > 0 and current_time - self.sequence_start_time > self.sequence_timeout:
                # 超时重置状态
                logger.debug(f"按键序列超时，重置状态,{current_time - self.sequence_start_time}>{self.sequence_timeout}")
                self.reset_key_sequence()
            
            # 处理延迟动作
            if action['type'] == "delay":
                self.delay_index = map_index
            else:
                self.delay_index = None
                self.execute_key_action(action)
                
                # 处理按键抬起事件
                if action['type'] == "key_up":
                    if action['key'] == "f":
                        current_time = time.time()
                        
                        # 如果是第一个F键，开始计时
                        if self.f_key_count == 0:
                            logger.debug("开始F键计数序列")
                            self.sequence_start_time = current_time
                        
                        # 增加F键计数
                        self.f_key_count += 1
                        
                        # 检查是否满足触发条件（5秒内按了至少两次F键，且中间没有ESC）
                        if self.f_key_count >= 2 and not self.esc_pressed_in_sequence:
                            logger.debug(f"{self.sequence_timeout }秒内按了{self.f_key_count}次F键，触发解密任务")
                            time_reset = time.time()
                            self.try_to_solve_tasks()
                            start += time.time() - time_reset
                            
                            # 触发后重置状态
                            self.reset_key_sequence()
                    
                    elif action['key'] == "esc":
                        # 如果在F键序列中按了ESC，标记状态
                        if self.f_key_count > 0:
                            logger.debug("F键序列中按下了ESC，标记状态")
                            self.esc_pressed_in_sequence = True 
        
        self.sleep(2)
    def execute_key_action(self, action):
        try:
            if action['type'] == "mouse_down":
                self.mouse_down(key=action['button'])
            elif action['type'] == "mouse_up":
                self.mouse_up(key=action['button'])
            elif action['type'] == "key_down":
                action['key'] = normalize_key(action['key'])
                if action['key'] == 'f4':
                    self.reset_and_transport()
                elif action['key'] == 'lshift':
                    self.send_key_down(self.get_dodge_key())
                elif action['key'] == 'f':
                    self.send_key_down(self.get_interact_key())
                else:
                    self.send_key_down(action['key'])
            elif action['type'] == "key_up":
                action['key'] = normalize_key(action['key'])
                if action['key'] != 'f4':
                    self.send_key_up(action['key'])
            elif action['type'] == "mouse_rotation":
                self.execute_mouse_rotation(action)
            elif action['type'] == "mouse_move":
                self.execute_mouse_move(action['dx'], action['dy'])
            else:
                raise
        except:
            self.log_info(f"不支持的按键-> type: {action['type']} key: {action['key']}")
            raise

    def execute_mouse_rotation(self, action):
        direction = action.get("direction", "up")
        angle = action.get("angle", 0)
        sensitivity = action.get("sensitivity", 10)

        pixels = angle * sensitivity

        if direction == "left":
            dx, dy = -pixels, 0
        elif direction == "right":
            dx, dy = pixels, 0
        elif direction == "up":
            dx, dy = 0, -pixels
        elif direction == "down":
            dx, dy = 0, pixels
        else:
            logger.warning(f"未知的鼠标方向: {direction}")
            return
        self.execute_mouse_move(dx, dy)
        logger.debug(f"鼠标视角旋转: {direction}, 角度: {angle}, 像素: {pixels}")
        
    def execute_mouse_move(self, dx, dy):
        interaction = self.executor.interaction
        _genshin_interaction = GenshinInteraction(
                interaction.capture, self.hwnd
            )
            # 确保窗口在前台
        self.hwnd.bring_to_front()
        _genshin_interaction.move_mouse_relative(int(dx), int(dy))

        

def normalize_key(key: str) -> str:
    """
    将 'shift' (不区分大小写) 标准化为 'lshift'。
    """
    if isinstance(key, str) and key.lower() == 'shift':
        return 'lshift'
    if isinstance(key, str) and key.lower() == 'ctrl':
        return 'lcontrol'
    return key

