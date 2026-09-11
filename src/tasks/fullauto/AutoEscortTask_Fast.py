from qfluentwidgets import FluentIcon
import time
import numpy as np

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.CommissionsTask import CommissionsTask, Mission

logger = Logger.get_logger(__name__)

DEFAULT_PA_DELAY = 0.160
MOUSE_DEG_TO_PIXELS = 10
TARGET_WHITE_PIXELS_1920_1080 = 1200


class AutoEscortTask_Fast(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动快速护送任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "黎瑟: 超级飞枪80护送（需120帧+黎瑟+春玦戟+弧光百劫/裂魂+巧手+协战）【需要游戏处于前台】"
        self.description = "注: 需求120帧 帧数敏感 掉帧会坠机\n"
        self.description += "请在 OK-DNA 里设置【水平/垂直灵敏度】【射击时水平/垂直灵敏度】【螺旋飞跃按键】\n"
        self.description += "展开查看具体配置"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE
        
        self.mapping_pn = {"-": -1, "+": 1}

        self.default_config.update({
            "快速继续挑战": True,
            "失误截图": True,
            "我已在 OK-DNA 游戏灵敏度设置里配置【游戏内水平/垂直灵敏度】": False,
            "我已在 OK-DNA 游戏灵敏度设置里配置【游戏内射击时水平/垂直灵敏度】": False,
            "我已在 OK-DNA 游戏快捷键设置里配置【螺旋飞跃按键】": False,
            "帧数敏感，如果不能稳120帧，大概率坠机": False,
            "设置: 镜头距离1.3，120帧，最低画质，垂直同步关， 插帧关": False,
            "阵容: 黎瑟 + 春玦戟（0熔/5熔）+ 弧光百劫/裂魂 + 任意协战": False,
            "近战魔之楔:【金色迅捷 0熔 +10 / 5熔 +6】/ 穿引共鸣 / 迅捷蓄势+5 / 迅捷坠击+5（面板攻速2.00/1.99）": False,
            "远程魔之楔:【请勿携带“专注·厚重”】推荐装备金色迅捷+10或任意迅捷（面板攻速1.3~2.0）": False,
            "路线1·4撤离撞门超级跳延迟Offset": 0,
            "路线1·4撤离撞门超级跳延迟-/+": "-",
            "路线1结算超级跳延迟Offset": 0,
            "路线1结算超级跳延迟-/+": "-",
            "路线1结算超级跳角度Offset": 0,
            "路线1结算超级跳角度-/+": "-",
            "路线2结算超级跳延迟Offset": 0,
            "路线2结算超级跳延迟-/+": "-",
            "路线2结算超级跳角度Offset": 0,
            "路线2结算超级跳角度-/+": "-",
            "路线3结算超级跳延迟Offset": 0,
            "路线3结算超级跳延迟-/+": "-",
            "路线3结算超级跳角度Offset": 0,
            "路线3结算超级跳角度-/+": "-",
            "路线4结算超级跳延迟Offset": 0,
            "路线4结算超级跳延迟-/+": "-",
            "路线4结算超级跳角度Offset": 0,
            "路线4结算超级跳角度-/+": "-",
            # "DEBUG_PATH": 0,
            "DEBUG_GATE": 0,
        })
        self.config_description.update({
            "快速继续挑战": "R键快速继续挑战，跳过结算动画。",
            "失误截图": "ok-duet-night-abyss\screenshots 文件夹下保存，重启OK后清空。如成功率较低，长时间使用可以考虑关闭（截图文件可能会过度占用空间）。",
            "我已在 OK-DNA 游戏灵敏度设置里配置【游戏内水平/垂直灵敏度】": "必须勾选才能执行任务！",
            "我已在 OK-DNA 游戏灵敏度设置里配置【游戏内射击时水平/垂直灵敏度】": "必须勾选才能执行任务！",
            "我已在 OK-DNA 游戏快捷键设置里配置【螺旋飞跃按键】": "必须勾选才能执行任务！",
            "帧数敏感，如果不能稳120帧，大概率坠机": "必须勾选才能执行任务！",
            "设置: 镜头距离1.3，120帧，最低画质，垂直同步关， 插帧关": "必须勾选才能执行任务！",
            "阵容: 黎瑟 + 春玦戟（0熔/5熔）+ 弧光百劫/裂魂 + 任意协战": "必须勾选才能执行任务！",
            "近战魔之楔:【金色迅捷 0熔 +10 / 5熔 +6】/ 穿引共鸣 / 迅捷蓄势+5 / 迅捷坠击+5（面板攻速2.00/1.99）":"必须勾选才能执行任务！",
            "远程魔之楔:【请勿携带“专注·厚重”】推荐装备金色迅捷+10或任意迅捷（面板攻速1.3~2.0）": "必须勾选才能执行任务！",
            "路线1·4撤离撞门超级跳延迟Offset": "-/+ 1",
            "路线1·4撤离撞门超级跳延迟-/+": "撤离点自动门前撞墙-不开门+",
            "路线1结算超级跳延迟Offset": "-/+ 1",
            "路线1结算超级跳延迟-/+": "撤离点在落点后-前+",
            "路线1结算超级跳角度Offset": "-/+ 5",
            "路线1结算超级跳角度-/+": "撤离点在落点左-右+",
            "路线2结算超级跳延迟Offset": "-/+ 1",
            "路线2结算超级跳延迟-/+": "撤离点在落点后-前+",
            "路线2结算超级跳角度Offset": "-/+ 5",
            "路线2结算超级跳角度-/+": "撤离点在落点左-右+",
            "路线3结算超级跳延迟Offset": "-/+ 1",
            "路线3结算超级跳延迟-/+": "撤离点在落点后-前+",
            "路线3结算超级跳角度Offset": "-/+ 5",
            "路线3结算超级跳角度-/+": "撤离点在落点左-右+",
            "路线4结算超级跳延迟Offset": "-/+ 1",
            "路线4结算超级跳延迟-/+": "撤离点在落点后-前+",
            "路线4结算超级跳角度Offset": "-/+ 5",
            "路线4结算超级跳角度-/+": "撤离点在落点左-右+",
            # "DEBUG_PATH": "测试用，强制选择路径，0为不强制",
            "DEBUG_GATE": "测试用，强制选择机关，0为不强制",
        })
        self.config_type["路线1·4撤离撞门超级跳延迟-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线1结算超级跳延迟-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线1结算超级跳角度-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线2结算超级跳延迟-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线2结算超级跳角度-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线3结算超级跳延迟-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线3结算超级跳角度-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线4结算超级跳延迟-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线4结算超级跳角度-/+"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }

        self.action_timeout = 10

        # 缓存 GenshinInteraction 实例，避免重复创建
        self._genshin_interaction = None

        # 统计信息
        self.stats = {
            "rounds_completed": 0,  # 完成轮数
            "total_time": 0.0,  # 总耗时
            "start_time": None,  # 开始时间
            "current_phase": "准备中",  # 当前阶段
            "failed_attempts": 0,  # 失败次数（重新开始）
            "selected_path": None,  # 当前选择的路径
            "previous_path": None,  # 上一次选择的路径
            "path_select_fail": 0, # 路径选择失败次数
            "previous_door_count": 0,  # 上一次开门数
            "path_count": [0, 0, 0, 0],
            "path_fail": [0, 0, 0, 0],
            "door_count": [0, 0, 0, 0],
            "door_fail": [0, 0, 0, 0],
        }

        self.maze_task = None

    def run(self):
        mouse_jitter_setting = self.afk_config.get("鼠标抖动")
        self.afk_config.update({"鼠标抖动": False})
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position(save_current_pos=False)
        self.set_check_monthly_card()
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoEscortTask error", e)
            raise
        finally:
            self.afk_config.update({"鼠标抖动": mouse_jitter_setting})

    def do_run(self):
        # 检查是否已阅读注意事项
        if (not self.config.get("我已在 OK-DNA 游戏灵敏度设置里配置【游戏内水平/垂直灵敏度】", False)
            or not self.config.get("我已在 OK-DNA 游戏灵敏度设置里配置【游戏内射击时水平/垂直灵敏度】", False)
            or not self.config.get("我已在 OK-DNA 游戏快捷键设置里配置【螺旋飞跃按键】", False)
            or not self.config.get("帧数敏感，如果不能稳120帧，大概率坠机", False)
            or not self.config.get("设置: 镜头距离1.3，120帧，最低画质，垂直同步关， 插帧关", False)
            or not self.config.get("阵容: 黎瑟 + 春玦戟（0熔/5熔）+ 弧光百劫/裂魂 + 任意协战", False)
            or not self.config.get("近战魔之楔:【金色迅捷 0熔 +10 / 5熔 +6】/ 穿引共鸣 / 迅捷蓄势+5 / 迅捷坠击+5（面板攻速2.00/1.99）", False)
            or not self.config.get("远程魔之楔:【请勿携带“专注·厚重”】推荐装备金色迅捷+10或任意迅捷（面板攻速1.3~2.0）", False)
        ):
            logger.error("⚠️ 请先阅读注意事项并确认配置！")

            # 使用 info_set 显示详细配置要求
            self.info_set("错误", "未勾选配置确认")
            self.log_error("请先阅读并勾选注意事项")
            raise TaskDisabledException

        self.load_char()
        _start_time = 0
        _count = 0
        _path_end_time = 0  # 路径执行结束时间
        
        self.target_found = False
        self.path_str = "N"
        self.door_count = 0
        self.screenshot_frames = []
        self.scaled_path_points = {}
        self.scaled_path_threshold = 50

        # 初始化统计信息
        self.stats["rounds_completed"] = 0
        self.stats["start_time"] = time.time()
        self.stats["failed_attempts"] = 0
        self.stats["current_phase"] = "准备中"
        self.stats["path_select_fail"] = 0
        self.stats["path_count"] = [0, 0, 0, 0]
        self.stats["path_fail"] = [0, 0, 0, 0]
        self.stats["door_count"] = [0, 0, 0, 0]
        self.stats["door_fail"] = [0, 0, 0, 0]

        # 初始化 UI 显示
        self.info_set("完成轮数", "")
        self.info_set("总耗时", "00:00:00")
        self.info_set("当前阶段", "准备中")
        self.update_escort_stats()
        self.info_set("上轮路径", "?")

        while True:
            if self.in_team():
                if _start_time == 0:
                    _count += 1
                    _start_time = time.time()
                    
                    self.target_found = False
                    self.path_str = "N"
                    self.door_count = 0
                    self.screenshot_frames = []
                    self.scaled_path_points = {}
                    self.scaled_path_threshold = 50
                    
                    self.stats["selected_path"] = None

                    # 更新阶段
                    self.stats["current_phase"] = "执行初始路径"
                    self.info_set("当前阶段", "执行初始路径")

                    # 先执行初始路径
                    self.execute_escort_path_init()
                    self.save_frame(name="INIT")

                    self.sleep(0.300)
                    # 基于 track_point 位置选择后续路径
                    self.stats["current_phase"] = "检测路径"
                    self.info_set("当前阶段", "检测路径")
                    logger.info("检测 track_point 位置，选择护送路径...")
                    self.calc_escort_path_by_position_scaled_reference()
                    self.wait_until(
                        lambda: self.get_escort_path_by_position(), time_out=2.000
                    )
                    selected_path = self.stats["selected_path"]
                    logger.info(f"选择的护送路径: {selected_path}")

                    if (selected_path is None
                        or self.config.get("DEBUG_PATH", 0) in [1,2,3,4]
                        and selected_path != self.config.get("DEBUG_PATH", 0)
                    ):
                        self.dump_screenshots()
                        self.give_up_mission()
                        logger.warning("路径选择失败，等待退出队伍...")
                        self.stats["failed_attempts"] += 1
                        self.stats["path_select_fail"] += 1
                        self.stats["current_phase"] = "重新开始"
                        self.stats["previous_path"] = None
                        self.stats["previous_door_count"] = 0
                        self.info_set("上轮路径", f"路径选择失败")
                        self.info_set("当前阶段", "重新开始")
                        self.wait_until(
                            lambda: not self.in_team(), time_out=30, settle_time=1
                        )
                        _start_time = 0
                        _path_end_time = 0
                        continue
                    self.path_str = f"{selected_path}"
                    
                    self.stats["current_phase"] = "执行护送路径"
                    self.info_set("当前阶段", f"执行路径{self.stats.get('selected_path', '?')}")
                    self.stats["path_count"][selected_path-1] += 1
                    
                    # 执行进场路径
                    self.execute_escort_path_cont()
                    self.save_frame(name="CONT-P")
                    
                    # 执行开门路径
                    # 前往门A
                    self.door_count += 1
                    self.execute_escort_path_door_A()
                    self.save_frame(name="GATE-A")
                    if (self.check_target_found() 
                        and self.config.get("DEBUG_GATE", 0) not in [1,2,3,4] 
                        or self.config.get("DEBUG_GATE", 0) == 1
                    ):
                        # 已找到目标 执行门A撤离路径
                        self.execute_escort_path_door_A_exit()
                    else:
                        # 未找到目标 前往门B
                        self.door_count += 1
                        self.execute_escort_path_door_B()
                        self.save_frame(name="GATE-B")
                        if (self.check_target_found() 
                            and self.config.get("DEBUG_GATE", 0) not in [1,2,3,4] 
                            or self.config.get("DEBUG_GATE", 0) == 2):
                            # 已找到目标 前往门C 并执行门C撤离路径
                            # 注：门B撤离路径与门C相同
                            self.execute_escort_path_door_C()
                            self.save_frame(name="GATE-C")
                            self.execute_escort_path_door_C_exit()
                        else:
                            # 未找到目标 前往门C
                            self.door_count += 1
                            self.execute_escort_path_door_C()
                            self.save_frame(name="GATE-C")
                            if (self.check_target_found() 
                                and self.config.get("DEBUG_GATE", 0) not in [1,2,3,4] 
                                or self.config.get("DEBUG_GATE", 0) == 3):
                                # 已找到目标 执行门C撤离路径
                                self.execute_escort_path_door_C_exit()
                            else:
                                # 未找到目标 前往门D
                                self.door_count += 1
                                self.execute_escort_path_door_D()
                                self.save_frame(name="GATE-D")
                                if self.check_target_found():
                                    # 已找到目标 执行门D撤离路径
                                    self.execute_escort_path_door_D_exit()
                                else:
                                    # 未找到目标 继续等待协战开门
                                    self.wait_until(
                                        lambda: self.check_target_found(delay=1.000), time_out=6.000
                                    )
                                    if self.target_found:
                                        # 已找到目标 执行门D撤离路径
                                        self.execute_escort_path_door_D_exit()
                                    else:
                                        self.dump_screenshots()
                                        logger.warning("未找到目标，等待退出队伍...")
                                        self.give_up_mission()
                                        self.stats["failed_attempts"] += 1
                                        self.stats["current_phase"] = "重新开始"
                                        if self.stats.get("selected_path", None) is not None:
                                            self.stats["path_fail"][self.stats.get("selected_path", 1)-1] += 1
                                        self.info_set("上轮路径", f"路径{selected_path} 机关{self.door_count}")
                                        self.info_set("当前阶段", "重新开始")
                                        self.wait_until(
                                            lambda: not self.in_team(), time_out=30, settle_time=1
                                        )
                                        _start_time = 0
                                        _path_end_time = 0
                                        continue

                    # 执行撤离路径
                    self.execute_escort_path_exit()

                    _path_end_time = time.time()
                    self.stats["current_phase"] = "等待结算"
                    self.info_set("当前阶段", "等待结算")
                    if self.door_count > 0:
                        self.stats["door_count"][self.door_count-1] += 1
                    self.stats["previous_path"] = selected_path
                    self.stats["previous_door_count"] = self.door_count
                    self.info_set("上轮路径", f"路径{selected_path} 机关{self.door_count}")
                    logger.info("护送路径执行完毕，等待结算...")

                # 路径执行完成后，检查是否超时（5秒内应该进入结算）
                if _path_end_time > 0:
                    if time.time() - _path_end_time >= 5:
                        self.dump_screenshots()
                        logger.warning(
                            "路径执行完成5秒后仍未进入结算，任务超时，重新开始..."
                        )
                        self.give_up_mission()
                        self.stats["failed_attempts"] += 1
                        self.stats["current_phase"] = "重新开始"
                        if self.stats.get("selected_path", None) is not None:
                            self.stats["path_fail"][self.stats.get("selected_path", 1)-1] += 1
                            if self.door_count > 0:
                                self.stats["door_fail"][self.door_count-1] += 1
                        self.info_set("当前阶段", "重新开始")
                        self.wait_until(
                            lambda: not self.in_team(), time_out=30, settle_time=1
                        )
                        _start_time = 0
                        _path_end_time = 0
            
            if self.config.get("快速继续挑战", False):
                self.send_key(key="r", down_time=0.050)
                self.sleep(0.050)

            _status = self.handle_mission_interface()
            if _status == Mission.START:
                self.wait_until(self.in_team, time_out=30)

                # 完成一轮，更新统计
                if _count > 0:
                    self.stats["rounds_completed"] += 1
                    self.update_escort_stats()

                    # 计算总耗时
                    elapsed_time = time.time() - self.stats["start_time"]
                    hours = int(elapsed_time // 3600)
                    minutes = int((elapsed_time % 3600) // 60)
                    seconds = int(elapsed_time % 60)
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    self.info_set("总耗时", time_str)

                    avg_time = elapsed_time / self.stats["rounds_completed"]

                    logger.info("=" * 50)
                    logger.info(f"✓ 完成第 {self.stats['rounds_completed']} 轮护送")
                    logger.info(f"  总耗时: {time_str}")
                    logger.info(f"  平均每轮: {avg_time:.1f} 秒")
                    logger.info(f"  失败次数: {self.stats['failed_attempts']}")
                    # max_rounds = self.config.get("刷几次", 999)
                    # if max_rounds > 0:
                    #     remaining = max_rounds - self.stats["rounds_completed"]
                    #     logger.info(f"  剩余轮数: {remaining}")
                    logger.info("=" * 50)

                # if _count >= self.config.get("刷几次", 999):
                #     self.sleep(1)
                #     self.open_in_mission_menu()
                #     self.log_info_notify("任务终止")
                #     self.soundBeep()
                #     return
                self.log_info("任务开始")
                self.stats["current_phase"] = "任务开始"
                self.info_set("当前阶段", "任务开始")
                self.sleep(2)
                _start_time = 0
                _path_end_time = 0
            elif _status == Mission.CONTINUE:
                self.wait_until(self.in_team, time_out=30)
                self.update_escort_stats()
                self.log_info("任务继续")
                self.stats["current_phase"] = "任务继续"
                self.info_set("当前阶段", "任务继续")
                _start_time = 0
                _path_end_time = 0

            self.sleep(0.2)
    
    def update_escort_stats(self):
        """更新 UI 数据显示"""
        self.info_set("完成轮数", f"{self.get_success_frac(self.stats['rounds_completed'], self.stats['failed_attempts'])}")
        self.info_set("路径数据", f"路径1: {self.get_success_frac(self.stats['path_count'][0], self.stats['path_fail'][0])}, \
            路径2: {self.get_success_frac(self.stats['path_count'][1], self.stats['path_fail'][1])}, \
            路径3: {self.get_success_frac(self.stats['path_count'][2], self.stats['path_fail'][2])}, \
            路径4: {self.get_success_frac(self.stats['path_count'][3], self.stats['path_fail'][3])}"
        )
        self.info_set("机关数据", f"机关1: {self.get_success_frac(self.stats['door_count'][0], self.stats['door_fail'][0])}, \
            机关2: {self.get_success_frac(self.stats['door_count'][1], self.stats['door_fail'][1])}, \
            机关3: {self.get_success_frac(self.stats['door_count'][2], self.stats['door_fail'][2])}, \
            机关4: {self.get_success_frac(self.stats['door_count'][3], self.stats['door_fail'][3])}"
        )
        
    def get_success_frac(self, count: int, fail: int) -> str:
        """计算成功率"""
        success = (count - fail)
        return f"{success}/{count}"

    def execute_escort_path_init(self):
        """执行护送路径中的初始动作"""
        self.execute_mouse_rot_deg(deg_y=-90)
        self.sleep(0.100)
        self.send_key_down(self.get_spiral_dive_key())
        self.sleep(0.050)
        self.send_key_up(self.get_spiral_dive_key())
        self.sleep(0.700)
        self.execute_rhythm_super_jump(deg_y=30)
        self.sleep(0.050)
        # 黎瑟超级跳后 转视角使用射击时灵敏度
        self.execute_mouse_rot_deg(deg_y=15, use_aim_sensitivity=True)
        self.sleep(0.100)
    
    def execute_escort_path_cont(self):
        match self.stats.get("selected_path", 1):
            case 1:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-10, deg_y=-5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=12, deg_y=7)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(deg_y=-2)
                # 黎瑟超级跳后 转视角使用射击时灵敏度
                self.execute_mouse_rot_deg(deg_x=-2, use_aim_sensitivity=True)
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.save_frame(name="CONT-O")
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=18)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-8)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-0.5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-20, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
            case 2:
                self.execute_pa(deg_y=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-30, deg_y=-15)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=27, deg_y=25)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump()
                # 黎瑟超级跳后 转视角使用射击时灵敏度
                self.execute_mouse_rot_deg(deg_x=13, use_aim_sensitivity=True)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.save_frame(name="CONT-O")
                self.execute_mouse_rot_deg(deg_x=-10)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-0.5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-15, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
            case 3:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-20, deg_y=-15)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=42, deg_y=15)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(slide_delay=0.360)
                # 黎瑟超级跳后 转视角使用射击时灵敏度
                self.execute_mouse_rot_deg(deg_x=-22, use_aim_sensitivity=True)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.save_frame(name="CONT-O")
                self.execute_pa(deg_x=-20, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-20)
                self.sleep(DEFAULT_PA_DELAY)
                self.send_key_down(self.get_dodge_key())
                self.sleep(0.050)
                self.send_key_up(self.get_dodge_key())
                self.sleep(0.400)
                self.execute_mouse_rot_deg(deg_x=15)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.execute_mouse_rot_deg(deg_x=-15)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-15, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
            case 4:
                self.sleep(0.200)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=22)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=19)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.save_frame(name="CONT-O")
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=18)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-8)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-20, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
    
    def execute_escort_path_door_A(self):
        self.execute_mouse_rot_deg(deg_x=80, deg_y=-12)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_y=-5)
        self.sleep(0.050)
        self.wait_for_interaction()
        
    def execute_escort_path_door_A_exit(self):
        self.execute_mouse_rot_deg(deg_x=-5, deg_y=-28)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=15, deg_y=30)
        self.sleep(0.100)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.execute_mouse_rot_deg(deg_x=-15)
        self.sleep(0.600)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-15)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=15)
        self.sleep(DEFAULT_PA_DELAY)
    
    def execute_escort_path_door_B(self):
        self.execute_mouse_rot_deg(deg_x=51, deg_y=2)
        self.sleep(0.050)
        self.execute_pa(deg_y=1)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=13)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.send_key_down(key="w")
        self.sleep(0.600)
        self.send_key_up(key="w")
        self.wait_for_interaction()

    def execute_escort_path_door_C(self):
        self.execute_mouse_rot_deg(deg_x=-68.5, deg_y=-31)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=1)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_y=73.5)
        self.sleep(DEFAULT_PA_DELAY)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.execute_mouse_rot_deg(deg_y=-43.5)
        self.sleep(0.600)
        self.wait_for_interaction()
        
    def execute_escort_path_door_C_exit(self):
        self.execute_mouse_rot_deg(deg_x=-21, deg_y=-2)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_y=2)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=11.5)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=8)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)

    def execute_escort_path_door_D(self):
        self.execute_mouse_rot_deg(deg_x=-52, deg_y=-30)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_mouse_rot_deg(deg_y=45)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_mouse_rot_deg(deg_y=-30)
        self.sleep(0.500)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_y=15)
        self.sleep(0.400)
        self.wait_for_interaction()
             
    def execute_escort_path_door_D_exit(self):
        self.execute_mouse_rot_deg(deg_x=115.5, deg_y=15)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-30,deg_y=-15)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_x=-25)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-5)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-15, deg_y=10)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-10)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=20, deg_y=-10)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)

    def execute_escort_path_exit(self):
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.050)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.400)
        self.execute_mouse_rot_deg(deg_x=10)
        self.sleep(0.050)
        self.execute_pa(deg_y=-8)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_x=-10, deg_y=8)
        self.sleep(0.050)
        self.save_frame(name="EXIT-X")
        match self.stats.get("selected_path", 1):
            case 1:
                self.execute_mouse_rot_deg(deg_y=-20)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.send_key_down(self.get_spiral_dive_key())
                self.sleep(0.050)
                self.send_key_up(self.get_spiral_dive_key())
                self.execute_rhythm_super_jump(
                    deg_x=0.5, deg_y=25, 
                    slide_delay=0.500 + self.config.get("路线1·4撤离撞门超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线1·4撤离撞门超级跳延迟-/+","-"))
                )
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.save_frame(name="EXIT-Y")
                self.execute_rhythm_super_jump(
                    deg_x=0 + self.config.get("路线1结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线1结算超级跳角度-/+","-")), 
                    deg_y=5, slide_delay=0.220 + self.config.get("路线1结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线1结算超级跳延迟-/+","-"))
                )
            case 2:
                self.execute_pa(deg_y=8)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-10, deg_y=-13)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=13, deg_y=7)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(deg_y=-2)
                # 黎瑟超级跳后 转视角使用射击时灵敏度
                self.execute_mouse_rot_deg(deg_x=-3, use_aim_sensitivity=True)
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.save_frame(name="EXIT-Y")
                self.execute_rhythm_super_jump(
                    deg_x=-1 + self.config.get("路线2结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线2结算超级跳角度-/+","-")), 
                    deg_y=5, slide_delay=0.080 + self.config.get("路线2结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线2结算超级跳延迟-/+","-"))
                )
                self.sleep(0.100)
            case 3:
                self.execute_pa(deg_x=20, deg_y=-6.5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(deg_x=-40, deg_y=16.5, slide_delay=0.200)
                self.sleep(0.200)
                self.send_key_down(self.get_dodge_key())
                self.sleep(0.050)
                self.send_key_up(self.get_dodge_key())
                self.execute_mouse_rot_deg(deg_x=25)
                self.sleep(0.200)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_x=-6, deg_y=-20)
                self.sleep(0.050)
                self.save_frame(name="EXIT-Y")
                self.execute_rhythm_super_jump(
                    deg_x=0 + self.config.get("路线3结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线3结算超级跳角度-/+","-")), 
                    deg_y=5, slide_delay=0.080 + self.config.get("路线3结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线3结算超级跳延迟-/+","-"))
                )
            case 4:
                self.execute_mouse_rot_deg(deg_y=-20)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.send_key_down(self.get_spiral_dive_key())
                self.sleep(0.050)
                self.send_key_up(self.get_spiral_dive_key())
                self.execute_rhythm_super_jump(
                    deg_x=0.5, deg_y=25, 
                    slide_delay=0.500 + self.config.get("路线1·4撤离撞门超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线1·4撤离撞门超级跳延迟-/+","-"))
                )
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.save_frame(name="EXIT-Y")
                self.execute_rhythm_super_jump(
                    deg_x=-1 + self.config.get("路线4结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线4结算超级跳角度-/+","-")), 
                    deg_y=5, slide_delay=0.220 + self.config.get("路线4结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线4结算超级跳延迟-/+","-"))
                )
        self.sleep(0.100)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.sleep(0.050)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.sleep(0.600)
        self.save_frame(name="EXIT-Z")
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.050)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.400)
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.050)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.400)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)

    def calc_escort_path_by_position_scaled_reference(self):
        """计算缩放后的 track point 参考点"""
        # 1920x1080 分辨率下的参考点
        reference_points = {
            1: (957, 589) ,
            2: (805, 487),
            3: (1254, 538),
            4: (1545, 562),
        }
        # 像素距离参考阈值
        reference_threshold = 50

        # 获取当前分辨率
        current_width = self.width
        current_height = self.height

        # 计算缩放比例
        scale_x = current_width / 1920
        scale_y = current_height / 1080

        # 缩放参考点到当前分辨率
        self.scaled_path_points = {}
        for path_id, (x, y) in reference_points.items():
            self.scaled_path_points[path_id] = (int(x * scale_x), int(y * scale_y))
        # 缩放参考阈值到当前分辨率
        self.scaled_path_threshold = int(reference_threshold * np.sqrt(scale_x * scale_y))

        logger.info(
            f"当前分辨率: {current_width}x{current_height}, 缩放比例: {scale_x:.3f}x{scale_y:.3f}"
        )
        logger.info(f"缩放后的参考点: {self.scaled_path_points}")
        logger.info(f"缩放后的距离阈值: {self.scaled_path_threshold} 像素")
        
    def get_escort_path_by_position(self, delay=0.100) -> bool:
        """根据 track_point 的位置选择护送路径"""
        # 使用 find_track_point 检测位置
        try:
            self.sleep(delay)
            track_point = self.find_track_point()

            if track_point is None:
                logger.warning("❌ 未检测到 track_point，无法确定路径")
                return False

            detected_x, detected_y = track_point.center()

            logger.info(f"检测到 track_point 位置: ({detected_x}, {detected_y})")

            # 计算到每个参考点的距离
            min_distance = float("inf")
            selected_path = 1

            for path_id, (ref_x, ref_y) in self.scaled_path_points.items():
                distance = (
                    (detected_x - ref_x) ** 2 + (detected_y - ref_y) ** 2
                ) ** 0.5
                logger.debug(f"路径{path_id}: 距离 = {distance:.2f}")

                if distance < min_distance:
                    min_distance = distance
                    selected_path = path_id

            if min_distance > self.scaled_path_threshold:
                logger.warning(f"❌ 距离超过阈值 {self.scaled_path_threshold} 像素，路径选择失败")
                return False

            logger.info(
                f"✅ 选择路径{selected_path}，距离最近参考点 {min_distance:.2f} 像素"
            )

            # 记录选择的路径
            self.stats["selected_path"] = selected_path
            
            return True
        except TaskDisabledException:
            raise
        except Exception as e:
            logger.error("❌ 检测 track_point 时出错", e)
            return False
    
    def wait_for_interaction(self):
        """等待协战与机关交互 超时尝试主控交互"""
        if not self.target_found:
            ally_interaction = False
            ally_interaction_check_count = 0
            while not ally_interaction and ally_interaction_check_count < 3:
                self.sleep(0.500)
                try:
                    box = self.screen_box('ESCORT_TRACK_POINT')
                    track_point = self.find_track_point(box=box, filter_track_color=True)
                    if track_point is None:
                        logger.info(f"未检测到 track_point，协战已打开门{self.door_count}")
                        ally_interaction = True
                        break
                    else:
                        logger.info(f"检测到 track_point 位置: ({track_point.x}, {track_point.y}), 继续等待协战")
                except TaskDisabledException:
                    raise
                except Exception as e:
                        logger.error("检测 track_point 时出错，忽略目标检测", e)
                ally_interaction_check_count += 1
                    
            if not ally_interaction:
                logger.info(f"等待协战超时，尝试主控交互{self.door_count}")
                self.send_key_down(self.get_interact_key())
                self.sleep(0.050)
                self.send_key_up(self.get_interact_key())
                self.sleep(0.500)
                self.send_key_down(self.get_interact_key())
                self.sleep(0.050)
                self.send_key_up(self.get_interact_key())
                self.sleep(2.200)
    
    def check_target_found(self, delay=0.000) -> bool:
        """检测是否已找到目标"""
        # 检查是否找到目标，通过检测目标血条区域的白色像素数量判断
        if not self.target_found:
            self.sleep(delay)

            target_health_bar_box = self.screen_box('ESCORT_TARGET_HP')
            self.draw_boxes("target_health_bar", [target_health_bar_box], color="blue")
            
            logger.debug(f"目标血条检测区域: {target_health_bar_box}")
            target_health_bar_pixels  = self.next_frame()[
                target_health_bar_box.y:target_health_bar_box.y + target_health_bar_box.height,
                target_health_bar_box.x:target_health_bar_box.x + target_health_bar_box.width
            ]
            
            target_white_pixel_count = int(TARGET_WHITE_PIXELS_1920_1080 * self.width / 1920 * self.height / 1080)
            box_white_pixel_count = np.sum(np.all(target_health_bar_pixels >= [250, 250, 250], axis=2))
            logger.debug(f"目标血条区域白色像素阈值: {target_white_pixel_count}")
            logger.debug(f"目标血条区域白色像素数量: {box_white_pixel_count}")

            if box_white_pixel_count > target_white_pixel_count:
                logger.info("检测到目标血条，已找到目标")
                self.save_frame(name="TARGET")
                self.target_found = True
            else:
                logger.info("未检测到目标血条")
            
        return self.target_found

    def execute_mouse_rot_deg(self, deg_x=0, deg_y=0, use_aim_sensitivity=False, debug=True):
        if debug:
            logger.debug(f"鼠标视角旋转: x={deg_x:.1f}, y={deg_y:.1f}")
        pixels_x = deg_x * MOUSE_DEG_TO_PIXELS
        pixels_y = deg_y * MOUSE_DEG_TO_PIXELS

        self.move_mouse_relative(dx=pixels_x, dy=pixels_y, use_aim_sensitivity=use_aim_sensitivity)

    def execute_pa(self, deg_x=0, deg_y=0, rot_delay=0.300):
        logger.debug(f"执行穿引共鸣: 旋转 x={deg_x:.1f}, y={deg_y:.1f}, 长按{rot_delay:.3f}秒")
        self.mouse_down(key="left")
        self.sleep(rot_delay)
        if deg_x != 0 or deg_y != 0:
            self.execute_mouse_rot_deg(deg_x, deg_y, debug=False)
        self.mouse_up(key="left")
    
    def execute_rhythm_super_jump(self, deg_x=0, deg_y=0, rot_delay=0.200, slide_delay=0.700):
        logger.debug(f"执行黎瑟超级跳: 旋转 x={deg_x:.1f}, y={deg_y:.1f}, 延迟{rot_delay:.3f}秒, 滑行{slide_delay:.3f}秒")
        self.send_key_down("e")
        self.sleep(0.050)
        self.send_key_up("e")
        if deg_x != 0 or deg_y != 0:
            self.execute_mouse_rot_deg(deg_x, deg_y, debug=False)
        self.sleep(rot_delay)
        self.mouse_down(key="left")
        self.sleep(0.300)
        self.mouse_up(key="left")
        self.sleep(0.150)
        self.mouse_down(key="right")
        self.sleep(slide_delay)
        self.mouse_up(key="right")
        
    def save_frame(self, name = None):
        """失误截图: 缓存当前帧"""
        if self.config.get("失误截图", True):
            name=f"T{self.stats['rounds_completed']+1}P{self.path_str}G{self.door_count}_{time.strftime('%H.%M.%S', time.localtime(time.time()))}_{name}"
            self.screenshot_frames.append((name, self.next_frame().copy()))

    def dump_screenshots(self):
        """失误截图: 提取缓存帧生成截图"""
        if self.config.get("失误截图", True):
            for (name, frame) in self.screenshot_frames:
                self.screenshot(name=name, frame=frame)
            self.screenshot_frames = []
