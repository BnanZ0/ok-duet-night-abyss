# 重击（长按左键）技能：配置面、长按动作、全局技能设定的派发
import os
import unittest

from ok import TaskDisabledException
from ok.test.TaskTestCase import TaskTestCase

from src.char.BaseChar import BaseChar
from src.config import config
from src.tasks.AutoSkill import AutoSkill
from src.tasks.config import CommissionSkillConfig

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['en_US', 'es_ES', 'ja_JP', 'ko_KR', 'zh_CN', 'zh_TW']
HEAVY_ATTACK_STRINGS = ["重击", "重击长按时间", "重击按住左键多久(秒)"]


def po_path(lang, name):
    return os.path.join(REPO, 'i18n', lang, 'LC_MESSAGES', name)


def read_po_msgids(lang):
    """极简 .po 读取：只取 msgid -> msgstr，够查这几条文案。

    （不引 polib：它只声明在 pyproject 里，CI 装的是 requirements.txt，导入会直接失败。）
    """
    entries = {}
    msgid = None
    with open(po_path(lang, 'ok.po'), encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith('msgid '):
                msgid = line[len('msgid '):].strip().strip('"')
            elif line.startswith('msgstr ') and msgid is not None:
                entries[msgid] = line[len('msgstr '):].strip().strip('"')
                msgid = None
    return entries


class FakeTask:
    """只记录鼠标动作的假 task（`hold_normal_attack` 只用这三个方法）。"""

    def __init__(self):
        self.events = []

    def mouse_down(self, *args, **kwargs):
        self.events.append('down')

    def mouse_up(self, *args, **kwargs):
        self.events.append('up')

    def sleep(self, seconds):
        self.events.append(('sleep', seconds))


class FakeChar:
    """只记录重击时长的假角色。"""

    def __init__(self):
        self.holds = []
        self.clicks = 0

    def hold_normal_attack(self, duration):
        self.holds.append(duration)

    def click(self, *args, **kwargs):
        self.clicks += 1


class TestHeavyAttackConfig(unittest.TestCase):

    def test_heavy_attack_is_an_option_in_every_skill_slot(self):
        """四个技能槽的下拉都要有「重击」，且紧挨着「普攻」。"""
        options = CommissionSkillConfig.config_type["技能1"]["options"]
        self.assertIn("重击", options)
        self.assertEqual(options.index("重击"), options.index("普攻") + 1)
        for n in range(1, 5):
            self.assertEqual(CommissionSkillConfig.config_type[f"技能{n}"]["options"], options,
                             f"技能{n} 的下拉选项必须和其它槽一致")

    def test_hold_time_is_one_global_config(self):
        """长按时间只有一条全局配置，不是每个技能槽一条。"""
        self.assertEqual(CommissionSkillConfig.default_config["重击长按时间"], 1.5)
        self.assertEqual(CommissionSkillConfig.config_description["重击长按时间"], "重击按住左键多久(秒)")
        hold_keys = [key for key in CommissionSkillConfig.default_config if "长按" in key]
        self.assertEqual(hold_keys, ["重击长按时间"])

    def test_strings_exist_in_every_language(self):
        """新增的用户可见字符串必须六种语言都有，漏一种界面上就会显示中文原文。

        这条给"加了配置忘了跑 i18n"兜底：.po 是源、.mo 才是运行时读的文件，两边都查，
        避免只改 .po 忘了重编译。zh_CN 的 msgstr 故意留空（回落到中文 msgid），
        所以它的 .mo 里本来就只有那些英文 key，只查 .po。
        """
        for lang in LANGS:
            entries = read_po_msgids(lang)
            for msgid in HEAVY_ATTACK_STRINGS:
                self.assertIn(msgid, entries, f'{lang}/ok.po 缺少 {msgid}')
                if lang != 'zh_CN':
                    self.assertTrue(entries[msgid], f'{lang}/ok.po 的 {msgid} 没填翻译')
            if lang == 'zh_CN':
                continue
            with open(po_path(lang, 'ok.mo'), 'rb') as file:
                compiled = file.read()
            for msgid in HEAVY_ATTACK_STRINGS:
                self.assertIn(msgid.encode('utf-8'), compiled,
                              f'{lang}/ok.mo 缺少 {msgid}（.po 改了没重编译？）')
                self.assertIn(entries[msgid].encode('utf-8'), compiled,
                              f'{lang}/ok.mo 里的 {msgid} 不是 .po 里那句（没重编译？）')


class TestHoldNormalAttack(unittest.TestCase):

    def test_hold_presses_waits_then_releases(self):
        """重击 = 按下左键 -> 等长按时间 -> 松开。"""
        task = FakeTask()
        BaseChar(task).hold_normal_attack(1.5)
        self.assertEqual(task.events, ['down', ('sleep', 1.5), 'up'])

    def test_string_duration_is_cast(self):
        """配置控件有时给字符串，也要能读。"""
        task = FakeTask()
        BaseChar(task).hold_normal_attack("1.5")
        self.assertEqual(task.events, ['down', ('sleep', 1.5), 'up'])

    def test_negative_duration_still_presses_and_releases(self):
        """时长配成负数时退化成一次普攻（按下就松），不能把负数丢给 sleep。"""
        task = FakeTask()
        BaseChar(task).hold_normal_attack(-1)
        self.assertEqual(task.events, ['down', ('sleep', 0.0), 'up'])

    def test_button_is_released_when_interrupted(self):
        """中途被打断（角色死亡 / 玩家停任务）也必须松开左键，否则鼠标一直按着。"""
        class BoomTask(FakeTask):
            def sleep(self, seconds):
                self.events.append(('sleep', seconds))
                raise TaskDisabledException()

        task = BoomTask()
        with self.assertRaises(TaskDisabledException):
            BaseChar(task).hold_normal_attack(1.5)
        self.assertEqual(task.events[-1], 'up')

    def test_button_is_released_when_config_is_broken(self):
        """配置是乱码时抛错要抛，但按下过的左键必须先松开。"""
        task = FakeTask()
        with self.assertRaises(ValueError):
            BaseChar(task).hold_normal_attack("不是数字")
        self.assertEqual(task.events, ['down', 'up'])


class TestSkillTickerDispatch(TaskTestCase):
    task_class = AutoSkill

    config = config

    def test_ticker_holds_for_the_configured_time(self):
        """技能槽选「重击」时，ticker 按「重击长按时间」长按左键（不是点一下）。"""
        task = self.task
        char = FakeChar()
        original = {name: getattr(task, name) for name in
                    ('char', 'log_onetime_info', 'sleep')}
        original_config = task.__dict__.get('commission_skill_config')
        try:
            task.commission_skill_config = {
                "技能1": "重击",
                "技能1_释放频率": 5.0,
                "技能1_释放后等待": 0.0,
                "技能2": "不使用",
                "技能3": "不使用",
                "技能4": "不使用",
                "重击长按时间": 1.2,
            }
            task.char = char  # get_current_char 直接返回它
            task.log_onetime_info = lambda *args, **kwargs: None
            task.sleep = lambda seconds: None

            task.skill_tick.reset()  # 重置后第一次 tick 立刻释放
            task.skill_tick()

            self.assertEqual(char.holds, [1.2], '应该按配置的 1.2 秒长按')
            self.assertEqual(char.clicks, 0, '重击不是普攻，不能变成点击')
        finally:
            for name, value in original.items():
                setattr(task, name, value)
            task.__dict__.pop('commission_skill_config', None)
            if original_config is not None:
                task.__dict__['commission_skill_config'] = original_config
