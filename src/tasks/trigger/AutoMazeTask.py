import json
import os
import time
import win32api
import win32con

from ok import TriggerTask, Logger
from src.tasks.BaseDNATask import BaseDNATask

logger = Logger.get_logger(__name__)


class AutoMazeTask(BaseDNATask, TriggerTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动解锁迷宫"
        self.description = "自动识别并进行迷宫解锁"
        self.default_config.update({
            "启用": True,
            "移动延迟（秒）": 0.1,
        })
        self._unlocked = False
        self._last_no_puzzle_log = 0
        self.puzzle_paths = self._load_puzzle_paths()

    @property
    def unlocked(self):
        return self._unlocked

    def run(self):
        self._unlocked = False
        if self.scene.in_team(self.in_team_and_world):
            return
        
        self.scan_puzzles()

    def scan_puzzles(self):
        """扫描所有拼图位置"""
        found_any = False
        if self.find_one("mech_retry",
                         box=self.box_of_screen_scaled(2560, 1440, 2287, 1006, 2414, 1132, name="mech_retry",
                                                       hcenter=True), threshold=0.65):
            self.sleep(0.5)
            self.send_key("f", after_sleep=1)
            self._unlocked = True
            return
        if not self.find_one("mech_retry",
                             box=self.box_of_screen_scaled(3840, 2160, 3367, 1632, 3548, 1811, name="mech_retry",
                                                           hcenter=True), threshold=0.65):
            return
        
        self.rel_move_if_in_win()

        # 统一的检测区域（放大 5%）
        puzzle_box = self.box_of_screen_scaled(3840, 2160, 2336, 604, 3307, 1578, name="puzzle_detection", hcenter=True)
        box = self.find_best_match_in_box(puzzle_box,
                                          ["mech_maze_1", "mech_maze_2", "mech_maze_3", "mech_maze_4", "mech_maze_5",
                                           "mech_maze_6", "mech_maze_7", "mech_maze_8"], 0.7)
        if box:
            found_any = True
            self.log_puzzle_info(box)
            self.solve_puzzle(box.name)

        if not found_any:
            # 降低日志频率，避免刷屏
            now = time.time()
            if now - self._last_no_puzzle_log > 5.0:
                logger.debug("未检测到解密拼图")
                self._last_no_puzzle_log = now

        self._unlocked = found_any

    def solve_puzzle(self, puzzle_name):
        """执行 puzzle 解密（需要游戏窗口在前台）"""
        if puzzle_name not in self.puzzle_paths:
            raise ValueError(f"{puzzle_name} 没有解密路径")

        logger.info(f"🎯 检测到 {puzzle_name}，准备执行自动解密")

        hwnd_window = self.executor.device_manager.hwnd_window

        # 确保游戏窗口在前台，解密需要游戏窗口在前台（鼠标拖拽操作无法后台执行）
        self.try_bring_to_front()

        puzzle_data = self.puzzle_paths[puzzle_name]
        # 提取 coordinates 字段（如果是新格式），否则使用原数据（兼容旧格式）
        if isinstance(puzzle_data, dict) and "coordinates" in puzzle_data:
            path = puzzle_data["coordinates"]
        else:
            path = puzzle_data

        # 获取配置的移动延迟
        move_delay = self.config.get("移动延迟（秒）", 0.1)

        # 路径是基于 1920x1080 的，需要缩放到当前分辨率
        scale_x = hwnd_window.width / 1920
        scale_y = hwnd_window.height / 1080

        # 第一个点：按下鼠标
        x = int(path[0][0] * scale_x)
        y = int(path[0][1] * scale_y)
        abs_x, abs_y = hwnd_window.get_abs_cords(x, y)
        logger.debug(f"按下并移动到: ({abs_x}, {abs_y})")

        win32api.SetCursorPos((abs_x, abs_y))
        self.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.sleep(move_delay)

        # 中间点：移动鼠标（保持按下状态）
        for i in range(1, len(path)):
            x = int(path[i][0] * scale_x)
            y = int(path[i][1] * scale_y)
            abs_x, abs_y = hwnd_window.get_abs_cords(x, y)
            logger.debug(f"拖拽到: ({abs_x}, {abs_y})")

            win32api.SetCursorPos((abs_x, abs_y))
            self.sleep(move_delay)

        # 最后：释放鼠标左键
        logger.debug("释放")
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

        logger.info(f"✅ {puzzle_name} 解密完成")
        self.sleep(1)  # 等待游戏响应

    def _load_puzzle_paths(self):
        """从 JSON 文件加载解密路径数据"""
        json_path = os.path.join("mod", "builtin", "puzzle_paths.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"✓ 成功加载解密路径数据: {json_path}")
                return data.get("paths", {})
        except FileNotFoundError:
            logger.error(f"✗ 解密路径文件不存在: {json_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error("✗ 解密路径 JSON 解析失败", e)
            return {}
        except Exception as e:
            logger.error("✗ 加载解密路径失败", e)
            return {}
        
    
    def log_puzzle_info(self, box):
        """输出检测到的拼图信息"""
        logger.info(f"🔍 检测到 {box.name}")
        logger.info(f"  - 置信度: {box.confidence:.3f}")

        # 绘制检测框
        self.draw_boxes(box.name, box, "green")
