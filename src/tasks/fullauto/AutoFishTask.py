from qfluentwidgets import FluentIcon
import time
import cv2

from ok import Logger, TaskDisabledException
from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask

logger = Logger.get_logger(__name__)


class AutoFishTask(DNAOneTimeTask, BaseDNATask):
    """AutoFishTask
    无悠闲全自动钓鱼
    """
    BAR_MIN_AREA = 1200
    ICON_MIN_AREA = 70
    ICON_MAX_AREA = 400
    CONTROL_ZONE_RATIO = 0.25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动钓鱼"
        self.description = "无悠闲全自动钓鱼 (原作者: B站无敌大蜜瓜)"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        # 默认配置（会被 configs/AutoFishTask.json 覆盖）
        self.default_config.update({
            "MAX_ROUNDS": 100,
            "END_WAIT_SPACE": 1.0,
            "MAX_START_SEC": 20.0,
            "MAX_FIGHT_SEC": 60.0,
            "MAX_END_SEC": 20.0,
            "发出声音提醒": True,
        })

        # ROI 配置（鱼条和鱼标搜索区域，基于 1920x1080）
        self.roi_fish_bar_and_icon = [1620, 325, 1645, 725]

        # 配置描述（便于GUI显示）
        self.config_description.update({
            "MAX_ROUNDS": "最大轮数",
            "END_WAIT_SPACE": "每轮结束等待时间(秒)",
            "MAX_START_SEC": "开始阶段超时(秒)",
            "MAX_FIGHT_SEC": "溜鱼阶段超时(秒)",
            "MAX_END_SEC": "结束阶段超时(秒)",
            "发出声音提醒": "完成时播放提示音",
        })

        # runtime
        self.stats = {
            "rounds_completed": 0,
            "total_time": 0.0,
            "start_time": None,
            "current_phase": "准备中",
            "chance_used": 0,  # 授渔以鱼使用次数
        }

    def run(self):
        DNAOneTimeTask.run(self)
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoFishTask error", e)
            raise

    def init(self):
        self.stats = {
            "rounds_completed": 0,
            "total_time": 0.0,
            "start_time": None,
            "current_phase": "准备中",
            "chance_used": 0,  # 授渔以鱼使用次数
        }

    def find_fish_cast(self) -> tuple[bool, tuple]:
        """查找 fish_cast 图标（抛竿/收杆），返回 (found, center)"""
        CAST_THRESHOLD = 0.8  # fish_cast 匹配阈值
        fish_box = self.box_of_screen_scaled(3840, 2160, 3147, 1566, 3383, 1797, name="fish_bite")
        box = self.find_one("fish_cast", box=fish_box, threshold=CAST_THRESHOLD) or self.find_one("fish_ease",
                                                                                                  box=fish_box,
                                                                                                  threshold=CAST_THRESHOLD)
        if box:
            return True, (box.x + box.width // 2, box.y + box.height // 2)
        return False, (0, 0)

    def find_fish_bite(self) -> tuple[bool, tuple]:
        """查找 fish_bite 图标（等待鱼上钩），返回 (found, center)"""
        BITE_THRESHOLD = 0.8  # fish_bite 匹配阈值
        fish_box = self.box_of_screen_scaled(
            3840, 2160, 3147, 1566, 3383, 1797, name="fish_bite"
        )
        box = self.find_one("fish_bite", box=fish_box, threshold=BITE_THRESHOLD)
        if box:
            return True, (box.x + box.width // 2, box.y + box.height // 2)
        return False, (0, 0)

    def find_fish_chance(self) -> tuple[bool, tuple]:
        """查找 fish_chance 图标（授渔以鱼），返回 (found, center)"""
        CHANCE_THRESHOLD = 0.8  # fish_chance 匹配阈值
        fish_chance_box = self.box_of_screen_scaled(3840, 2160, 3467, 1797, 3703, 2033, name="fish_chance")
        box = self.find_one("fish_chance", box=fish_chance_box, threshold=CHANCE_THRESHOLD)
        if box:
            return True, (box.x + box.width // 2, box.y + box.height // 2)
        return False, (0, 0)

    def find_bar_and_fish_by_area(self):
        """基于 ROI 找到鱼条和鱼标的区域与面积

        返回：((has_bar, bar_center, bar_rect), (has_icon, icon_center, icon_rect))
        注意：bar_center 和 icon_center 是相对于 ROI 内部的坐标，bar_rect 和 icon_rect 也是
        """

        # 获取 ROI 区域
        box = self.box_of_screen_scaled(1920, 1080, 1620, 325, 1645, 725, name="fish_roi")

        try:
            # frame = self.frame
            # Box 对象使用 x, y, width, height 属性
            # box_x1, box_y1 = box.x, box.y
            # box_x2, box_y2 = box.x + box.width, box.y + box.height
            # box_x1 = max(0, min(box_x1, frame_width - 1))
            # box_y1 = max(0, min(box_y1, frame_height - 1))
            # box_x2 = max(box_x1 + 1, min(box_x2, frame_width))
            # box_y2 = max(box_y1 + 1, min(box_y2, frame_height))
            # roi_img = frame[box_y1:box_y2, box_x1:box_x2]
            frame_height, _ = self.frame.shape[:2]
            res_ratio = frame_height / 1080
            roi_img = box.crop_frame(self.frame)

            # 转换为灰度图
            gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

            # 二值化：提取亮色区域（鱼条和图标都是白色/亮色）
            _, scene_bin = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

            # 查找轮廓
            contours, _ = cv2.findContours(scene_bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            # 收集所有符合最小面积的轮廓
            blobs = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.ICON_MIN_AREA * res_ratio ** 2:
                    blobs.append({"contour": contour, "area": area})

            # 按面积降序排列
            blobs.sort(key=lambda b: b["area"], reverse=True)

            # Debug only
            # output_img = roi_img.copy()
            # colors = [
            #     (0, 0, 255),     # 红
            #     (0, 255, 0),     # 绿
            #     (255, 0, 0),     # 蓝
            #     (0, 255, 255),   # 黄
            #     (255, 0, 255),   # 紫
            #     (255, 255, 0),   # 青
            #     (255, 255, 255), # 白
            # ]
            # for i, blob in enumerate(blobs):
            #     color = colors[i % len(colors)]  # 超过列表长度循环使用
            #     cv2.drawContours(output_img, [blob["contour"]], -1, color, 2)
            # Debug only

            has_bar = has_icon = False
            bar_center = bar_rect = icon_center = icon_rect = None
            bar_area = icon_area = 0.0

            # 查找鱼条（最大的符合条件的轮廓）
            for blob in blobs:
                if blob["area"] > self.BAR_MIN_AREA * res_ratio ** 2:
                    contour = blob["contour"]
                    moments = cv2.moments(contour)
                    if moments["m00"] > 0:
                        has_bar = True
                        bar_area = blob["area"]
                        # 注意：这里是 ROI 内部坐标，不加 box_x1, box_y1
                        bar_center = (
                            int(moments["m10"] / moments["m00"]),
                            int(moments["m01"] / moments["m00"]),
                        )
                        x, y, w, h = cv2.boundingRect(contour)
                        # 矩形也是 ROI 内部坐标
                        bar_rect = (x, y, x + w, y + h)
                    break

            # 查找鱼标（第二大的符合条件的轮廓，排除鱼条）
            for blob in blobs:
                if blob["area"] == bar_area:
                    continue
                if self.ICON_MIN_AREA * res_ratio ** 2 < blob["area"] < self.ICON_MAX_AREA * res_ratio ** 2:
                    contour = blob["contour"]
                    moments = cv2.moments(contour)
                    if moments["m00"] > 0:
                        has_icon = True
                        icon_area = blob["area"]
                        # ROI 内部坐标
                        icon_center = (
                            int(moments["m10"] / moments["m00"]),
                            int(moments["m01"] / moments["m00"]),
                        )
                        x, y, w, h = cv2.boundingRect(contour)
                        icon_rect = (x, y, x + w, y + h)
                    break

            if has_bar:
                zone_ratio = bar_area / box.area()
                if self.CONTROL_ZONE_RATIO <= 0 or abs(
                        zone_ratio - self.CONTROL_ZONE_RATIO) / self.CONTROL_ZONE_RATIO > 0.1:
                    self.CONTROL_ZONE_RATIO = zone_ratio
                    self.log_info(f"set CONTROL_ZONE_RATIO {self.CONTROL_ZONE_RATIO}")

            # Debug only
            # cv2.imshow("Contours", output_img)
            # cv2.waitKey(1)
            # Debug only

            # 更新统计信息
            self.stats.update({
                "last_bar_found": has_bar,
                "last_bar_area": float(bar_area),
                "last_icon_found": has_icon,
                "last_icon_area": float(icon_area),
            })

            return (has_bar, bar_center, bar_rect), (has_icon, icon_center, icon_rect)
        except TaskDisabledException:
            # cv2.destroyAllWindows()
            raise
        except Exception as e:
            logger.error("find_bar_and_fish_by_area error", e)
            return (False, None, None), (False, None, None)

    # ---- phases ----
    def phase_start(self) -> bool:
        cfg = self.config
        self.stats["current_phase"] = "抛竿"
        self.info_set("当前阶段", "抛竿")

        # ensure foreground handled by framework interaction activation
        start_deadline = time.monotonic() + cfg.get("MAX_START_SEC", 20.0)

        has_cast_icon, _ = self.find_fish_cast()
        self.stats["last_cast_icon_found"] = has_cast_icon

        # 检测是否有授渔以鱼机会
        has_chance_icon, _ = self.find_fish_chance()
        if has_chance_icon:
            logger.info("检测到fish_chance（授渔以鱼）-> 按下E键使用授渔以鱼抛竿")
            self.stats["chance_used"] = self.stats.get("chance_used", 0) + 1
            self.info_set("授渔以鱼", self.stats["chance_used"])
            # 上一轮的鱼被用作鱼饵，不计入轮数
            if self.stats["rounds_completed"] > 0:
                self.stats["rounds_completed"] -= 1
                self.info_set("完成轮数", self.stats["rounds_completed"])
                logger.info(f"上一轮的鱼作为鱼饵，轮数调整为: {self.stats['rounds_completed']}")
            self.send_key("e", down_time=0.06)
        elif not has_cast_icon:
            logger.info("开始阶段未找到fish_cast，尝试按空格抛竿并等待fish_bite出现")
            # press space to cast
            self.send_key("space", down_time=0.06)
        else:
            logger.info("找到fish_cast -> 按下空格抛竿")
            self.send_key("space", down_time=0.06)

        logger.info("等待fish_bite出现...")
        ret = self.wait_until(lambda: self.find_fish_bite()[0], time_out=start_deadline, raise_if_not_found=False)
        self.stats["last_bite_icon_found"] = ret
        if ret:
            logger.info("找到fish_bite -> 等待鱼咬钩")
        else:
            logger.info("超时：等待fish_bite出现")
            return False

        # poll_interval = 0.01
        # while time.monotonic() < start_deadline:
        #     has_bite_icon, _ = self.find_fish_bite()
        #     self.stats["last_bite_icon_found"] = has_bite_icon
        #     if has_bite_icon:
        #         logger.info("找到fish_bite -> 等待鱼咬钩")
        #         break
        #     self.sleep(poll_interval)
        # else:
        #     logger.info("超时：等待fish_bite出现")
        #     return False

        # 等待 fish_bite 消失（鱼咬钩了）
        logger.info("等待鱼咬钩...")
        bite_gone_stable_time = 0.5  # 咬钩消失稳定时间
        ret = self.wait_until(lambda: not self.find_fish_bite()[0], time_out=start_deadline,
                              settle_time=bite_gone_stable_time)
        self.stats["last_bite_icon_found"] = not ret
        if not ret:
            logger.info("等待fish_bite消失超时")
            return False
        # absent_start = None
        # while time.monotonic() < start_deadline:
        #     has_bite_icon, _ = self.find_fish_bite()
        #     self.stats["last_bite_icon_found"] = has_bite_icon
        #     if not has_bite_icon:
        #         if absent_start is None:
        #             absent_start = time.monotonic()
        #         elif time.monotonic() - absent_start >= bite_gone_stable_time:
        #             logger.info("fish_bite已消失 -> 鱼咬钩了！")
        #             break
        #     else:
        #         absent_start = None
        #     self.sleep(poll_interval)
        # else:
        #     logger.info("等待fish_bite消失超时")
        #     return False

        # 等待 fish_cast 出现（收杆提示）
        logger.info("等待fish_cast出现（收杆提示）...")
        ret = self.wait_until(lambda: self.find_fish_cast()[0], time_out=start_deadline)
        self.stats["last_cast_icon_found"] = ret
        if ret:
            logger.info("找到fish_cast -> 按下空格收杆，进入溜鱼阶段")
            self.send_key("space", down_time=0.06)
            return True
        # while time.monotonic() < start_deadline:
        #     has_cast_icon, _ = self.find_fish_cast()
        #     self.stats["last_cast_icon_found"] = has_cast_icon
        #     if has_cast_icon:
        #         logger.info("找到fish_cast -> 按下空格收杆，进入溜鱼阶段")
        #         self.send_key("space", down_time=0.06)
        #         return True
        #     self.sleep(poll_interval)

        logger.info("超时：等待fish_cast出现")
        return False

    def phase_fight(self) -> bool:
        cfg = self.config
        self.stats["current_phase"] = "溜鱼"
        self.info_set("当前阶段", "溜鱼")
        logger.info("进入溜鱼阶段...")

        # 硬编码的常量
        BAR_MISSING_TIMEOUT = 2.5  # 鱼条丢失超时
        MERGE_GRACE_SECONDS = 0.20  # 合并宽限时间

        # 运行时状态
        is_holding_space = False
        icon_was_visible_prev = False
        last_known_icon_y_relative = 0.0

        bar_missing_start_time = None
        merge_start_time = None

        def set_hold(target_hold: bool):
            nonlocal is_holding_space
            if target_hold != is_holding_space:
                if target_hold:
                    self.send_key_down("space")
                else:
                    self.send_key_up("space")
                is_holding_space = target_hold
                self.stats["last_hold_state"] = is_holding_space

        try:
            while True:
                now = time.monotonic()
                if now >= time.monotonic() + cfg.get("MAX_FIGHT_SEC", 60.0):
                    logger.info("溜鱼超时")
                    return False

                (has_bar, bar_center, bar_rect), (has_icon, icon_center, icon_rect) = self.find_bar_and_fish_by_area()

                # 记录鱼标相对位置（用于合并处理）
                if has_bar and has_icon:
                    last_known_icon_y_relative = icon_center[1] - bar_center[1]

                # 检查鱼条是否丢失
                if not has_bar:
                    if bar_missing_start_time is None:
                        bar_missing_start_time = now
                    elif now - bar_missing_start_time >= BAR_MISSING_TIMEOUT:
                        logger.info(f"鱼条丢失超过 {BAR_MISSING_TIMEOUT}s -> 溜鱼结束")
                        return True
                else:
                    bar_missing_start_time = None

                # 主控制逻辑：两层控制系统
                if has_bar and bar_rect:
                    bar_top = bar_rect[1]
                    bar_bottom = bar_rect[3]
                    bar_height = bar_bottom - bar_top

                    if bar_height <= 0:
                        bar_height = 1

                    # 计算控制区域边界
                    control_zone_ratio = self.CONTROL_ZONE_RATIO
                    control_height = int(bar_height * control_zone_ratio)
                    control_top = bar_top + control_height
                    control_bottom = bar_bottom - control_height

                    is_merged = has_bar and (not has_icon) and icon_was_visible_prev

                    if has_icon:
                        merge_start_time = None
                        icon_y = icon_center[1]

                        # 简化的两层控制逻辑
                        if icon_y < control_top:
                            # 鱼标在上控制区 -> 按住空格
                            set_hold(True)
                        elif icon_y > control_bottom:
                            # 鱼标在下控制区 -> 松开空格
                            set_hold(False)
                        # else: 鱼标在中立区 -> 保持当前状态（滞回控制）

                    else:
                        # 处理鱼标与鱼条合并的情况
                        if is_merged:
                            if merge_start_time is None:
                                merge_start_time = now
                                self.stats["last_merge_event"] = (f"merged, last_rel={last_known_icon_y_relative:.1f}")
                                # logger.info("检测到合并，处理...")
                            elapsed = now - merge_start_time
                            if elapsed <= MERGE_GRACE_SECONDS:
                                # 根据上次已知的相对位置决定操作
                                if last_known_icon_y_relative < 0:
                                    set_hold(True)
                                else:
                                    set_hold(False)
                        else:
                            merge_start_time = None
                else:
                    set_hold(False)

                icon_was_visible_prev = has_icon

                self.next_frame()

        except TaskDisabledException:
            self.send_key_up("space")
            raise
        finally:
            self.send_key_up("space")

    def phase_end(self) -> bool:
        cfg = self.config
        self.stats["current_phase"] = "收线"
        self.info_set("当前阶段", "收线")

        # wait and press space to collect
        logger.info(f"等待 {cfg.get('END_WAIT_SPACE', 7.0)}s 结束鱼信息展示...")
        self.sleep(cfg.get("END_WAIT_SPACE", 7.0))

        logger.info("收线 (Space)")
        self.send_key("space", down_time=0.06)

        # wait and verify
        confirm_deadline = time.monotonic() + cfg.get("MAX_END_SEC", 20.0)
        while time.monotonic() < confirm_deadline:
            has_cast_icon, _ = self.find_fish_cast()
            has_bite_icon, _ = self.find_fish_bite()
            has_chance_icon, _ = self.find_fish_chance()
            self.stats["last_cast_icon_found"] = has_cast_icon
            self.stats["last_bite_icon_found"] = has_bite_icon
            if has_cast_icon or has_bite_icon or has_chance_icon:
                if has_chance_icon:
                    logger.info("确认已回到挥杆界面（检测到授渔以鱼）")
                else:
                    logger.info("确认已回到挥杆界面")
                return True
            self.send_key("space", down_time=0.06)
            self.sleep(1.0)
        logger.info("结束阶段确认失败")
        return False

    # main run
    def do_run(self):
        cfg = self.config
        max_rounds = cfg.get("MAX_ROUNDS", 1)

        logger.info("=" * 50)
        logger.info("自动钓鱼任务启动，使用 COCO 标注识别")
        logger.info(f"目标轮数: {max_rounds} 轮")
        logger.info("=" * 50)

        # 初始化统计
        self.stats["rounds_completed"] = 0
        self.stats["start_time"] = time.time()
        self.stats["chance_used"] = 0

        # 初始化界面显示
        self.info_set("完成轮数", 0)
        self.info_set("授渔以鱼", 0)
        self.info_set("当前阶段", "准备中")
        self.info_set("目标轮数", max_rounds)

        # main loop: start -> fight -> end
        while True:
            try:
                # 检查是否达到目标轮数（在phase_start之前检查，因为可能会遇到授渔以鱼导致轮数减少）
                if self.stats["rounds_completed"] >= max_rounds:
                    # 需要再执行一次phase_start来检查是否有授渔以鱼
                    # 如果有授渔以鱼，上一轮不计数，需要继续

                    # 临时检查授渔以鱼
                    has_chance_icon, _ = self.find_fish_chance()
                    if has_chance_icon:
                        logger.info("检测到授渔以鱼，上一轮不计数，继续钓鱼...")
                        # 轮数会在phase_start中自动减1
                    else:
                        # 确实完成了目标轮数
                        elapsed_time = time.time() - self.stats["start_time"]
                        hours = int(elapsed_time // 3600)
                        minutes = int((elapsed_time % 3600) // 60)
                        seconds = int(elapsed_time % 60)

                        logger.info("=" * 50)
                        logger.info(f"✓ 已完成目标轮数: {self.stats['rounds_completed']} 轮")
                        logger.info(f"✓ 总耗时: {hours:02d}:{minutes:02d}:{seconds:02d}")
                        if self.stats["rounds_completed"] > 0:
                            avg_time = elapsed_time / self.stats["rounds_completed"]
                            logger.info(f"✓ 平均每轮: {avg_time:.1f} 秒")
                        logger.info("自动钓鱼任务完成！")
                        logger.info("=" * 50)
                        self.soundBeep()
                        break

                if not self.phase_start():
                    self.sleep(1.0)
                    continue
                if not self.phase_fight():
                    self.sleep(1.0)
                    continue
                if not self.phase_end():
                    self.sleep(1.0)
                    continue

                # 完成一轮
                self.stats["rounds_completed"] += 1
                self.info_set("完成轮数", self.stats["rounds_completed"])

                elapsed_time = time.time() - self.stats["start_time"]
                hours = int(elapsed_time // 3600)
                minutes = int((elapsed_time % 3600) // 60)
                seconds = int(elapsed_time % 60)
                avg_time = elapsed_time / self.stats["rounds_completed"]

                # 更新总耗时显示
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.info_set("总耗时", time_str)

                logger.info("=" * 50)
                logger.info(f"✓ 完成第 {self.stats['rounds_completed']} 轮")
                logger.info(f"  总耗时: {hours:02d}:{minutes:02d}:{seconds:02d}")
                logger.info(f"  平均每轮: {avg_time:.1f} 秒")
                remaining = max_rounds - self.stats["rounds_completed"]
                logger.info(f"  剩余轮数: {remaining}")
                logger.info("=" * 50)

                # 继续下一轮
                self.sleep(1.0)
                self.sleep(1.0)
            except TaskDisabledException:
                raise
            except Exception as e:
                logger.error("AutoFishTask fatal", e)
                break
