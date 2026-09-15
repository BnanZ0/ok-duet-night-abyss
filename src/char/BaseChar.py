import time
from typing import Any  # noqa
from ok import Logger

class BaseChar:
    def __init__(self, task, char_name=None):
        self.task = task
        self.char_name = char_name
        self.last_perform = 0
        self.sleep_adjust = 0
        self.logger = Logger.get_logger(self.name)

    @property
    def name(self):
        """获取角色类名作为其名称。

        Returns:
            str: 角色类名字符串。
        """
        return f"{self.__class__.__name__}"

    def perform(self):
        """执行角色的主要操作逻辑。"""
        self.last_perform = time.time()
        self.do_perform()

    def do_perform(self):
        """执行角色的标准战斗行动。"""
        # self.click_liberation(con_less_than=1)
        # if self.click_resonance()[0]:
        #     return self.switch_next_char()
        # if self.click_echo():
        #     return self.switch_next_char()
        self.continues_normal_attack(10)

    def get_ultimate_key(self):
        """获取终结技按键 (代理到 task.get_ultimate_key)。"""
        return self.task.get_ultimate_key()

    def get_geniemon_key(self):
        """获取魔灵支援按键 (代理到 task.get_geniemon_key)。"""
        return self.task.get_geniemon_key()

    def get_combat_key(self):
        """获取战技按键 (代理到 task.get_combat_key)。"""
        return self.task.get_combat_key()
    
    def send_combat_key(self, after_sleep=0, interval=-1, down_time=0.01):
        """发送战技按键。

        Args:
            after_sleep (float, optional): 发送后的休眠时间。默认为 0。
            interval (float, optional): 按键按下和释放的间隔。默认为 -1 (使用默认值)。
            down_time (float, optional): 按键按下的持续时间。默认为 0.01。
        """
        self._combat_available = False
        self.task.send_key(self.get_combat_key(), interval=interval, down_time=down_time, after_sleep=after_sleep)


    def send_combat_key_with_ctrl(self, after_sleep=0):        
        """发送 Ctrl + 战技组合键 (Ctrl+E)。

        Args:
            after_sleep (float, optional): 发送后的休眠时间。默认为 0。
            interval (float, optional): 不适用没保留参数
            down_time (float, optional): 不适用没保留参数
        """

        self._combat_available = False
        
        # 1. 按下 Ctrl (只按不放) - 使用 ok 框架支持的 "CONTROL" 键名
        self.task.send_key_down("CONTROL")
        
        # 2. 稍微等待，确保系统/游戏识别到 Ctrl 已按住 (防止判定为单独按 E)
        # 0.05改为0.4秒，即使卡顿或者30帧也能稳定
        self.sleep(0.4, check_combat=False) 
        
        # 3. 发送战技 (按 E)
        # 直接调用现有的 send_combat_key 方法
        self.send_combat_key()
        
        # 4. 稍微等待，防止释放过快
        self.sleep(0.05, check_combat=False)
        
        # 5. 释放 Ctrl - 使用 ok 框架支持的 "CONTROL" 键名
        self.task.send_key_up("CONTROL")

        # 6. 模拟ok-script，处理后续休眠 
        if after_sleep > 0:
            self.sleep(after_sleep)

    def send_ultimate_key(self, after_sleep=0, interval=-1, down_time=0.01):
        """发送终结技按键。

        Args:
            after_sleep (float, optional): 发送后的休眠时间。默认为 0。
            interval (float, optional): 按键按下和释放的间隔。默认为 -1 (使用默认值)。
            down_time (float, optional): 按键按下的持续时间。默认为 0.01。
        """
        self._ultimate_available = False
        self.task.send_key(self.get_ultimate_key(), interval=interval, down_time=down_time, after_sleep=after_sleep)

    def send_geniemon_key(self, after_sleep=0, interval=-1, down_time=0.01):
        """发送魔灵支援按键。

        Args:
            after_sleep (float, optional): 发送后的休眠时间。默认为 0。
            interval (float, optional): 按键按下和释放的间隔。默认为 -1 (使用默认值)。
            down_time (float, optional): 按键按下的持续时间。默认为 0.01。
        """
        self._geniemon_available = False
        self.task.send_key(self.get_geniemon_key(), interval=interval, down_time=down_time, after_sleep=after_sleep)

    def click(self, *args: Any, **kwargs: Any):
        """执行一次点击操作 (代理到 task.click)。"""
        self.task.click(*args, **kwargs)

    def continues_normal_attack(self, duration, interval=0.1, after_sleep=0):
        """持续进行普通攻击一段时间。

        Args:
            duration (float): 持续时间 (秒)。
            interval (float, optional): 每次攻击的间隔时间。默认为 0.1。
            click_resonance_if_ready_and_return (bool, optional): 如果共鸣技能可用, 是否立即释放并返回。默认为 False。
            until_con_full (bool, optional): 是否持续攻击直到协奏值满。默认为 False。
        """
        start = time.time()
        while time.time() - start < duration:
            self.task.click()
            self.sleep(interval)
        self.sleep(after_sleep)

    def hold_normal_attack(self, duration):
        """长按普通攻击一段时间后松开，也就是重击。

        Args:
            duration (float): 长按的秒数。
        """
        self.task.mouse_down()
        try:
            self.task.sleep(max(0.0, float(duration)))
        finally:
            # 中途抛异常（角色死亡、任务被停止）也必须松开，否则鼠标一直按着
            self.task.mouse_up()

    def sleep(self, sec, check_combat=True):
        """休眠指定时间 (代理到 task.sleep_check_combat)。

        Args:
            sec (float): 休眠秒数。
            check_combat (bool, optional): 是否检查战斗状态。默认为 True。
        """
        if sec > 0:
            self.task.sleep_check_combat(sec + self.sleep_adjust, check_combat=check_combat)