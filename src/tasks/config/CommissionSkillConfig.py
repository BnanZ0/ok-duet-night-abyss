from qfluentwidgets import FluentIcon

from ok import Logger
from src.tasks.BaseDNATask import BaseDNATask

logger = Logger.get_logger(__name__)

default_config = {}
config_description = {}
config_type = {}

for n in range(1, 5):
    default_config.update({
        f"技能{n}": "不使用",
        f"技能{n}_释放频率": 5.0,
        f"技能{n}_释放后等待": 0.0,
    })
    config_description.update({
        f"技能{n}_释放频率": "每几秒释放一次技能",
        f"技能{n}_释放后等待": "释放后等待几秒",
    })
    config_type.update({
        f"技能{n}": {
            "type": "drop_down",
            "options": ["不使用", "战技", "Ctrl+战技（赛琪专属）", "终结技", "魔灵支援", "普攻", "重击", "自动苏乙终结技"],
        },
    })

# 重击（长按左键）的时长，所有技能槽共用这一条：释放频率决定循环周期，
# 这里决定周期里按多久。释放频率小于长按时间时就是无缝连续重击。
default_config["重击长按时间"] = 1.5
config_description["重击长按时间"] = "重击按住左键多久(秒)"

class CommissionSkillConfig(BaseDNATask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.SETTING
        self.name = "全局技能设定"
        self.description = "不需要按开始"
        self.group_name = "任务设定"
        self.group_icon = FluentIcon.SETTING
        
        self.default_config.update(default_config)
        self.config_description.update(config_description)
        self.config_type.update(config_type)
