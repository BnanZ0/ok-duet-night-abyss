from collections import deque
import math
import cv2
import numpy as np
import re

from ok import TriggerTask
from qfluentwidgets import FluentIcon
from src.tasks.BaseDNATask import BaseDNATask

class AutoRouletteTask(BaseDNATask, TriggerTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动解锁轮盘"
        self.description = "随便搞的，基于2k写的其他分辨率要是有问题就不管了，有bug也不用反馈因为拿到巧手后就不维护了(狗头)"
        self.croppe_center = None
        self.mech_number = 0
        self.mech_angle = []
        self.img_croppe = None
        self._unlocked = False

    @property
    def unlocked(self):
        return self._unlocked
        
    def solve_mech_wheel(self, mech_wheel, control):
        """
        使用广度优先搜索 (BFS) 算法解决机械轮盘谜题。

        参数:
        mech_wheel (list): 开关状态的初始列表 (e.g., [True, False, ...])。
        control (list): 控制装置的定义 (e.g., [0, 120, 0])。

        返回:
        list: 如果有解，返回操作位置的序列 (e.g., [4, 1, 0])。
        str: 如果无解，返回一个说明字符串。
        """
        # --- 步骤 1: 解析 control 来确定操作模式 ---
        # 根据您的解释, "60代表相邻", 所以我们用60作为单位长度。
        # control = [0, 120, 0] 意味着触角在相对位置 0 和 120/60 = 2。
        tentacle_relative_pos = [0]
        current_pos = 0
        # 假设 control 总是以0开始和结束
        if len(control) > 1:
            for i in range(1, len(control), 2):
                distance = control[i]
                step = distance // 60  # 计算相对步长
                current_pos += step
                tentacle_relative_pos.append(current_pos)

        num_wheels = len(mech_wheel)

        # --- 步骤 2: （可选）通过奇偶性检查快速判断无解情况 ---
        initial_falses = sum(1 for w in mech_wheel if not w)
        num_tentacles = len(tentacle_relative_pos)
        # 如果目标是0个False(偶数), 而初始是奇数个False, 并且每次操作翻转偶数个开关，则无解。
        if initial_falses % 2 != 0 and num_tentacles % 2 == 0:
            return "此问题无解 (无法从奇数个'False'通过每次翻转偶数个开关达到全'True'状态)。"

        # --- 步骤 3: 设置 BFS ---
        initial_state = tuple(mech_wheel)
        target_state = tuple([True] * num_wheels)

        if initial_state == target_state:
            return []  # 已经完成，无需操作

        # 队列中存储 (当前状态, 到达该状态的操作路径)
        queue = deque([(initial_state, [])])
        # visited集合用来存储已经访问过的状态，防止无限循环
        visited = {initial_state}

        # --- 步骤 4: 执行 BFS 搜索 ---
        while queue:
            current_state, path = queue.popleft()

            # 尝试在每一个可能的位置 (0 到 num_wheels-1) 进行一次操作
            for i in range(num_wheels):
                next_state_list = list(current_state)

                # 根据 control 的模式翻转对应位置的开关
                for rel_pos in tentacle_relative_pos:
                    flip_index = (i + rel_pos) % num_wheels
                    next_state_list[flip_index] = not next_state_list[flip_index]

                next_state = tuple(next_state_list)

                # 如果达到目标状态，返回路径
                if next_state == target_state:
                    return path + [i]

                # 如果是一个未曾访问过的新状态，则加入队列和visited集合
                if next_state not in visited:
                    visited.add(next_state)
                    new_path = path + [i]
                    queue.append((next_state, new_path))

        # 如果队列为空，意味着已经探索了所有可能的状态但仍未找到解
        return "此问题无解"
    
    def get_croppe_img(self):
        len_height_ratio = 0.28
        cx, cy = self.width_of_screen(0.75) , self.height_of_screen(0.5)
        half_len = self.height_of_screen(len_height_ratio)
        x1 = cx - half_len
        y1 = cy - half_len
        x2 = cx + half_len
        y2 = cy + half_len
        frame = self.frame
        img = frame[y1:y2, x1:x2]
        h, w = img.shape[:2]
        self.croppe_center = (w // 2, h // 2)
        self.img_croppe = img

    def ring_mask(self, img, mask_r1_ratio=0.87, mask_r2_ratio=0.96):
        cropped = img
        if cropped is None or cropped.size == 0:
            return 0.0
        h, w = cropped.shape[:2]

        r1 = int(math.floor(0.5 * h * mask_r1_ratio))
        r2 = int(math.ceil(0.5 * h * mask_r2_ratio))
        if r2 <= r1:
            return 0.0

        center = (w // 2, h // 2)
        ring_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(ring_mask, center, r2, 255, -1)
        if r1 > 0:
            cv2.circle(ring_mask, center, r1, 0, -1)
        combined_mask = cv2.bitwise_and(cropped, cropped, mask=ring_mask)

        return combined_mask
    
    def detect_control(self, img):
        lower_white = np.array([160, 160, 160])
        upper_white = np.array([255, 255, 255])
        match_mask = cv2.inRange(img, lower_white, upper_white)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30,30))
        closed_mask = cv2.morphologyEx(match_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return self.find_white_regions(closed_mask)
    
    def add_point_unique(self, white_regions, new_point, min_dist=20):
        """
        white_regions: 已有中心点列表 [(x1,y1),(x2,y2),...]
        new_point: 待加入的点 (cx, cy)
        min_dist: 最小允许距离，小于这个距离就不加入
        """
        for pt in white_regions:
            dist = math.hypot(pt[0] - new_point[0], pt[1] - new_point[1])
            if dist < min_dist:
                return
        white_regions.append(new_point)

    def find_white_regions(self, img, thresh_value=200, min=1000):
        min_area = min / 3840 / 2160 * self.screen_width * self.screen_height
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        _, bw = cv2.threshold(gray, thresh_value, 255, cv2.THRESH_BINARY)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bw)

        white_regions = []

        for i in range(1, num_labels):  # label 0 是背景
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_area:
                continue
            cx, cy = centroids[i]
            self.add_point_unique(white_regions, (int(cx), int(cy)), min_dist=20)

        return white_regions
    
    def draw_rec(self, img, result, color=(0, 255, 0)):
        if type(result) == tuple:
            cx, cy = result[0], result[1]
            size = 10
            cv2.rectangle(img, (cx - size, cy - size), (cx + size, cy + size), color, 2)
            return img
        for p in result:
            cx, cy = p[0], p[1]
            size = 15
            cv2.rectangle(img, (cx - size, cy - size), (cx + size, cy + size), color, 2)
        return img
    
    def get_clockwise_order(self, points):
        """
        判断两点顺时针移动的先后顺序。
        返回顺时针方向第二个点。
        """
        if len(points) != 2:
            return None
        point1, point2 = points[0], points[1]
        cx, cy = self.croppe_center

        def clockwise_angle(p):
            dx = p[0] - cx
            dy = cy - p[1]
            angle = math.degrees(math.atan2(dy, dx))
            if angle < 0:
                angle += 360
            cw_angle = (180 - angle) % 360
            return cw_angle

        a1 = clockwise_angle(point1)
        a2 = clockwise_angle(point2)

        diff = (a2 - a1) % 360

        if 0 < diff <= 180:
            return point1
        else:
            return point2
    
    def angle_bucket(self, points):
        step = 360 / self.mech_number
        result = [True] * self.mech_number

        if len(points) == 0:
            return result
        (cx, cy) = self.croppe_center

        for (x, y) in points:
            dx = x - cx
            dy = cy - y
            
            # atan2返回: 角度0°在 3 点钟方向，逆时针为正。
            angle = np.degrees(np.arctan2(dy, dx))
            if angle < 0:
                angle += 360
            
            # 以 9 点钟方向（180°）为起点，顺时针为正方向
            adj_angle = (180 - angle) % 360
            if adj_angle > 350:
                adj_angle = 360 - adj_angle
            idx = round(adj_angle / step)
            result[idx] = False

        return result
    
    def angle_between_points_from_center(self, points):
        c = self.croppe_center
        (p1, p2) = points
        v1 = np.array([p1[0]-c[0], p1[1]-c[1]])
        v2 = np.array([p2[0]-c[0], p2[1]-c[1]])

        cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1)*np.linalg.norm(v2))
        theta_rad = np.arccos(np.clip(cos_theta, -1.0, 1.0))
        theta_deg = np.degrees(theta_rad)
        return theta_deg

    def get_control(self, control_result):
        if len(control_result) == 2:
            deg = self.angle_between_points_from_center(control_result)
            if 55 < deg < 65:
                control = [0, 60, 0]
            else:
                control = [0, 120, 0]
        else:
            control = [0]
        return control
    
    def get_point_angle(self, point):
        cx, cy = self.croppe_center
        dx = point[0] - cx
        dy = cy - point[1]

        angle = np.degrees(np.arctan2(dy, dx))
        if angle < 0:
            angle += 360

        adj_angle = (180 - angle) % 360
        return adj_angle
    
    def get_control_ang(self):
        self.get_croppe_img()
        img_control = self.get_img_control()
        control_result = self.detect_control(img_control)
        if len(control_result) == 0:
            return -1
        if len(control_result) == 2:
            target_control = self.get_clockwise_order(control_result)
        else:
            target_control = control_result[0]
        ang = self.get_point_angle(target_control)
        return ang
    
    def get_mech_number(self, img):
        min_area = 4500 / 3840 / 2160 * self.screen_width * self.screen_height

        lower_white = np.array([0, 0, 0])
        upper_white = np.array([55, 55, 55])
        match_mask = cv2.inRange(img, lower_white, upper_white)
        thresh_inv = cv2.bitwise_not(match_mask)
        
        if cv2.countNonZero(thresh_inv) == 0:
            return 0
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh_inv)

        black_regions = []

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < min_area:
                continue
            # print(f"尺寸 {area}")
            cx, cy = centroids[i]
            self.add_point_unique(black_regions, (int(cx), int(cy)), min_dist=20)

        return len(black_regions)
    
    def get_img_mech(self):
        if self.img_croppe is None:
            self.get_croppe_img()
        return self.ring_mask(self.img_croppe, 0.87, 0.96)
    
    def get_img_control(self):
        if self.img_croppe is None:
            self.get_croppe_img()
        return self.ring_mask(self.img_croppe, 0.67, 0.75)

    def run(self):
        self._unlocked = False
        if self.scene.in_team(self.in_team_and_world):
            return
        
        if not self.ocr(box=self.screen_box('ROULETTE_SPACE_TEXT'),
                    match=re.compile("space", re.IGNORECASE)):
            return
        else:
            self.sleep(0.1)

        if self.find_one("pick_up_f", box=self.screen_box('ROULETTE_F_SEARCH')) :
            self.sleep(0.5)
            self.send_key("f", after_sleep=1)
            self._unlocked = True
            return
        
        while True:
            self.get_croppe_img()
            img_mech = self.get_img_mech()
            img_control = self.get_img_control()

            mech_result = self.find_white_regions(img_mech)
            self.mech_number = self.get_mech_number(img_mech)
            if self.mech_number == 0:
                return
            self.log_info(f"机械轮盘数量: {self.mech_number}")
            
            self.mech_angle = []
            for i in range(self.mech_number):
                step = 360 / self.mech_number
                self.mech_angle.append(i*step)

            mech_result = self.find_white_regions(img_mech)
            control_result = self.detect_control(img_control)
            mech_wheel = self.angle_bucket(mech_result)
            control = self.get_control(control_result)

            solution = self.solve_mech_wheel(mech_wheel, control)

            self.log_info(f"输入: mech_wheel={mech_wheel}, control={control}")
            self.log_info(f"解答序列: {solution}")
            if type(solution) is str:
                return
            while True:
                ang = self.get_control_ang()
                for idx, value in enumerate(solution[:]):
                    target_ang = self.mech_angle[value]
                    if target_ang - 5 < ang < target_ang + 5:
                        self.send_key("space")
                        solution.pop(idx)
                        break
                if len(solution) == 0:
                    break
                self.next_frame()
            if self.wait_until(self.in_team, time_out=2):
                self._unlocked = True
                break
            else:
                self.screenshot("img_mech", img_mech)
                self.screenshot("img_control", img_control)
