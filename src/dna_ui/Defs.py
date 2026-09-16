"""ui/Defs.py — 界面判据与点击坐标的唯一出处。

1. label 只回答"我在哪个界面"，命中后点哪里一律走 `COORD` 固定坐标。
2. 判据只在**自己的流程位置**被调用，不要求在任何页面都能区分。
3. 坐标以 1600x900 为基准，运行期由框架按实际分辨率缩放。

用法：
    box = self.find_ui(Ui.RESET_CONFIRM_OK)        # 找判据（返回 Box 或 None）
    self.click_ui_coord(COORD.RESET_TRANSPORT_OK)  # 按坐标点
"""

REF_WIDTH = 1600
REF_HEIGHT = 900


class Ui:
    """界面判据 label 名。"""
    START_SCREEN_START = 'start_screen_start_btn'
    START_SCREEN_START_2 = 'start_screen_start_btn2'
    MANUAL_SELECT_NOT_USE = 'manual_select_not_use'
    ACTION_DIALOG_RETREAT = 'action_dialog_retreat'
    ACTION_DIALOG_CONTINUE = 'action_dialog_continue'
    ACTION_DIALOG_CONTINUE_2 = 'action_dialog_continue2'
    LETTER_SELECT_NOT_USE = 'letter_select_not_use'
    LETTER_REWARD_CONFIRM = 'letter_reward_confirm'
    ESC_MENU_SETTINGS = 'esc_menu_settings'
    RESET_CONFIRM_OK = 'reset_confirm_ok'
    RESULT_AGAIN_BTN = 'result_again_btn'


# label -> (搜索框 (x0,y0,x1,y1), 判据界面名, 说明)
# 搜索框覆盖该判据在所有应命中截图上的实测位置（含内容多一行导致的整体位移）。
DISCRIMINATORS = {
    Ui.START_SCREEN_START: (
        (1262, 780, 1322, 850), 'start_screen',
        '开始/选择密函 按钮左侧 ◯ 图标 -> 开始界面（6 个入口共用，含"多一行内容"的 10px 下移）'),
    Ui.START_SCREEN_START_2: (
        (948, 781, 996, 837), 'start_screen',
        '另一套开始界面布局的 ◯ 图标（x963,y796）-> 开始界面；图标与 START_SCREEN_START 同一个，只是位置不同'),
    Ui.MANUAL_SELECT_NOT_USE: (
        (497, 362, 590, 456), 'manual_select',
        '委托手册弹窗第 1 槽 ⊘ 图标 -> 委托手册弹窗（双按钮/单按钮两套布局都有）'),
    Ui.ACTION_DIALOG_RETREAT: (
        (486, 592, 560, 645), 'action_dialog',
        '「撤离」绿色门形图标 -> 行动抉择弹窗（3 个模式共用同一布局）'),
    Ui.ACTION_DIALOG_CONTINUE: (
        (998, 594, 1075, 650), 'action_dialog',
        '「继续挑战」金色 ◯ 图标 -> 行动抉择弹窗（常规布局：探险 / 扼守 / 密函）'),
    Ui.ACTION_DIALOG_CONTINUE_2: (
        (999, 535, 1073, 588), 'action_dialog',
        '「继续挑战」金色 ◯ 图标 -> 行动抉择弹窗（灾厄模式那套，比常规布局上移 59px；'
        '单独一条标注方便版本更新后核对 UI 变化）'),
    Ui.LETTER_SELECT_NOT_USE: (
        (720, 340, 810, 465), 'letter_select',
        '卡牌矩阵第 1 格 ⊘ 图标 -> 密函选择（两套布局位置相同，是主判据）'),
    Ui.LETTER_REWARD_CONFIRM: (
        (665, 720, 730, 775), 'letter_reward',
        '「确认选择」按钮左侧 ◯ 图标 -> 密函奖励'),
    Ui.ESC_MENU_SETTINGS: (
        (1129, 780, 1215, 850), 'esc_menu',
        '「设置」齿轮图标 -> 局内 ESC 菜单（右下 4 按钮之一）'),
    Ui.RESET_CONFIRM_OK: (
        (815, 495, 875, 560), 'reset_confirm',
        '「确定」按钮左侧金色 ◯ 图标 -> 重置位置二次确认弹窗'),
    Ui.RESULT_AGAIN_BTN: (
        (1027, 769, 1099, 835), 'result',
        '「再次进行」按钮左侧金色环形图标 -> 任务结算（5 张结算界面位置一致）'),
}


class SCREEN_BOX:
    """非判据用途的搜索框，集中维护，各自保留原作者写的基准。

    格式：(原始宽, 原始高, x0, y0, x1, y1, hcenter)。运行期按实际分辨率自动缩放，
    所以基准是多少都不影响正确性。判据的搜索框在 `DISCRIMINATORS` 里。

    `hcenter` 是框架 `box_of_screen_scaled` 的同名参数：True 时该右侧元素从右边缘
    量边距，False 时从左边量。**必须逐框保留原作者的值** —— 16:9 分辨率下两者结果
    相同，换了比例就会偏移。目前只有 FISH_CHANCE 是 False。
    """

    # ---- 委托流程 ----
    REWARD_DRAG_AREA = (2560, 1440, 69, 969, 2498, 1331, True)      # start_mission 鼠标安全区
    # 轮次数字 OCR：新版 HUD 在左上角，数字在 x172-190 / y245-268
    ROUND_INFO_OCR = (1600, 900, 170, 240, 230, 275, True)
    SETTING_OTHER_TAB = (1600, 900, 500, 0, 620, 60, True)          # 设置「其他」页签
    # 「复位角色」：深色条 + 浅灰文字，没有可裁图形，整条都是可点范围。
    # 同时兼作点击前的鼠标安全范围（框架里这是闸门，鼠标不在框内就不做安全移动）
    RESET_CHARACTER_AREA = (1600, 900, 1166, 606, 1469, 642, True)
    RESET_OK_SAFE_BOX = (2560, 1440, 1298, 772, 1735, 846, True)    # 点「确定」前鼠标允许停留的范围

    # ---- HUD（新截图 1600×900）----
    SERUM_ICON = (1600, 900, 18, 322, 68, 394, True)                # 血清水滴图标
    ULTIMATE_KEY_ICON = (1600, 900, 1404, 810, 1474, 858, True)     # 右下角 Q 终结技键
    # 沉浸式戏剧左上目标栏那颗菱形：金 = 未开战、红 = 已开战。
    # 「已开战」按颜色判（金/红形状一样，只有颜色不同）。位置优先用菱形模板，模板没匹上时
    # 退回这个固定框兜底 —— 亮场景那颗菱形模板分只有 0.802，压着 0.8 的阈值。
    # 红色占比实测（阈值 0.15）：金 0.000 / 红 0.23(亮场景)~0.26(暗场景)。
    THEATRE_OBJECTIVE_DIAMOND = (1600, 900, 37, 268, 58, 291, True)

    # ---- 密函选择 ----
    # 拖拽/鼠标安全区：相对框 (0.4432,0.3556)-(0.9750,0.6037)，按 1600×900 展开
    LETTER_DRAG_AREA = (1600, 900, 709, 320, 1560, 543, True)

    # ---- 大世界 / 追踪 ----
    FIND_TRACK_POINT = (2560, 1440, 454, 265, 2110, 1094, True)     # track_point 搜索区
    HEDGE_PROCESS_INFO = (3840, 2160, 12, 494, 637, 1002, True)     # 避险进度信息
    HEDGE_TRACK_POINT = (2560, 1440, 2183, 82, 2414, 140, True)     # 避险右上角追踪点

    # ---- 勘察 / 护送 ----
    HEALTH_BAR = (2560, 1440, 91, 512, 303, 525, True)              # 勘察目标血条
    ESCORT_TRACK_POINT = (2560, 1440, 850, 360, 1710, 1080, True)   # 护送追踪点
    ESCORT_TARGET_HP = (1920, 1080, 38, 401, 284, 426, True)        # 护送目标血条

    # ---- 范围外（钓鱼 / 迷宫 / 肉鸽 / 轮盘），保留原作者基准，待重做 ----
    FISH_CHANCE = (3840, 2160, 3269, 1672, 3505, 1908, False)       # 原作者没传 hcenter -> False
    MAZE_MECH_RETRY_A = (2560, 1440, 2287, 1006, 2414, 1132, True)
    MAZE_MECH_RETRY_B = (3840, 2160, 3367, 1632, 3548, 1811, True)
    MAZE_PUZZLE = (3840, 2160, 2336, 604, 3307, 1578, True)
    ROGUE_DIALOG = (2560, 1440, 1504, 854, 1555, 1224, True)
    ROGUE_SPACE_TEXT = (2560, 1440, 2092, 1380, 2183, 1418, True)
    ROULETTE_SPACE_TEXT = (2560, 1440, 1878, 736, 1963, 769, True)
    ROULETTE_F_SEARCH = (2560, 1440, 2275, 1235, 2365, 1315, True)

    # ---- 全屏 ----
    FULL_SCREEN = (2560, 1440, 1, 1, 2559, 1439, True)


# 密函奖励的两组区域（1600x900 基准），下标顺序都对应第 1/2/3 个奖励：
#   REWARD_COUNT_BOX    「持有数：N」的 OCR 区域
#   REWARD_SELECTED_BOX 「选中指示器 ✔」的搜索区域（判断点击有没有生效）
# 点击位置不在这里，仍是 COORD.LETTER_REWARD_CARD_*。
REWARD_COUNT_BOX = (
    (512, 580, 636, 606),
    (743, 579, 864, 607),
    (971, 579, 1096, 606),
)

REWARD_SELECTED_BOX = (
    (542, 610, 610, 651),
    (779, 606, 833, 652),
    (1005, 607, 1065, 653),
)


class COORD:
    """点击坐标（1600x900 基准）。判据负责"认界面"，这里负责"点哪里"。"""

    # ---- 开始界面 ----
    START_SCREEN_BTN = (1291, 820)

    # ---- 委托手册弹窗（点哪一格由配置决定）----
    MANUAL_NOT_USE = (543, 409)
    MANUAL_ITEM = {
        '100%': (674, 394),
        '200%': (804, 394),
        '800%': (934, 394),
        '2000%': (1064, 394),
    }
    MANUAL_CANCEL = (617, 609)            # 双按钮版 [Esc] 取消
    MANUAL_CONFIRM = (925, 609)           # 双按钮版 [Space] 开始挑战
    MANUAL_CONFIRM_NEXT = (759, 611)      # 单按钮版 [Space] 确认选择（局内继续轮次）

    # ---- 行动抉择弹窗 ----
    # 两套：常规 / 灾厄（弹窗差 59px）。检测到哪一套就点哪一套的坐标。
    ACTION_CONTINUE = (1028, 622)
    ACTION_CONTINUE_2 = (1026, 560)
    ACTION_RETREAT = (515, 619)

    # ---- 任务结算（不需要判据：靠 in_team() 真假 + 点了之后界面消失来推进）----
    RESULT_AGAIN = (1122, 796)
    RESULT_QUIT = (1427, 796)

    # ---- 密函选择 ----
    # 卡牌矩阵里「⊘ 不使用」固定占第 1 格，第一个可选密函固定在第 2 格。
    # 三张密函截图（局外/局内/结算后）的卡片边界逐像素一致，第 2 格卡面 x 823~880。
    # 所以"自动选择第一个密函"点的是**第 2 格**，不是 ⊘ 那格；框取卡面内侧避开圆角边框。
    LETTER_FIRST = (825, 365, 880, 418)
    # 「Space 确认选择」按钮中心（局外 x1292 / 局内 x1108，实测都落在芯片上）。
    # 芯片模板在云游戏实拍帧上只有 0.76，过不了 0.8 阈值，所以不做检测、直接点这里
    LETTER_CONFIRM = (1292, 583)
    LETTER_INGAME_CONFIRM = (1108, 580)

    # ---- 密函奖励 ----
    # 点奖励区域本身（REWARD_COUNT_BOX）；实测点卡片中间的图案只会弹出物品详情，
    # 不会改变选择，所以这里不再保留"卡片中心"坐标。
    LETTER_REWARD_CONFIRM = (808, 755)

    # ---- ESC 菜单 ----
    ESC_CONTINUE = (1013, 817)
    ESC_SETTINGS = (1170, 814)
    ESC_CHAR_SKILL = (1326, 811)
    ESC_GIVEUP = (1479, 812)

    # ---- 重置角色 / 复位并传送 ----
    # 「复位角色」整条都能点，用 SCREEN_BOX.RESET_CHARACTER_AREA 在框内随机点
    RESET_TRANSPORT_OK = (962, 506)           # 二次确认弹窗的「确定」按钮

    # ---- 沉浸式戏剧（不朽剧目·勇者征程）----
    # 判据都是按钮/图标本身（label 在 AutoTheatreTask 里），这里只需点按钮上的图标中心：
    # 图标都落在按钮内侧，实测点这些坐标不会误触隔壁按钮。
    THEATRE_START = (1402, 802)               # 阵容页「前往」的 ✦ 图标
    THEATRE_START_CONFIRM = (843, 523)        # 「确认进入」弹窗的「确定」圆圈
    THEATRE_RESULT_WIN = (1382, 843)          # 结算页「前往」的黄色圆圈（下一层）
    THEATRE_RESULT_RETRY = (1069, 843)        # 结算页「再次挑战」的环形箭头
    THEATRE_ESC_RETRY = (1326, 816)           # 局内菜单「重新开始」（和旧菜单第 3 个按钮同位置）
    # 「是否重新开始战斗」二次确认弹窗的「确定」：和「复位角色」的二次确认是同一个按钮位置
    THEATRE_RESTART_CONFIRM = (962, 506)

    # ---- 月卡（按用户要求沿用旧坐标，不重构）----
    MONTHLY_CARD_CLOSE = (800, 801)
