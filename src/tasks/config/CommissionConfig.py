from qfluentwidgets import FluentIcon

from ok import Logger
from src.tasks.BaseDNATask import BaseDNATask

logger = Logger.get_logger(__name__)

LETTER_HANDLE_AUTO_SELECT_FIRST = "自动选择第一个密函"
LETTER_HANDLE_START_DIRECTLY = "直接开始"
LETTER_HANDLE_WAIT_USER = "等待用户选择"

LETTER_HANDLE_MODES = [
    LETTER_HANDLE_AUTO_SELECT_FIRST,
    LETTER_HANDLE_START_DIRECTLY,
    LETTER_HANDLE_WAIT_USER,
]

LETTER_REWARD_DEFAULT = "默认选择"
LETTER_REWARD_COUNT_ZERO = "持有数为0"
LETTER_REWARD_COUNT_MIN = "持有数最少"
LETTER_REWARD_COUNT_MAX = "持有数最多"
LETTER_REWARD_WAIT_USER = "等待用户选择"

LETTER_REWARD_PREFERENCES = [
    LETTER_REWARD_DEFAULT,
    LETTER_REWARD_COUNT_ZERO,
    LETTER_REWARD_COUNT_MIN,
    LETTER_REWARD_COUNT_MAX,
    LETTER_REWARD_WAIT_USER,
]

default_config = {
    "委托手册": "不使用",
    "委托手册指定轮次": "",
    "自动处理密函": LETTER_HANDLE_AUTO_SELECT_FIRST,
    "密函奖励偏好": LETTER_REWARD_DEFAULT,
    "自动穿引共鸣": True,
    "自动花弓": True,
}

config_description = {
    "委托手册指定轮次": "范例: 3,5,8",
    "自动处理密函": "密函处理方式：自动选择第一个密函 / 直接开始 / 等待用户选择",
    "密函奖励偏好": "密函奖励选择策略：默认选择 / 持有数为0 / 持有数最少 / 持有数最多 / 等待用户选择",
    "自动穿引共鸣": "在需要时启用触发任务的自动穿引共鸣",
    "自动花弓": "在需要时启用触发任务的自动花弓",
}

config_type = {
    "委托手册": {
        "type": "drop_down",
        "options": ["不使用", "100%", "200%", "800%", "2000%"],
    },
    "自动处理密函": {
        "type": "drop_down",
        "options": LETTER_HANDLE_MODES,
    },
    "密函奖励偏好": {
        "type": "drop_down",
        "options": LETTER_REWARD_PREFERENCES,
    }
}

class CommissionConfig(BaseDNATask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.SETTING
        self.name = "全局任务设定"
        self.description = "不需要按开始"
        self.group_name = "任务设定"
        self.group_icon = FluentIcon.SETTING

        self.default_config.update(default_config)
        self.config_description.update(config_description)
        self.config_type.update(config_type)

        if isinstance(getattr(self, "config", None), dict):
            # 兼容升级
            # 1) 「自动处理密函」旧版为 bool：
            #    True -> 自动选择第一个密函；False -> 等待用户选择。
            # 2) 「密函奖励偏好」旧版使用「不使用」表示默认行为：
            #    不使用 -> 默认选择。
            mode = self.config.get("自动处理密函", default_config["自动处理密函"])
            mode_options = config_type["自动处理密函"]["options"]
            if mode not in mode_options:
                mode_compat_map = {
                    True: LETTER_HANDLE_AUTO_SELECT_FIRST,
                    False: LETTER_HANDLE_WAIT_USER,
                }
                mode = mode_compat_map.get(mode, mode)
                if mode not in mode_options:
                    mode = default_config["自动处理密函"]
            self.config["自动处理密函"] = mode

            reward_pref = self.config.get("密函奖励偏好", default_config["密函奖励偏好"])
            reward_pref_compat_map = {
                "不使用": LETTER_REWARD_DEFAULT,
            }
            reward_pref = reward_pref_compat_map.get(reward_pref, reward_pref)
            if reward_pref not in config_type["密函奖励偏好"]["options"]:
                reward_pref = default_config["密函奖励偏好"]
            self.config["密函奖励偏好"] = reward_pref
