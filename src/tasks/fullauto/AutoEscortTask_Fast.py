from qfluentwidgets import FluentIcon
import time

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.CommissionsTask import CommissionsTask, Mission
from src.tasks.trigger.AutoMazeTask import AutoMazeTask

logger = Logger.get_logger(__name__)

DEFAULT_PA_DELAY = 0.160



class AutoEscortTask_Fast(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动护送任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "黎瑟：超级飞枪80护送（需黎瑟+巧手+协战+远程任意双枪）【需要游戏处于前台】"
        self.description = "注：帧数敏感 掉帧可能会坠机。\n"
        self.description += "请在OK设置里配置螺旋飞跃键位 游戏内设置四项灵敏度0.2 OK已强制0.2灵敏度无需设置\n"
        self.description += "展开查看具体配置\n"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE
        
        self.mapping_pn = {"-": -1, "+": 1}

        self.default_config.update({
            "快速继续挑战": True,
            "我已阅读注意事项并确认配置": False,
            "我已在OK设置里配置螺旋飞跃键位": False,
            "我已在游戏内设置四项灵敏度为0.2": False,
            "装备：黎瑟 + 0精春玦戟 迅捷+10 + 远程任意双枪": False,
            "设置：镜头距离1.3，1080p120帧，最低画质，垂直同步关， 插帧关": False,
            "魔之楔：金色迅捷+10 / 紫色穿引共鸣 / 紫色迅捷蓄势+5 / 紫色迅捷坠击+5（面板攻速2.0）": False,
            "如果路线2撤离撞墙 请设置路线2结算超级跳延迟为-1": False,
            "路线1结算超级跳延迟Offset": 0,
            "路线1结算超级跳延迟+-": "-",
            "路线1结算超级跳角度Offset": 0,
            "路线1结算超级跳角度+-": "-",
            "路线2结算超级跳延迟Offset": 0,
            "路线2结算超级跳延迟+-": "-",
            "路线2结算超级跳角度Offset": 0,
            "路线2结算超级跳角度+-": "-",
            "路线3结算超级跳延迟Offset": 0,
            "路线3结算超级跳延迟+-": "-",
            "路线3结算超级跳角度Offset": 0,
            "路线3结算超级跳角度+-": "-",
            "路线4结算超级跳延迟Offset": 0,
            "路线4结算超级跳延迟+-": "-",
            "路线4结算超级跳角度Offset": 0,
            "路线4结算超级跳角度+-": "-",
        })
        self.config_description.update({
            "我已阅读注意事项并确认配置": "必须勾选才能执行任务！",
            "我已在OK设置里配置螺旋飞跃键位": "必须勾选才能执行任务！",
            "我已在游戏内设置四项灵敏度为0.2": "必须勾选才能执行任务！",
            "装备：黎瑟 + 0精春玦戟 迅捷+10 + 远程任意双枪": "必须勾选才能执行任务！",
            "设置：镜头距离1.3，1080p120帧，最低画质，垂直同步关， 插帧关": "必须勾选才能执行任务！",
            "魔之楔：金色迅捷+10 / 紫色穿引共鸣 / 紫色迅捷蓄势+5 / 紫色迅捷坠击+5（面板攻速2.0）": "必须勾选才能执行任务！",
            "如果路线2撤离撞墙 请设置路线2结算超级跳延迟为-1": "必须勾选才能执行任务！",
            "路线1结算超级跳延迟Offset": "-+ 1",
            "路线1结算超级跳角度Offset": "-+ 5",
            "路线2结算超级跳延迟Offset": "-+ 1",
            "路线2结算超级跳角度Offset": "-+ 5",
            "路线3结算超级跳延迟Offset": "-+ 1",
            "路线3结算超级跳角度Offset": "-+ 5",
            "路线4结算超级跳延迟Offset": "-+ 1",
            "路线4结算超级跳角度Offset": "-+ 5",
        })
        self.config_type["路线1结算超级跳延迟+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线1结算超级跳角度+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线2结算超级跳延迟+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线2结算超级跳角度+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线3结算超级跳延迟+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线3结算超级跳角度+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线4结算超级跳延迟+-"] = {
            "type": "drop_down",
            "options": ["-", "+"],
        }
        self.config_type["路线4结算超级跳角度+-"] = {
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
        }

        self.maze_task = None

    def run(self):
        mouse_jitter_setting = self.afk_config.get("鼠标抖动")
        self.afk_config.update({"鼠标抖动": False})
        sensitivity_switch = self.sensitivity_config.get("Game Sensitivity Switch")
        self.sensitivity_config.update({"Game Sensitivity Switch": True})
        sensitivity_x = self.sensitivity_config.get("X-axis sensitivity")
        self.sensitivity_config.update({"X-axis sensitivity": 0.2})
        sensitivity_y = self.sensitivity_config.get("Y-axis sensitivity")
        self.sensitivity_config.update({"Y-axis sensitivity": 0.2})
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
            self.sensitivity_config.update({"Game Sensitivity Switch": sensitivity_switch})
            self.sensitivity_config.update({"X-axis sensitivity": sensitivity_x})
            self.sensitivity_config.update({"Y-axis sensitivity": sensitivity_y})

    def do_run(self):
        # 检查是否已阅读注意事项
        if not self.config.get("我已阅读注意事项并确认配置", False) or not self.config.get("我已在OK设置里配置螺旋飞跃键位", False) or not self.config.get("我已在游戏内设置四项灵敏度为0.2", False) \
                or not self.config.get("装备：黎瑟 + 0精春玦戟 迅捷+10 + 远程任意双枪", False) \
                or not self.config.get("设置：镜头距离1.3，1080p120帧，最低画质，垂直同步关， 插帧关", False) \
                or not self.config.get("魔之楔：金色迅捷+10 / 紫色穿引共鸣 / 紫色迅捷蓄势+5 / 紫色迅捷坠击+5（面板攻速2.0）", False) \
                or not self.config.get("如果路线2撤离撞墙 请设置路线2结算超级跳延迟为-1", False):
            logger.error("⚠️ 请先阅读注意事项并确认配置！")

            # 使用 info_set 显示详细配置要求
            self.info_set("错误", "未勾选配置确认")
            self.info_set("角色与武器", "使用黎瑟主控，近战武器: 0精春玦戟")
            self.info_set(
                "武器mod(不要携带其他魔之楔)",
                "金色迅捷+10、紫色穿引共鸣、紫色迅捷蓄势+5、紫色迅捷坠击+5",
            )
            self.info_set("武器面板攻速", "面板攻速: 2.0")
            self.info_set("控制设置", "游戏内设置四项灵敏度: 0.2。镜头距离: 1.3")

            self.log_error("请先勾选「我已阅读注意事项并确认配置」")
            return

        self.load_char()
        _start_time = 0
        _count = 0
        _path_end_time = 0  # 路径执行结束时间

        # 初始化统计信息
        self.stats["rounds_completed"] = 0
        self.stats["start_time"] = time.time()
        self.stats["failed_attempts"] = 0
        self.stats["current_phase"] = "准备中"

        # 初始化 UI 显示
        self.info_set("完成轮数", 0)
        self.info_set("失败次数", 0)
        self.info_set("总耗时", "00:00:00")
        self.info_set("当前阶段", "准备中")

        while True:
            if self.in_team():
                if _start_time == 0:
                    _count += 1
                    _start_time = time.time()

                    # 更新阶段
                    self.stats["current_phase"] = "执行初始路径"
                    self.info_set("当前阶段", "执行初始路径")

                    # 先执行初始路径
                    self.execute_escort_path_init()

                    self.sleep(0.800)
                    # 基于 track_point 位置选择后续路径
                    self.stats["current_phase"] = "检测路径"
                    self.info_set("当前阶段", "检测路径")
                    logger.info("检测 track_point 位置，选择护送路径...")
                    selected_path = self.get_escort_path_by_position()
                    logger.info(f"选择的护送路径: {selected_path}")
                    
                    if selected_path is None:
                        logger.warning("路径选择失败，等待退出队伍...")
                        self.stats["failed_attempts"] += 1
                        self.info_set("失败次数", self.stats["failed_attempts"])
                        self.stats["current_phase"] = "重新开始"
                        self.info_set("当前阶段", "重新开始")
                        self.wait_until(
                            lambda: not self.in_team(), time_out=30, settle_time=1
                        )
                        _start_time = 0
                        _path_end_time = 0
                        continue
                    
                    self.stats["current_phase"] = "执行护送路径"
                    self.info_set(
                        "当前阶段", f"执行路径{self.stats.get('selected_path', '?')}"
                    )
                    
                    self.execute_escort_path_cont()
                    
                    self.target_found = False
                    
                    self.execute_escort_path_door_A()
                    if self.target_found:
                        self.execute_escort_path_door_A_exit()
                    else:
                        self.execute_escort_path_door_B()
                        self.execute_escort_path_door_C()
                        if self.target_found:
                            self.execute_escort_path_door_C_exit()
                        else:
                            self.execute_escort_path_door_D()
                            self.execute_escort_path_door_D_exit()
                    
                    self.execute_escort_path_exit()

                    _path_end_time = time.time()
                    self.stats["current_phase"] = "等待结算"
                    self.info_set("当前阶段", "等待结算")
                    logger.info("护送路径执行完毕，等待结算...")

                # 路径执行完成后，检查是否超时（5秒内应该进入结算）
                if _path_end_time > 0:
                    if time.time() - _path_end_time >= 5:
                        logger.warning(
                            "路径执行完成5秒后仍未进入结算，任务超时，重新开始..."
                        )
                        self.give_up_mission()
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
                    self.info_set("完成轮数", self.stats["rounds_completed"])

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
                self.log_info("任务继续")
                self.stats["current_phase"] = "任务继续"
                self.info_set("当前阶段", "任务继续")
                _start_time = 0
                _path_end_time = 0

            self.sleep(0.2)
    
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
        self.execute_mouse_rot_deg(deg_y=15)
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
                self.execute_mouse_rot_deg(deg_x=-2)
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
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
                self.sleep(0.100)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-0.5)
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
                self.execute_mouse_rot_deg(deg_x=13)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
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
                self.sleep(0.100)
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
                self.execute_mouse_rot_deg(deg_x=-22)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.send_key_down(self.get_dodge_key())
                self.sleep(0.050)
                self.send_key_up(self.get_dodge_key())
                self.sleep(0.400)
                self.execute_mouse_rot_deg(deg_x=20)
                self.sleep(0.050)
                self.execute_pa(deg_x=10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=24)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-24)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-15, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
            case 4:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=20)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=1.5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=15)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_y=-15)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.sleep(0.100)
                self.execute_mouse_rot_deg(deg_x=-50, deg_y=-5)
                self.sleep(0.050)
                self.execute_pa(deg_x=-25, deg_y=20)
                self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
    
    def execute_escort_path_door_A(self):
        self.execute_mouse_rot_deg(deg_x=80, deg_y=-12)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.wait_for_interaction()
        
    def execute_escort_path_door_A_exit(self):
        self.execute_mouse_rot_deg(deg_x=-5, deg_y=-33)
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
        self.execute_mouse_rot_deg(deg_x=51, deg_y=-3)
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
        self.execute_pa(deg_y=73)
        self.sleep(DEFAULT_PA_DELAY)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.execute_mouse_rot_deg(deg_y=-43)
        self.sleep(0.600)
        self.wait_for_interaction()
        
    def execute_escort_path_door_C_exit(self):
        self.execute_mouse_rot_deg(deg_x=-21.5)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=10)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=10)
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
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_y=15)
        self.sleep(0.200)
        self.wait_for_interaction()
             
    def execute_escort_path_door_D_exit(self):
        self.execute_mouse_rot_deg(deg_x=100.5, deg_y=15)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_y=-15)
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_x=-50)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=20)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=-40)
        self.sleep(DEFAULT_PA_DELAY)
        self.execute_pa(deg_x=20)
        self.sleep(DEFAULT_PA_DELAY)

    def execute_escort_path_exit(self):
        self.send_key_down(self.get_dodge_key())
        self.sleep(0.050)
        self.send_key_up(self.get_dodge_key())
        self.sleep(0.400)
        self.execute_mouse_rot_deg(deg_x=10)
        self.sleep(0.050)
        self.execute_pa()
        self.sleep(DEFAULT_PA_DELAY)
        self.sleep(0.200)
        self.execute_mouse_rot_deg(deg_x=-10)
        self.sleep(0.050)
        match self.stats.get("selected_path", 1):
            case 1:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_y=-60)
                self.sleep(0.100)
                self.send_key_down(self.get_spiral_dive_key())
                self.sleep(0.050)
                self.send_key_up(self.get_spiral_dive_key())
                self.execute_rhythm_super_jump(deg_x=0.5 + self.config.get("路线1结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线1结算超级跳角度+-","-")), deg_y=45, slide_delay=0.500 + self.config.get("路线1结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线1结算超级跳延迟+-","-")))
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.execute_rhythm_super_jump(deg_y=5, slide_delay=0.240)
            case 2:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=-10, deg_y=-5)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa(deg_x=13, deg_y=7)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(deg_y=-2)
                self.execute_mouse_rot_deg(deg_x=-3)
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.execute_rhythm_super_jump(deg_x=-1 + self.config.get("路线2结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线2结算超级跳角度+-","-")), deg_y=5, slide_delay=0.080 + self.config.get("路线2结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线2结算超级跳延迟+-","-")))
                self.sleep(0.100)
            case 3:
                self.execute_pa(deg_x=10, deg_y=-10)
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_rhythm_super_jump(deg_x=-27, deg_y=10, slide_delay=0.200)
                self.execute_mouse_rot_deg(deg_x=22)
                self.sleep(0.050)
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_x=-4)
                self.sleep(0.050)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.execute_rhythm_super_jump(deg_x=-0.5 + self.config.get("路线3结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线3算超级跳角度+-","-")), deg_y=5, slide_delay=0.160 + self.config.get("路线3结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线3结算超级跳延迟+-","-")))
            case 4:
                self.execute_pa()
                self.sleep(DEFAULT_PA_DELAY)
                self.execute_mouse_rot_deg(deg_y=-60)
                self.sleep(0.100)
                self.send_key_down(self.get_spiral_dive_key())
                self.sleep(0.050)
                self.send_key_up(self.get_spiral_dive_key())
                self.execute_rhythm_super_jump(deg_x=0.5, deg_y=45, slide_delay=0.500)
                self.sleep(0.050)
                self.mouse_down(key="left")
                self.sleep(0.050)
                self.mouse_up(key="left")
                self.sleep(0.200)
                self.execute_mouse_rot_deg(deg_y=-10)
                self.sleep(0.100)
                self.execute_rhythm_super_jump(deg_x=-1 + self.config.get("路线4结算超级跳角度Offset",0.000)*0.100*self.mapping_pn.get(self.config.get("路线4结算超级跳角度+-","-")), deg_y=5, slide_delay=0.260 + self.config.get("路线4结算超级跳延迟Offset",0.000)*0.010*self.mapping_pn.get(self.config.get("路线4结算超级跳延迟+-","-")))
        self.sleep(0.100)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.sleep(0.050)
        self.mouse_down(key="left")
        self.sleep(0.050)
        self.mouse_up(key="left")
        self.sleep(0.600)
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
    
    def get_escort_path_by_position(self):
        """根据 track_point 的位置选择护送路径

        使用 AutoExcavation 的 find_track_point 方法检测当前位置，
        根据坐标与预设点的距离选择最近的路径。

        3840x2160 分辨率下的参考点：
        - 路径1: (1902, 431)
        - 路径2: (1719, 438)
        - 路径3: (2284, 461)
        - 路径4: (2898, 688)

        Returns:
            选择的路径动作列表
        """
        # 定义 1920x1080 分辨率下的参考点
        reference_points = {
            1: (957, 589) ,
            2: (805, 487),
            3: (1254, 538),
            4: (1545, 562),
        }

        # 获取当前分辨率
        current_width = self.width
        current_height = self.height

        # 计算缩放比例
        scale_x = current_width / 1920
        scale_y = current_height / 1080

        # 缩放参考点到当前分辨率
        scaled_points = {}
        for path_id, (x, y) in reference_points.items():
            scaled_points[path_id] = (int(x * scale_x), int(y * scale_y))

        logger.info(
            f"当前分辨率: {current_width}x{current_height}, 缩放比例: {scale_x:.3f}x{scale_y:.3f}"
        )
        logger.info(f"缩放后的参考点: {scaled_points}")

        # 使用 AutoExcavation 的 find_track_point 方法检测位置
        try:
            track_point = self.find_track_point()

            if track_point is None:
                logger.warning("❌ 未检测到 track_point，无法确定路径，重新开始任务...")
                self.give_up_mission()
                return None

            # 获取检测到的坐标（使用中心点）
            detected_x = track_point.x + track_point.width // 2
            detected_y = track_point.y + track_point.height // 2

            logger.info(f"检测到 track_point 位置: ({detected_x}, {detected_y})")

            # 计算到每个参考点的距离
            min_distance = float("inf")
            selected_path = 1

            for path_id, (ref_x, ref_y) in scaled_points.items():
                distance = (
                    (detected_x - ref_x) ** 2 + (detected_y - ref_y) ** 2
                ) ** 0.5
                logger.debug(f"路径{path_id}: 距离 = {distance:.2f}")

                if distance < min_distance:
                    min_distance = distance
                    selected_path = path_id

            logger.info(
                f"✅ 选择路径{selected_path}，距离最近参考点 {min_distance:.2f} 像素"
            )

            # 记录选择的路径
            self.stats["selected_path"] = selected_path
            
            return selected_path

        except Exception as e:
            logger.error("❌ 检测 track_point 时出错，重新开始任务...", e)
            self.give_up_mission()
            return None
    
    def wait_for_interaction(self):
        if not self.target_found:
            ally_interaction = False
            ally_interaction_check_count = 0
            while not ally_interaction and ally_interaction_check_count < 3:
                self.sleep(0.500)
                try:
                    box = self.box_of_screen_scaled(2560, 1440, 850, 360, 1710, 1080, name="find_track_point", hcenter=True)
                    track_point = self.find_track_point(box=box, filter_track_color=True)
                    if track_point is None:
                        logger.info("未检测到 track_point，协战已打开当前门")
                        ally_interaction = True
                        break
                    else:
                        logger.info(f"检测到 track_point 位置: ({track_point.x}, {track_point.y}), 继续执行后续路径")
                except Exception as e:
                        logger.warning("检测 track_point 时出错，忽略目标检测")
                ally_interaction_check_count += 1
                    
            if not ally_interaction:
                self.send_key_down(self.get_interact_key())
                self.sleep(0.050)
                self.send_key_up(self.get_interact_key())
                self.sleep(0.700)
                self.send_key_down(self.get_interact_key())
                self.sleep(0.050)
                self.send_key_up(self.get_interact_key())
                self.sleep(2.000)
                
            try:
                track_point = self.find_track_point(filter_track_color=True)
                if track_point is None:
                    logger.info("未检测到 track_point，已找到目标")
                    self.target_found = True
                else:
                    logger.info(f"检测到 track_point 位置: ({track_point.x}, {track_point.y}), 继续执行后续路径")
            except Exception as e:
                    logger.warning("检测 track_point 时出错，忽略目标检测")

    def execute_mouse_rot_deg(self, deg_x=0, deg_y=0):
        pixels_x = deg_x * 10
        pixels_y = deg_y * 10

        self.move_mouse_relative(pixels_x, pixels_y)
        logger.debug(f"鼠标视角旋转: x={deg_x}度, y={deg_y}度, 像素: ({pixels_x}, {pixels_y})")

    def execute_pa(self, deg_x=0, deg_y=0, rot_delay=0.300):
        self.mouse_down(key="left")
        self.sleep(rot_delay)
        if deg_x != 0 or deg_y != 0:
            self.execute_mouse_rot_deg(deg_x, deg_y)
        self.mouse_up(key="left")
    
    def execute_rhythm_super_jump(self, deg_x=0, deg_y=0, rot_delay=0.200, slide_delay=0.700):
        self.send_key_down("e")
        self.sleep(0.050)
        self.send_key_up("e")
        if deg_x != 0 or deg_y != 0:
            self.execute_mouse_rot_deg(deg_x, deg_y)
        self.sleep(rot_delay)
        self.mouse_down(key="left")
        self.sleep(0.300)
        self.mouse_up(key="left")
        self.sleep(0.150)
        self.mouse_down(key="right")
        self.sleep(slide_delay)
        self.mouse_up(key="right")