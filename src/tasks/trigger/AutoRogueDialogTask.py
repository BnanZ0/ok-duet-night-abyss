import re

from ok import TriggerTask, Logger
from src.tasks.BaseDNATask import BaseDNATask
from src.scene.DNAScene import DNAScene

logger = Logger.get_logger(__name__)


class AutoRogueDialogTask(BaseDNATask, TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动肉鸽对话"
        self.description = "自动跳过肉鸽对话"
        self.scene: DNAScene | None = None
        self.template_shape = None

    def run(self):
        if self.scene.in_team(self.in_team_and_world):
            return
        if self.template_shape != self.frame.shape[:2]:
            self.init_box()
        rogue_dialogs = self.find_feature("rogue_dialog", box=self.rogue_dialog_box)
        rogue_gift = self.find_feature("rogue_gift", box=self.rogue_dialog_box)
        if (len(rogue_dialogs) == 1 and len(rogue_gift) == 0):
            self.click_box(rogue_dialogs)
        if self.ocr(
                box=self.screen_box('ROGUE_SPACE_TEXT'),
                match=re.compile("space", re.IGNORECASE)):
            self.send_key("space", down_time=3.5)

    def init_box(self):
        self.rogue_dialog_box = self.screen_box('ROGUE_DIALOG')
        self.template_shape = self.frame.shape[:2]
