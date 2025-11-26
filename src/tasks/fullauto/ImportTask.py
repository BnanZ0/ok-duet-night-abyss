from qfluentwidgets import FluentIcon
import re
import time
import win32con
import win32api
import cv2
import os
import json
import numpy as np
from functools import cached_property

from pathlib import Path
from PIL import Image
from ok import Logger, TaskDisabledException, GenshinInteraction
from ok import find_boxes_by_name
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.CommissionsTask import CommissionsTask, Mission, QuickMoveTask
from src.tasks.BaseCombatTask import BaseCombatTask

from src.tasks.trigger.AutoMazeTask import AutoMazeTask
from src.tasks.trigger.AutoRouletteTask import AutoRouletteTask

from src.tasks.AutoDefence import AutoDefence
from src.tasks.AutoExpulsion import AutoExpulsion
from src.tasks.AutoExploration import AutoExploration

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
        self.last_f_time = 0
        self.last_f_was_interact = False

        self.default_config.update({
            '轮次': 10,
            '外部文件夹': "",
            '副本类型': "默认",
            # '使用内建机关解锁': False,
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
            # '使用内建解密': '使用ok内建解密功能',
        })

        self.skill_tick = self.create_skill_ticker()
        self.action_timeout = 10
        self.quick_move_task = QuickMoveTask(self)

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            path = Path.cwd()
            self.script = self.process_json_files(f'{path}\mod\{self.config.get("外部文件夹")}\scripts')
            self.img = self.load_png_files(f'{path}\mod\{self.config.get("外部文件夹")}\map')
            _to_do_task = self
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
        self.init_all()
        self.load_char()
        if self.in_team():
            self.open_in_mission_menu()
            self.sleep(0.5)
        while True:
            if self.in_team():
                self.get_wave_info()
                if self.current_wave != -1:
                    if self.current_wave != self.runtime_state["wave"]:
                        self.runtime_state["wave"] = self.current_wave
                self.skill_tick()
                if time.time() - self.runtime_state["wave_start_time"] >= self.config.get('超时时间', 180):
                    self.log_info('任务超时')
                    self.open_in_mission_menu()
                    self.sleep(0.5)
                if self.delay_index is not None and time.time() > self.runtime_state["delay_task_start"]:
                    self.runtime_state["delay_task_start"] += 1
                    if self.match_map(self.delay_index):
                        self.walk_to_aim(self.delay_index)
            _status = self.handle_mission_interface(stop_func=self.stop_func)
            if _status == Mission.START or _status == Mission.STOP:
                if _status == Mission.STOP:
                    self.quit_mission()
                    self.log_info('任务中止')
                    self.init_all()
                    continue
                self.wait_until(self.in_team, time_out=30)
                self.log_info('任务开始')
                self.init_all()
                self.sleep(2)
                self.walk_to_aim()
                now = time.time()
                self.runtime_state.update({"wave_start_time": now, "delay_task_start": now + 1})
            elif _status == Mission.CONTINUE:
                self.log_info('任务继续')
                self.wait_until(self.in_team, time_out=30)
                self.init_for_next_round()
                now = time.time()
                self.runtime_state.update({"wave_start_time": now, "delay_task_start": now + 1})
            self.sleep(0.2)

    def init_all(self):
        self.init_for_next_round()
        self.delay_index = None
        self.skill_tick.reset()
        self.current_round = 0

    def init_for_next_round(self):
        self.init_runtime_state()

    def init_runtime_state(self):
        self.runtime_state = {"wave_start_time": 0, "wave": -1, "delay_task_start": 0}
        self.reset_wave_info()

    def stop_func(self):
        self.get_round_info()
        n = self.config.get('轮次', 3)
        if self.current_round >= n:
            return True

    def load_direct_folder(self, path):
        folders = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and item != 'builtin':
                folders.append(item)
        return folders

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

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.png'):
                file_path = os.path.join(folder_path, filename)
                try:
                    pil_img = Image.open(file_path)
                    img_array = np.array(pil_img)
                    if len(img_array.shape) == 3:
                        template = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                    else:
                        template = img_array

                    if template is None:
                        raise ValueError(f"图像转换失败: {file_path}")

                    # 兼容性处理：Python 3.9+ 才支持 removesuffix，低版本用切片
                    key_name = filename.removesuffix(".png") if hasattr(filename, "removesuffix") else filename[:-4]

                    png_files[key_name] = template
                    self.log_info(f"成功加载(已转灰度): {filename}")

                except Exception as e:
                    self.log_error(f"加载失败 {filename}", e)
        png_files = {key: png_files[key] for key in sorted(png_files.keys(), key=lambda x: (len(x), x))}
        return png_files

    def walk_to_aim(self, former_index=None):
        """
        尝试匹配下一个地图节点并执行宏。
        """
        # 预编译正则，提高多次调用的效率
        # 假设逻辑是：如果没有前置点，跳过以字母结尾的名字（通常是 start 点之后的步骤）
        end_with_letter_pattern = re.compile(r'[a-zA-Z]$')
        # maze_task = self.get_task_by_class(AutoMazeTask)
        # roulette_task = self.get_task_by_class(AutoRouletteTask)

        while True:
            start_time = time.perf_counter()
            map_index = None

            # 尝试在 5 秒内找到匹配的地图
            while map_index is None and time.perf_counter() - start_time < 5:
                # if self.config.get('使用内建机关解锁', False):
                #     maze_task.run()
                #     roulette_task.run()
                #     if maze_task.unlocked or roulette_task.unlocked:

                #         def find_next_child(parent_name):
                #             parent_name += "-"
                #             for name in self.img.keys():
                #                 if name.startswith(parent_name) and len(name) > len(parent_name):
                #                     return name
                #             return None

                #         step_1 = find_next_child(former_index)
                #         if step_1:
                #             self.log_info(f"索引跳跃: {former_index} -> {step_1}")
                #             former_index = step_1

                #             # 重置时间并跳过本次匹配
                #             start_time = time.perf_counter()
                #             self.sleep(1)
                #             continue
                #         else:
                #             self.log_info(f"无法找到 {former_index} 的后续节点")

                # 传入编译好的正则对象，稍微提升一点性能
                map_index, count = self.match_map(former_index, pattern=end_with_letter_pattern)

                if count == 0:
                    self.log_info("无候选地图，导航结束")
                    return True

                if map_index is None:
                    # 避免 CPU 100% 空转，给系统喘息时间
                    self.sleep(0.1)

            if map_index is not None:
                self.log_info(f'开始执行宏: {map_index}')
                try:
                    self.play_macro_actions(map_index)
                    # 更新前置节点，用于下一次逻辑判断
                    former_index = map_index
                except MacroFailedException:
                    logger.warning(f"宏执行失败: {map_index}")
                    return False
                except TaskDisabledException:
                    raise
                except Exception as e:
                    logger.error("ImportTask critical error", e)
                    raise
            else:
                self.log_info("超时未匹配到任何地图，假定到达目的地或路径丢失")
                return True

    def match_map(self, index, max_conf=0.0, pattern=None):  # 建议给 max_conf 一个合理的默认阈值，如 0.6
        """
        在当前屏幕中寻找匹配度最高的地图模板。
        """
        # 1. 提取图像处理逻辑到循环外 (极大的性能提升)
        # 假设 box 定义不变，可以提取出来
        box = self.box_of_screen_scaled(2560, 1440, 1, 1, 2559, 1439, name="full_screen", hcenter=True)

        # 只裁剪和转换一次屏幕
        cropped_screen = box.crop_frame(self.frame)
        screen_gray = cv2.cvtColor(cropped_screen, cv2.COLOR_BGR2GRAY)

        count = 0
        max_index = None
        best_threshold = max_conf  # 使用传入的阈值作为基准，低于此值不认为是匹配

        # 如果没有传入预编译的正则，则临时编译
        if pattern is None:
            pattern = re.compile(r'[a-zA-Z]$')

        for name, template_gray in self.img.items():
            # --- 过滤逻辑 ---
            # 逻辑 1: 起始状态 (index is None)
            if index is None and not pattern.search(name):
                continue

            if index is not None:
                # 逻辑 2: 不匹配自己 (先判断这个效率最高)
                if index == name:
                    continue

                # 逻辑 3: 严格的前缀匹配
                
                # 1. 必须是以 index 开头
                if not name.startswith(index):
                    continue
                
                # 2. 获取去掉 index 后的剩余部分
                # 例如: index="A-1", name="A-1-1" -> suffix="-1"
                # 例如: index="A-1", name="A-10"  -> suffix="0"
                suffix = name[len(index):]

                # 3. 检查分隔符：如果不是以 '-' 开头，说明不是层级递进，而是数字扩展 (如 1 -> 10)
                # 这一步阻止了 "60角色-A-1-1" 匹配到 "60角色-A-1-10"
                if not suffix.startswith('-'):
                    continue
                
                # 4. 层级限制
                # 如果剩余部分包含 2 个或以上的 '-', 说明是跨级节点 (如 A -> A-1-1)
                # 也就是 suffix 只能是 "-1", 不能是 "-1-1"
                if suffix.count('-') >= 2:
                    continue

                # 5. 长度限制 (保留作为最后的防线)
                # 由于上面限制了只能有一个 '-', 这个长度限制其实主要限制 "-xxxxx" 后面数字或字符太长的情况
                if len(suffix) > 4: 
                    continue

            count += 1

            # 执行匹配
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            _, threshold, _, _, = cv2.minMaxLoc(result)

            # 只记录比当前最佳结果更好的
            if threshold > best_threshold:
                best_threshold = threshold
                max_index = name
                # 只有当发现更好的匹配时才打印 debug 日志，减少刷屏
                # logger.debug(f"发现潜在匹配: {name} conf={threshold:.4f}")

        if max_index is not None:
            self.log_info(f"成功匹配: {max_index} (conf={best_threshold:.4f})")
        else:
            # 只有在真的找不到时才打印，或者使用 debug 级别
            # self.log_info("本轮未匹配到有效地图")
            pass

        return max_index, count

    @cached_property
    def genshin_interaction(self):
        """
        缓存 Interaction 实例，避免每次鼠标移动都重新创建对象。
        需要确保 self.executor.interaction 和 self.hwnd 在此类初始化时可用。
        """
        # 确保引用的是正确的类
        return GenshinInteraction(self.executor.interaction.capture, self.hwnd)

    def play_macro_actions(self, map_index):
        actions = self.script[map_index]["actions"]

        if "original_x_sensitivity" and "original_y_sensitivity" in self.script[map_index] :
            self.original_Xsensitivity = self.script[map_index]["original_x_sensitivity"]
            self.original_Ysensitivity = self.script[map_index]["original_y_sensitivity"]
        else:
            self.original_Xsensitivity = 1.0
            self.original_Ysensitivity = 1.0
        
        # 使用 perf_counter 获得更高精度的时间
        start_time = time.perf_counter()

        for action in actions:
            target_time = action['time']

            # 等待直到达到动作指定的时间戳
            while True:
                current_offset = time.perf_counter() - start_time
                if current_offset >= target_time:
                    break

                # 检查中断条件
                if self.check_for_monthly_card()[0]:
                    raise MacroFailedException

                # 这里的 next_frame 最好包含微小的 sleep，防止 CPU 100% 空转
                self.next_frame()

            if action['type'] == "delay":
                self.delay_index = map_index
            else:
                self.delay_index = None
                self.execute_action(action)

        self.sleep(2)

    def execute_action(self, action):
        """
        分发动作执行，替代原有的 execute_key_action
        """
        action_type = action['type']

        try:
            if action_type == "mouse_move":
                # 判断设置中灵敏度开关是否打开
                if self.sensitivity_config['Game Sensitivity Switch'] is True:
                    self.execute_mouse_move_after_calculation(action['dx'], action['dy'])
                else:
                    self.execute_mouse_move(action['dx'], action['dy'])

            elif action_type == "mouse_rotation":
                self.execute_mouse_rotation(action)

            elif action_type in ("mouse_down", "mouse_up"):
                self._handle_mouse_click(action_type, action['button'])

            elif action_type in ("key_down", "key_up"):
                self._handle_keyboard(action_type, action['key'])

            else:
                raise ValueError(f"Unknown action type: {action_type}")

        except Exception as e:
            # 获取 key 信息用于日志，如果不存在则为 None
            key_info = action.get('key') or action.get('button') or 'N/A'
            self.log_info(f"执行动作失败 -> type: {action_type}, key/btn: {key_info}, Error: {e}")
            raise

    def _handle_mouse_click(self, action_type, button):
        if action_type == "mouse_down":
            self.mouse_down(key=button)
        else:
            self.mouse_up(key=button)

    def _handle_keyboard(self, action_type, key):
        key = normalize_key(key)

        if key == 'f4':
            if action_type == "key_down":
                self.reset_and_transport()
            return

        # 3. 统一应用动态按键映射
        if key == 'lshift':
            key = self.get_dodge_key()
        elif key == 'f':
            key = self._resolve_f_key(action_type)
        elif key == '4':
            key = self.get_spiral_dive_key()
        elif key == 'e':
            key = self.get_combat_key()
        elif key == 'q':
            key = self.get_ultimate_key()

        # 4. 执行实际按键操作
        if action_type == "key_down":
            self.send_key_down(key)
        elif action_type == "key_up":
            self.send_key_up(key)

    def _resolve_f_key(self, action_type):
        """
        解析 F 键的具体行为：
        - 间隔 >= 3秒：视为交互 (Interact)
        - 间隔 < 3秒：视为快速破解 (Original F)
        """
        if action_type == "key_down":
            current_time = time.time()
            last_time = self.last_f_time
            if current_time - last_time >= 3.0:
                # 判定为交互
                self.last_f_time = current_time
                self.last_f_was_interact = True
                resolved_key = self.get_interact_key()
                return resolved_key
            else:
                # 判定为快速破解 (频繁按下)
                self.last_f_was_interact = False
                return 'f'
        
        else: # key_up
            # 根据按下时的判定结果，释放对应的键
            if self.last_f_was_interact:
                self.last_f_was_interact = False
                return self.get_interact_key()
            else:
                return 'f'

    def execute_mouse_rotation(self, action):
        direction = action.get("direction", "up")
        angle = action.get("angle", 0)
        sensitivity = action.get("sensitivity", 10)

        pixels = int(angle * sensitivity)

        # 使用字典映射替代 if-elif 链，更简洁
        direction_map = {"left": (-pixels, 0), "right": (pixels, 0), "up": (0, -pixels), "down": (0, pixels)}

        if direction not in direction_map:
            logger.warning(f"未知的鼠标方向: {direction}")
            return

        dx, dy = direction_map[direction]
        # 判断设置中灵敏度开关是否打开
        if self.sensitivity_config['Game Sensitivity Switch'] is True:
            self.execute_mouse_move_after_calculation(dx, dy)
        else:
            self.execute_mouse_move(dx, dy)
        logger.debug(f"鼠标视角旋转: {direction}, 角度: {angle}, 像素: {pixels}")

    def execute_mouse_move(self, dx, dy):
        """
        优化：复用 genshin_interaction 实例，避免频繁创建对象。
        """
        self.try_bring_to_front()

        # 使用缓存的实例
        self.genshin_interaction.move_mouse_relative(int(dx), int(dy))

    def execute_mouse_move_after_calculation(self, dx, dy):
        """
        用于不同灵敏度

        优化：复用 genshin_interaction 实例，避免频繁创建对象。
        """
        self.try_bring_to_front()

        calculation_dx, calculation_dy = self.calculate_sensitivity(self.original_Xsensitivity, self.original_Ysensitivity, dx, dy)

        # 使用缓存的实例
        self.genshin_interaction.move_mouse_relative(int(calculation_dx), int(calculation_dy))

def normalize_key(key: str) -> str:
    """
    标准化按键名称
    """
    if not isinstance(key, str):
        return key

    key_lower = key.lower()
    if key_lower == 'shift':
        return 'lshift'
    if key_lower == 'ctrl':
        return 'lcontrol'
    return key
