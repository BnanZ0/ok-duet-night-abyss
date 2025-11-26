import time
from typing import Protocol, Callable, Union
import numpy as np
import cv2
import winsound
import win32api
import win32con
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from ok import BaseTask, Box, Logger, color_range_to_bound, run_in_new_thread, og

logger = Logger.get_logger(__name__)
f_black_color = {
    'r': (0, 20),  # Red range
    'g': (0, 20),  # Green range
    'b': (0, 20)  # Blue range
}

class Ticker(Protocol):
    """
    技能循环计时器接口。
    
    这是一个可调用的对象（类似函数），用于控制动作的执行频率，
    并提供了额外的方法来手动干预计时器的状态。
    """
    
    def __call__(self) -> None:
        """
        尝试执行动作（Tick）。
        
        如果距离上次执行的时间超过了设定的间隔（Interval），
        则执行绑定的 Action，并更新最后执行时间。
        """
        ...

    def reset(self) -> None:
        """
        重置计时器状态。
        
        将“上次执行时间”归零。这意味着下一次调用 tick() 时，
        几乎肯定会立即触发动作（视为初次运行）。
        """
        ...

    def touch(self) -> None:
        """
        刷新计时器（将最后执行时间设为当前时间）。
        
        用于“欺骗”计时器刚刚执行过动作。
        效果：强制动作进入冷却，直到经过一个完整的 interval 周期。
        """
        ...

    def start_next_tick(self) -> None:
        """
        重置下一帧的计时起点（同步延迟）。
        
        标记计时器。下一次调用 tick() 时，不会检查间隔，也不会执行动作，
        而是直接将“上次执行时间”对齐到那一刻的时间。
        
        用途：通常用于在手动释放技能后，告诉计时器从下一帧开始重新倒计时。
        """
        ...

class BaseDNATask(BaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_config = self.get_global_config('Game Hotkey Config')  # 游戏热键配置
        self.monthly_card_config = self.get_global_config('Monthly Card Config')
        self.afk_config = self.get_global_config('挂机设置')
        self.old_mouse_pos = None
        self.next_monthly_card_start = 0
        self._logged_in = False
        self.sensitivity_config = self.get_global_config('Game Sensitivity Config')  # 游戏灵敏度配置

    @property
    def f_search_box(self) -> Box:
        f_search_box = self.get_box_by_name('pick_up_f')
        f_search_box = f_search_box.copy(x_offset=-f_search_box.width * 0.2,
                                         width_offset=f_search_box.width * 0.65,
                                         height_offset=f_search_box.height * 8.3,
                                         y_offset=-f_search_box.height * 1.3,
                                         name='search_dialog')
        return f_search_box

    @property
    def thread_pool_executor(self) -> ThreadPoolExecutor:
        return og.my_app.get_thread_pool_executor()

    def in_team(self) -> bool:
        frame = self.frame
        if self.find_one('lv_text', frame=frame, threshold=0.8):
            return True
        # start_time = time.perf_counter()
        mat = self.get_feature_by_name("ultimate_key_icon").mat
        mat2 = self.get_box_by_name("ultimate_key_icon").crop_frame(frame)
        max_area1 = invert_max_area_only(mat)[2]
        max_area2 = invert_max_area_only(mat2)[2]
        result = False
        if max_area1 > 0:
            if abs(max_area1 - max_area2) / max_area1 < 0.15:
                result = True
        # elapsed = time.perf_counter() - start_time
        # logger.debug(f"in_team check took {elapsed:.4f} seconds.")
        return result

    def in_team_and_world(self):
        return self.in_team()

    def ensure_main(self, esc=True, time_out=30):
        self.info_set('current task', 'wait main')
        if not self.wait_until(lambda: self.is_main(esc=esc), time_out=time_out, raise_if_not_found=False):
            raise Exception('Please start in game world and in team!')
        self.info_set('current task', 'in main')

    def is_main(self, esc=True):
        if self.in_team():
            self._logged_in = True
            return True
        if self.handle_monthly_card():
            return True
        # if self.wait_login():
        #     return True
        if esc:
            self.back(after_sleep=1.5)

    def find_start_btn(self, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one('start_icon', threshold=threshold, box=box, template=template)

    def find_cancel_btn(self, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one('cancel_icon', threshold=threshold, box=box, template=template)

    def find_retry_btn(self, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one('retry_icon', threshold=threshold, box=box, template=template)

    def find_quit_btn(self, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one('quit_icon', threshold=threshold, box=box, template=template)

    def find_drop_item(self, rates=2000, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one(f'drop_item_{str(rates)}', threshold=threshold, box=box, template=template)

    def find_not_use_letter_icon(self, threshold: float = 0, box: Box | None = None, template=None) -> Box | None:
        if isinstance(box, Box):
            self.draw_boxes(box.name, box, "blue")
        return self.find_one('not_use_letter', threshold=threshold, box=box, template=template)

    def safe_get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def soundBeep(self, _n=None):
        if hasattr(self, "config") and not self.config.get("发出声音提醒", True):
            return
        if _n is None:
            n = max(1, self.afk_config.get("提示音", 1))
        else:
            n = _n
        run_in_new_thread(
            lambda: [winsound.Beep(523, 150) or time.sleep(0.3) for _ in range(n)]
        )

    def log_info_notify(self, msg):
        self.log_info(msg, notify=self.afk_config['弹出通知'])

    def move_mouse_to_safe_position(self, save_current_pos: bool = True, box: Union[Box, None] = None):
        if self.afk_config["防止鼠标干扰"]:
            self.old_mouse_pos = win32api.GetCursorPos() if save_current_pos else None
            if self.rel_move_if_in_win(0.95, 0.6, box=box):
                self.sleep(0.01)
            else:
                self.old_mouse_pos = None

    def move_back_from_safe_position(self):
        if self.afk_config["防止鼠标干扰"] and self.old_mouse_pos is not None:
            self.sleep(0.01)
            win32api.SetCursorPos(self.old_mouse_pos)
            self.old_mouse_pos = None

    # def sleep(self, timeout):
    #     return super().sleep(timeout - self.check_for_monthly_card())

    def check_for_monthly_card(self):
        if self.should_check_monthly_card():
            start = time.time()
            ret = self.handle_monthly_card()
            cost = time.time() - start
            return ret, cost
            # start = time.time()
            # logger.info(f'check_for_monthly_card start check')
            # if self.in_combat():
            #     logger.info(f'check_for_monthly_card in combat return')
            #     return time.time() - start
            # if self.in_team():
            #     logger.info(f'check_for_monthly_card in team send sleep until monthly card popup')
            #     monthly_card = self.wait_until(self.handle_monthly_card, time_out=120, raise_if_not_found=False)
            #     logger.info(f'wait monthly card end {monthly_card}')
            #     cost = time.time() - start
            #     return cost
        return False, 0

    def should_check_monthly_card(self):
        if self.next_monthly_card_start > 0:
            if 0 < time.time() - self.next_monthly_card_start < 120:
                return True
        return False

    def set_check_monthly_card(self, next_day=False):
        if self.monthly_card_config.get('Check Monthly Card'):
            now = datetime.now()
            hour = self.monthly_card_config.get('Monthly Card Time')
            # Calculate the next 5 o'clock in the morning
            next_four_am = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if now >= next_four_am or next_day:
                next_four_am += timedelta(days=1)
            next_monthly_card_start_date_time = next_four_am - timedelta(seconds=30)
            # Subtract 1 minute from the next 5 o'clock in the morning
            self.next_monthly_card_start = next_monthly_card_start_date_time.timestamp()
            logger.info('set next monthly card start time to {}'.format(next_monthly_card_start_date_time))
        else:
            self.next_monthly_card_start = 0
            logger.info('set next monthly card start to {}'.format(self.next_monthly_card_start))

    def handle_monthly_card(self):
        monthly_card = self.find_one('monthly_card', threshold=0.8)
        if not hasattr(self, '_last_monthly_card_check_time'):
            self._last_monthly_card_check_time = 0
        now = time.time()
        if now - self._last_monthly_card_check_time >= 10:
            self._last_monthly_card_check_time = now
            self.screenshot('monthly_card1')
        ret = monthly_card is not None
        if ret:
            self.wait_until(self.in_team, time_out=10,
                            post_action=lambda: self.click_relative(0.50, 0.89, after_sleep=1))
            self.set_check_monthly_card(next_day=True)
        logger.info(f'check_monthly_card {monthly_card}, ret {ret}')
        return ret

    def find_track_point(self, threshold: float = 0, box: Box | None = None, template=None, frame_processor=None,
                         mask_function=None, filter_track_color=False) -> Box | None:
        frame = None
        if box is None:
            box = self.box_of_screen_scaled(2560, 1440, 454, 265, 2110, 1094, name="find_track_point", hcenter=True)
        # if isinstance(box, Box):
        #     self.draw_boxes(box.name, box, "blue")
        if filter_track_color:
            if template is None:
                template = self.get_feature_by_name("track_point").mat
            template = color_filter(template, track_point_color)
            frame = color_filter(self.frame, track_point_color)
        return self.find_one("track_point", threshold=threshold, box=box, template=template, frame=frame,
                             frame_processor=frame_processor, mask_function=mask_function)

    def is_mouse_in_window(self) -> bool:
        """
        检测鼠标是否在游戏窗口范围内。

        Returns:
            bool: 如果鼠标在窗口内则返回 True，否则返回 False。
        """
        mouse_x, mouse_y = win32api.GetCursorPos()
        hwnd_window = og.device_manager.hwnd_window
        win_x = hwnd_window.x - (hwnd_window.window_width - hwnd_window.width)
        win_y = hwnd_window.y - (hwnd_window.window_height - hwnd_window.height)

        return (win_x <= mouse_x < win_x + hwnd_window.window_width) and \
            (win_y <= mouse_y < win_y + hwnd_window.window_height)
    
    def is_mouse_in_box(self, box: Box) -> bool:
        """
        检测鼠标是否在给定的 Box 内。

        Args:
            box (Box): 给定的 Box。

        Returns:
            bool: 如果鼠标在 Box 内则返回 True，否则返回 False。
        """
        if not isinstance(box, Box):
            return True
        mouse_x, mouse_y = win32api.GetCursorPos()
        hwnd_window = og.device_manager.hwnd_window
        coords = [
            (box.x, box.y),
            (box.x + box.width, box.y + box.height)
        ]
        (x1, y1), (x2, y2) = [hwnd_window.get_abs_cords(x, y) for x, y in coords]
        return x1 <= mouse_x < x2 and y1 <= mouse_y < y2

    def rel_move_if_in_win(self, x=0.5, y=0.5, box=None):
        """
        如果鼠标在窗口内，则将其移动到游戏窗口内的相对位置。

        Args:
            x (float): 相对 x 坐标 (0.0 到 1.0)。
            y (float): 相对 y 坐标 (0.0 到 1.0)。
        """
        if not self.is_mouse_in_window() or not self.is_mouse_in_box(box=box):
            return False
        abs_pos = self.executor.device_manager.hwnd_window.get_abs_cords(self.width_of_screen(x),
                                                                         self.height_of_screen(y))
        win32api.SetCursorPos(abs_pos)
        return True

    def create_ticker(self, action: Callable, interval: Union[float, int, Callable] = 1.0) -> Ticker:
        last_time = 0
        armed = False

        def get_interval():
            if callable(interval):
                return interval()
            if hasattr(interval, "value"):
                return interval.value
            return float(interval)

        def tick():
            nonlocal last_time, armed
            now = time.perf_counter()

            if armed:
                last_time = now
                armed = False
                return

            current_interval = get_interval()

            if now - last_time >= current_interval:
                last_time = now
                action()

        def reset():
            nonlocal last_time
            last_time = 0

        def touch():
            nonlocal last_time
            last_time = time.perf_counter()

        def start_next_tick():
            nonlocal armed
            armed = True

        tick.reset = reset
        tick.touch = touch
        tick.start_next_tick = start_next_tick
        return tick

    def get_interact_key(self):
        """获取交互的按键。

        Returns:
            str: 交互的按键字符串。
        """
        return self.key_config['Interact Key']

    def get_dodge_key(self):
        """获取闪避的按键。

        Returns:
            str: 闪避的按键字符串。
        """
        return self.key_config['Dodge Key']

    def get_spiral_dive_key(self):
        """获取螺旋飞跃的按键。

        Returns:
            str: 螺旋飞跃的按键字符串。
        """
        return self.key_config['HelixLeap Key']
    
        
    def calculate_sensitivity(self, original_Xsensitivity, original_Ysensitivity, dx, dy):
        """计算玩家水平鼠标移动值和垂直鼠标移动值

        Returns:
            int: 玩家水平鼠标移动值
            int: 玩家垂直鼠标移动值

        """
        # 获取设置中的游戏灵敏度
        game_Xsensitivity = round(self.sensitivity_config['X-axis sensitivity'], 1)
        game_Ysensitivity = round(self.sensitivity_config['Y-axis sensitivity'], 1)

        # 判断和计算
        if original_Xsensitivity == game_Xsensitivity and original_Ysensitivity == game_Ysensitivity:
            calculate_dx = dx
            calculate_dy = dy
        else:
            calculate_dx = dx / round(game_Xsensitivity / original_Xsensitivity, 10)
            calculate_dy = dy / round(game_Ysensitivity / original_Ysensitivity, 10)
        
        return calculate_dx, calculate_dy

    def try_bring_to_front(self):
        if not self.hwnd.is_foreground():
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            self.hwnd.bring_to_front()
            self.sleep(0.5)

track_point_color = {
    "r": (121, 255),  # Red range
    "g": (116, 255),  # Green range
    "b": (34, 211),  # Blue range
}

lower_white = np.array([244, 244, 244], dtype=np.uint8)
lower_white_none_inclusive = np.array([243, 243, 243], dtype=np.uint8)
upper_white = np.array([255, 255, 255], dtype=np.uint8)
black = np.array([0, 0, 0], dtype=np.uint8)


def isolate_white_text_to_black(cv_image):
    """
    Converts pixels in the near-white range (244-255) to black,
    and all others to white.
    Args:
        cv_image: Input image (NumPy array, BGR).
    Returns:
        Black and white image (NumPy array), where matches are black.
    """
    match_mask = cv2.inRange(cv_image, black, lower_white_none_inclusive)
    output_image = cv2.cvtColor(match_mask, cv2.COLOR_GRAY2BGR)

    return output_image


def color_filter(img, color):
    lower_bound, upper_bound = color_range_to_bound(color)
    mask = cv2.inRange(img, lower_bound, upper_bound)
    img_modified = img.copy()
    img_modified[mask == 0] = 0
    return img_modified


def invert_max_area_only(mat):
    # 转灰度并二值化
    gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

    # 连通组件分析
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)

    # 找最大连通区域（排除背景）
    areas = stats[1:, 4]
    if len(areas) == 0:
        return None, None, 0
    # max_area = np.max(areas)
    max_idx = np.argmax(areas) + 1

    # 生成只包含最大区域的掩码
    max_region = (labels == max_idx).astype(np.uint8) * 255

    # 对这个区域做黑白反转，其他部分全部置为0
    inverted_region = 255 - max_region

    # 再计算反转后的最大白色区域（一般只有一块）
    num_labels2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(inverted_region)
    areas2 = stats2[1:, 4]
    if len(areas2) == 0:
        return None, None, 0
    max_area2 = np.max(areas2)
    max_idx2 = np.argmax(areas2) + 1

    # 提取最终掩码
    final_mask = (labels2 == max_idx2).astype(np.uint8) * 255

    return inverted_region, final_mask, max_area2
