from qfluentwidgets import FluentIcon
import time
import win32con
import win32gui
import ctypes
from ctypes import wintypes

from ok import Logger, TaskDisabledException
from src.tasks.DNAOneTimeTask import DNAOneTimeTask
from src.tasks.BaseCombatTask import BaseCombatTask
from src.tasks.CommissionsTask import CommissionsTask, Mission
from src.tasks.AutoExcavation import AutoExcavation

logger = Logger.get_logger(__name__)

"""
护送任务路径 - 相对时间格式
每个动作包含 delay 字段，表示距离上一个动作的时间间隔
"""

# ESCORT_PATH_A
ESCORT_PATH_A_RELATIVE = [
    {
        "type": "mouse_rotation",
        "delay": 1.49,
        "angle": 16,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1427, "button": "left"},
    {"type": "mouse_up", "delay": 0.5364, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {"type": "mouse_up", "delay": 0.5916, "button": "left"},
    {"type": "mouse_down", "delay": 0.1315, "button": "left"},
    {"type": "mouse_up", "delay": 0.6564, "button": "left"},
    {"type": "mouse_down", "delay": 0.1305, "button": "left"},
    {"type": "mouse_up", "delay": 0.5816, "button": "left"},
    {"type": "key_down", "delay": 0.7784, "key": "w"},
    {"type": "key_down", "delay": 0.1, "key": "lshift"},
    {"type": "key_up", "delay": 0.1216, "key": "w"},
    {"type": "key_up", "delay": 0.113, "key": "lshift"},
    {
        "type": "mouse_rotation",
        "delay": 0.0958,
        "angle": 26,
        "direction": "down",
        "sensitivity": 10,
    },
]

# 总时长: 5.59 秒, 动作数: 14

# ESCORT_PATH_A_1
ESCORT_PATH_A_1_RELATIVE = [
    {
        "type": "mouse_rotation",
        "delay": 0.2,
        "angle": 20,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1913, "button": "left"},
    {"type": "mouse_up", "delay": 0.3554, "button": "left"},
    {"type": "mouse_down", "delay": 0.159, "button": "left"},
    {"type": "mouse_up", "delay": 0.564, "button": "left"},
    {"type": "mouse_down", "delay": 0.0922, "button": "left"},
    {"type": "mouse_up", "delay": 0.5024, "button": "left"},
    {"type": "mouse_down", "delay": 0.1313, "button": "left"},
    {"type": "mouse_up", "delay": 0.5722, "button": "left"},
    {"type": "mouse_down", "delay": 0.0833, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4389,
        "angle": 8,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1557, "button": "left"},
    {"type": "mouse_down", "delay": 0.0682, "button": "left"},
    {"type": "mouse_up", "delay": 0.5662, "button": "left"},
    {"type": "mouse_down", "delay": 0.1283, "button": "left"},
    {"type": "mouse_up", "delay": 0.5584, "button": "left"},
    {"type": "mouse_down", "delay": 0.1283, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.2348,
        "angle": 8,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 20,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.3137, "button": "left"},
    {"type": "mouse_down", "delay": 0.1316, "button": "left"},
    {"type": "mouse_up", "delay": 0.5484, "button": "left"},
    {"type": "key_down", "delay": 0.3737, "key": "w"},
    {"type": "key_up", "delay": 0.5052, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.1274,
        "angle": 18,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.045,
        "angle": 8,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "key_down", "delay": 0.0611, "key": "s"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.0105, "key": "s"},
    {"type": "key_up", "delay": 1.0325, "key": "d"},
    {"type": "key_down", "delay": 0.0571, "key": "w"},
    {"type": "mouse_down", "delay": 1.4299, "button": "left"},
    {"type": "key_up", "delay": 0.0505, "key": "w"},
    {"type": "mouse_up", "delay": 0.3395, "button": "left"},
    {"type": "mouse_down", "delay": 0.1429, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3611,
        "angle": 12,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2625, "button": "left"},
    {"type": "mouse_down", "delay": 0.1279, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5096,
        "angle": 10,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1071, "button": "left"},
    {"type": "mouse_down", "delay": 0.1142, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1417,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.006,
        "angle": 9,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4031, "button": "left"},
    {"type": "mouse_down", "delay": 0.1526, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1443,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0002,
        "angle": 68,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4554, "button": "left"},
    {"type": "key_down", "delay": 0.1, "key": "d"},
    {"type": "key_down", "delay": 0.14, "key": "w"},
    {"type": "key_up", "delay": 0.2638, "key": "d"},
    {"type": "key_down", "delay": 0.0062, "key": "a"},
    {"type": "key_up", "delay": 0.3, "key": "a"},
    {"type": "key_up", "delay": 0.09, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.0444,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 69.5,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1147, "button": "left"},
    {"type": "mouse_up", "delay": 0.6328, "button": "left"},
    {"type": "key_down", "delay": 0.4674, "key": "f"},
    {"type": "key_up", "delay": 0.097, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.2987,
        "angle": 57,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0358, "button": "left"},
    {"type": "mouse_up", "delay": 0.6318, "button": "left"},
    {"type": "mouse_down", "delay": 0.1082, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4242,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1677, "button": "left"},
    {"type": "key_down", "delay": 0.1996, "key": "w"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.1217, "key": "d"},
    {"type": "key_up", "delay": 0.03, "key": "w"},
    {"type": "key_down", "delay": 0.0083, "key": "s"},
    {"type": "key_up", "delay": 0.5017, "key": "s"},
    {"type": "key_down", "delay": 0.0428, "key": "d"},
    {"type": "key_up", "delay": 0.3922, "key": "d"},
    {"type": "key_down", "delay": 1.4303, "key": "f"},
    {"type": "key_up", "delay": 0.131, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.4947,
        "angle": 64,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 34,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.7758, "button": "left"},
    {"type": "mouse_up", "delay": 0.5918, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1018,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 34,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.57, "button": "left"},
    {"type": "mouse_down", "delay": 0.1106, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4194,
        "angle": 54,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 44,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1324, "button": "left"},
    {"type": "key_down", "delay": 0.0965, "key": "d"},
    {"type": "key_down", "delay": 0.32, "key": "w"},
    {"type": "key_up", "delay": 0.18, "key": "d"},
    {"type": "key_down", "delay": 0.0298, "key": "a"},
    {"type": "key_up", "delay": 0.279, "key": "a"},
    {"type": "key_up", "delay": 0.5416, "key": "w"},
    {"type": "key_down", "delay": 0.0495, "key": "s"},
    {"type": "key_down", "delay": 0.3398, "key": "a"},
    {"type": "key_up", "delay": 0.1406, "key": "s"},
    {"type": "key_up", "delay": 0.5784, "key": "a"},
    {"type": "key_down", "delay": 1.4355, "key": "f"},
    {"type": "key_up", "delay": 0.106, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.4807,
        "angle": 108,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 72,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0782, "button": "left"},
    {"type": "mouse_up", "delay": 0.5795, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 26,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1877, "button": "left"},
    {"type": "mouse_down", "delay": 0.0915, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3208,
        "angle": 8,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2877, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 12,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1577, "button": "left"},
    {"type": "key_down", "delay": 0.8847, "key": "s"},
    {"type": "key_down", "delay": 0.0035, "key": "d"},
    {"type": "key_up", "delay": 1.3373, "key": "s"},
    {"type": "key_up", "delay": 0.0195, "key": "d"},
    {"type": "key_down", "delay": 0.234, "key": "a"},
    {"type": "key_down", "delay": 0.0307, "key": "s"},
    {"type": "key_up", "delay": 0.2902, "key": "a"},
    {"type": "key_up", "delay": 0.0021, "key": "s"},
    {"type": "key_down", "delay": 1.4866, "key": "f"},
    {"type": "key_up", "delay": 0.134, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.7597,
        "angle": 21,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.01,
        "angle": 90,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0817, "button": "left"},
    {"type": "mouse_up", "delay": 0.617, "button": "left"},
    {"type": "mouse_down", "delay": 0.113, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4883,
        "angle": 38,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1286, "button": "left"},
    {"type": "mouse_down", "delay": 0.133, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3383,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2786, "button": "left"},
    {"type": "mouse_down", "delay": 0.103, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4783,
        "angle": 16,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 12,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1086, "button": "left"},
    {"type": "mouse_down", "delay": 0.109, "button": "left"},
    {"type": "mouse_up", "delay": 0.5472, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.0752,
        "angle": 19,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0511, "button": "left"},
    {"type": "mouse_up", "delay": 0.4847, "button": "left"},
    {"type": "mouse_down", "delay": 0.1133, "button": "left"},
    {"type": "mouse_up", "delay": 0.6139, "button": "left"},
    {"type": "mouse_down", "delay": 0.1361, "button": "left"},
    {"type": "mouse_up", "delay": 0.5683, "button": "left"},
    {"type": "mouse_down", "delay": 0.1437, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3989,
        "angle": 13,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.0759, "button": "left"},
    {"type": "mouse_down", "delay": 0.1133, "button": "left"},
    {"type": "mouse_up", "delay": 0.6139, "button": "left"},
    {"type": "mouse_down", "delay": 0.1361, "button": "left"},
    {"type": "mouse_up", "delay": 0.5683, "button": "left"},
    {"type": "mouse_down", "delay": 0.1159, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3661,
        "angle": 1,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.158, "button": "left"},
    {"type": "mouse_down", "delay": 0.1757, "button": "left"},
    {"type": "mouse_up", "delay": 0.6041, "button": "left"},
    {"type": "mouse_down", "delay": 0.1148, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "mouse_down", "delay": 0.0797, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3955,
        "angle": 30,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4415, "button": "left"},
    {"type": "mouse_down", "delay": 0.1123, "button": "left"},
    {"type": "mouse_up", "delay": 0.5541, "button": "left"},
    {"type": "key_down", "delay": 0.3359, "key": "s"},
    {"type": "key_down", "delay": 0.07, "key": "a"},
    {"type": "key_down", "delay": 0.1324, "key": "lshift"},
    {"type": "key_up", "delay": 0.1617, "key": "s"},
    {"type": "key_up", "delay": 0.01, "key": "a"},
    {"type": "key_up", "delay": 0.0082, "key": "lshift"},
]

# 总时长: 72.56 秒, 动作数: 174

# ESCORT_PATH_A_2
ESCORT_PATH_A_2_RELATIVE = [
    {
        "type": "mouse_rotation",
        "delay": 0.2,
        "angle": 26,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 7,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.208, "button": "left"},
    {"type": "mouse_up", "delay": 0.5234, "button": "left"},
    {"type": "mouse_down", "delay": 0.1777, "button": "left"},
    {"type": "mouse_up", "delay": 0.5939, "button": "left"},
    {"type": "mouse_down", "delay": 0.1284, "button": "left"},
    {"type": "mouse_up", "delay": 0.5482, "button": "left"},
    {"type": "mouse_down", "delay": 0.2168, "button": "left"},
    {"type": "mouse_up", "delay": 0.543, "button": "left"},
    {"type": "mouse_down", "delay": 0.1523, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3384,
        "angle": 20,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1776, "button": "left"},
    {"type": "mouse_down", "delay": 0.1544, "button": "left"},
    {"type": "mouse_up", "delay": 0.4823, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4356,
        "angle": 4,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 7,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "key_down", "delay": 0.1761, "key": "s"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.0105, "key": "s"},
    {"type": "key_up", "delay": 0.6325, "key": "d"},
    {"type": "key_down", "delay": 0.4571, "key": "w"},
    {"type": "mouse_down", "delay": 1.2299, "button": "left"},
    {"type": "key_up", "delay": 0.0505, "key": "w"},
    {"type": "mouse_up", "delay": 0.3395, "button": "left"},
    {"type": "mouse_down", "delay": 0.1429, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3611,
        "angle": 12,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2625, "button": "left"},
    {"type": "mouse_down", "delay": 0.1279, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5096,
        "angle": 10,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1071, "button": "left"},
    {"type": "mouse_down", "delay": 0.1142, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1417,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.006,
        "angle": 9,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4031, "button": "left"},
    {"type": "mouse_down", "delay": 0.1526, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1443,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0003,
        "angle": 68,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4553, "button": "left"},
    {"type": "key_down", "delay": 0.3, "key": "d"},
    {"type": "key_down", "delay": 0.14, "key": "w"},
    {"type": "key_up", "delay": 0.2638, "key": "d"},
    {"type": "key_down", "delay": 0.0062, "key": "a"},
    {"type": "key_up", "delay": 0.3, "key": "a"},
    {"type": "key_up", "delay": 0.09, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.0444,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0299,
        "angle": 69.5,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1448, "button": "left"},
    {"type": "mouse_up", "delay": 0.6328, "button": "left"},
    {"type": "key_down", "delay": 0.6684, "key": "f"},
    {"type": "key_up", "delay": 0.121, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.7737,
        "angle": 57,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0358, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1642,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4677, "button": "left"},
    {"type": "mouse_down", "delay": 0.1082, "button": "left"},
    {"type": "mouse_up", "delay": 0.5918, "button": "left"},
    {"type": "key_down", "delay": 0.1996, "key": "w"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.1217, "key": "d"},
    {"type": "key_up", "delay": 0.03, "key": "w"},
    {"type": "key_down", "delay": 0.0083, "key": "s"},
    {"type": "key_up", "delay": 0.5017, "key": "s"},
    {"type": "key_down", "delay": 0.0428, "key": "d"},
    {"type": "key_up", "delay": 0.3922, "key": "d"},
    {"type": "key_down", "delay": 1.4303, "key": "f"},
    {"type": "key_up", "delay": 0.131, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.6947,
        "angle": 64,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 34,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.7758, "button": "left"},
    {"type": "mouse_up", "delay": 0.5918, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1018,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 34,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.57, "button": "left"},
    {"type": "mouse_down", "delay": 0.1106, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4194,
        "angle": 54,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 44,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1324, "button": "left"},
    {"type": "key_down", "delay": 0.0965, "key": "d"},
    {"type": "key_down", "delay": 0.32, "key": "w"},
    {"type": "key_up", "delay": 0.18, "key": "d"},
    {"type": "key_down", "delay": 0.0298, "key": "a"},
    {"type": "key_up", "delay": 0.279, "key": "a"},
    {"type": "key_up", "delay": 0.5416, "key": "w"},
    {"type": "key_down", "delay": 0.0495, "key": "s"},
    {"type": "key_down", "delay": 0.3398, "key": "a"},
    {"type": "key_up", "delay": 0.1406, "key": "s"},
    {"type": "key_up", "delay": 0.5784, "key": "a"},
    {"type": "key_down", "delay": 1.4355, "key": "f"},
    {"type": "key_up", "delay": 0.106, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.5807,
        "angle": 108,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 72,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0782, "button": "left"},
    {"type": "mouse_up", "delay": 0.5795, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 26,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1877, "button": "left"},
    {"type": "mouse_down", "delay": 0.0915, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3208,
        "angle": 8,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2877, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 12,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1577, "button": "left"},
    {"type": "key_down", "delay": 0.8847, "key": "s"},
    {"type": "key_down", "delay": 0.0035, "key": "d"},
    {"type": "key_up", "delay": 1.3373, "key": "s"},
    {"type": "key_up", "delay": 0.0195, "key": "d"},
    {"type": "key_down", "delay": 0.234, "key": "a"},
    {"type": "key_down", "delay": 0.0307, "key": "s"},
    {"type": "key_up", "delay": 0.2902, "key": "a"},
    {"type": "key_up", "delay": 0.0021, "key": "s"},
    {"type": "key_down", "delay": 1.4866, "key": "f"},
    {"type": "key_up", "delay": 0.134, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.7597,
        "angle": 21,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.01,
        "angle": 90,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0817, "button": "left"},
    {"type": "mouse_up", "delay": 0.617, "button": "left"},
    {"type": "mouse_down", "delay": 0.113, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4883,
        "angle": 38,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1286, "button": "left"},
    {"type": "mouse_down", "delay": 0.133, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3383,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2786, "button": "left"},
    {"type": "mouse_down", "delay": 0.103, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4783,
        "angle": 16,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 10,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1086, "button": "left"},
    {"type": "key_down", "delay": 0.5714, "key": "w"},
    {"type": "key_down", "delay": 0.3166, "key": "lshift"},
    {"type": "key_up", "delay": 0.1472, "key": "w"},
    {"type": "key_up", "delay": 0.0571, "key": "lshift"},
    {
        "type": "mouse_rotation",
        "delay": 0.0325,
        "angle": 9,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.2228, "button": "left"},
    {"type": "mouse_up", "delay": 0.6421, "button": "left"},
    {"type": "mouse_down", "delay": 0.1563, "button": "left"},
    {"type": "mouse_up", "delay": 0.4657, "button": "left"},
    {"type": "mouse_down", "delay": 0.0487, "button": "left"},
    {"type": "mouse_up", "delay": 0.564, "button": "left"},
    {"type": "mouse_down", "delay": 0.0922, "button": "left"},
    {"type": "mouse_up", "delay": 0.5024, "button": "left"},
    {"type": "mouse_down", "delay": 0.1313, "button": "left"},
    {"type": "mouse_up", "delay": 0.5722, "button": "left"},
    {"type": "mouse_down", "delay": 0.0833, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4389,
        "angle": 8,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1557, "button": "left"},
    {"type": "mouse_down", "delay": 0.0682, "button": "left"},
    {"type": "mouse_up", "delay": 0.5662, "button": "left"},
    {"type": "mouse_down", "delay": 0.1283, "button": "left"},
    {"type": "mouse_up", "delay": 0.5584, "button": "left"},
    {"type": "mouse_down", "delay": 0.1283, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.2948,
        "angle": 20,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.3137, "button": "left"},
    {"type": "mouse_down", "delay": 0.1316, "button": "left"},
    {"type": "mouse_up", "delay": 0.5484, "button": "left"},
    {"type": "mouse_down", "delay": 0.0651, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5413,
        "angle": 1,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.0085, "button": "left"},
    {"type": "mouse_down", "delay": 0.1276, "button": "left"},
    {"type": "mouse_up", "delay": 0.5904, "button": "left"},
    {"type": "mouse_down", "delay": 0.1064, "button": "left"},
    {"type": "mouse_up", "delay": 0.5634, "button": "left"},
    {"type": "mouse_down", "delay": 0.1131, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "mouse_down", "delay": 0.0797, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3955,
        "angle": 30,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4415, "button": "left"},
    {"type": "key_down", "delay": 0.4547, "key": "lshift"},
    {"type": "key_up", "delay": 0.1199, "key": "lshift"},
]

# 总时长: 74.53 秒, 动作数: 174

# ESCORT_PATH_A_3
ESCORT_PATH_A_3_RELATIVE = [
    {
        "type": "mouse_rotation",
        "delay": 0.2,
        "angle": 20,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0913, "button": "left"},
    {"type": "mouse_up", "delay": 0.3554, "button": "left"},
    {"type": "mouse_down", "delay": 0.159, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4243,
        "angle": 15,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1397, "button": "left"},
    {"type": "mouse_down", "delay": 0.0922, "button": "left"},
    {"type": "mouse_up", "delay": 0.5024, "button": "left"},
    {"type": "mouse_down", "delay": 0.1313, "button": "left"},
    {"type": "mouse_up", "delay": 0.5722, "button": "left"},
    {"type": "mouse_down", "delay": 0.0833, "button": "left"},
    {"type": "mouse_up", "delay": 0.5947, "button": "left"},
    {"type": "mouse_down", "delay": 0.0682, "button": "left"},
    {"type": "mouse_up", "delay": 0.5662, "button": "left"},
    {"type": "mouse_down", "delay": 0.1283, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3515,
        "angle": 19,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.05,
        "angle": 16,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1169, "button": "left"},
    {"type": "mouse_down", "delay": 0.1483, "button": "left"},
    {"type": "mouse_up", "delay": 0.6884, "button": "left"},
    {"type": "key_down", "delay": 0.4537, "key": "w"},
    {"type": "key_up", "delay": 0.6052, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.1374,
        "angle": 6,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.05,
        "angle": 4,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "key_down", "delay": 0.0861, "key": "s"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.0105, "key": "s"},
    {"type": "key_up", "delay": 1.0325, "key": "d"},
    {"type": "key_down", "delay": 0.0571, "key": "w"},
    {"type": "key_down", "delay": 0.0429, "key": "d"},
    {"type": "key_up", "delay": 0.16, "key": "d"},
    {"type": "mouse_down", "delay": 0.227, "button": "left"},
    {"type": "key_up", "delay": 0.0505, "key": "w"},
    {"type": "mouse_up", "delay": 0.3395, "button": "left"},
    {"type": "mouse_down", "delay": 0.1429, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3611,
        "angle": 8,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2625, "button": "left"},
    {"type": "mouse_down", "delay": 0.1279, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5096,
        "angle": 8,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1071, "button": "left"},
    {"type": "mouse_down", "delay": 0.1142, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1417,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.006,
        "angle": 7,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4031, "button": "left"},
    {"type": "mouse_down", "delay": 0.1526, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1443,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0004,
        "angle": 68,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4552, "button": "left"},
    {"type": "key_down", "delay": 1.1, "key": "d"},
    {"type": "key_down", "delay": 0.14, "key": "w"},
    {"type": "key_up", "delay": 0.2638, "key": "d"},
    {"type": "key_down", "delay": 0.0062, "key": "a"},
    {"type": "key_up", "delay": 0.3, "key": "a"},
    {"type": "key_up", "delay": 0.09, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.0144,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.09,
        "angle": 69,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1147, "button": "left"},
    {"type": "mouse_up", "delay": 0.6328, "button": "left"},
    {"type": "key_down", "delay": 0.6684, "key": "f"},
    {"type": "key_up", "delay": 0.121, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.9207,
        "angle": 57,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0358, "button": "left"},
    {"type": "mouse_up", "delay": 0.6318, "button": "left"},
    {"type": "mouse_down", "delay": 0.1082, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4242,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1677, "button": "left"},
    {"type": "key_down", "delay": 0.1996, "key": "w"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.1217, "key": "d"},
    {"type": "key_up", "delay": 0.03, "key": "w"},
    {"type": "key_down", "delay": 0.0083, "key": "s"},
    {"type": "key_up", "delay": 0.5017, "key": "s"},
    {"type": "key_down", "delay": 0.0428, "key": "d"},
    {"type": "key_up", "delay": 0.3922, "key": "d"},
    {"type": "key_down", "delay": 1.4303, "key": "f"},
    {"type": "key_up", "delay": 0.131, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.6477,
        "angle": 64,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 34,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.7758, "button": "left"},
    {"type": "mouse_up", "delay": 0.5918, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1018,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 34,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.57, "button": "left"},
    {"type": "mouse_down", "delay": 0.1106, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4194,
        "angle": 54,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 44,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1324, "button": "left"},
    {"type": "key_down", "delay": 0.0965, "key": "d"},
    {"type": "key_down", "delay": 0.32, "key": "w"},
    {"type": "key_up", "delay": 0.18, "key": "d"},
    {"type": "key_down", "delay": 0.0298, "key": "a"},
    {"type": "key_up", "delay": 0.279, "key": "a"},
    {"type": "key_up", "delay": 0.5416, "key": "w"},
    {"type": "key_down", "delay": 0.0495, "key": "s"},
    {"type": "key_down", "delay": 0.3398, "key": "a"},
    {"type": "key_up", "delay": 0.1406, "key": "s"},
    {"type": "key_up", "delay": 0.5784, "key": "a"},
    {"type": "key_down", "delay": 1.4355, "key": "f"},
    {"type": "key_up", "delay": 0.106, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.6997,
        "angle": 108,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 72,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0782, "button": "left"},
    {"type": "mouse_up", "delay": 0.5795, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 26,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1877, "button": "left"},
    {"type": "mouse_down", "delay": 0.0915, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3208,
        "angle": 8,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2877, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 12,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1577, "button": "left"},
    {"type": "key_down", "delay": 0.8847, "key": "s"},
    {"type": "key_down", "delay": 0.0035, "key": "d"},
    {"type": "key_up", "delay": 1.3373, "key": "s"},
    {"type": "key_up", "delay": 0.0195, "key": "d"},
    {"type": "key_down", "delay": 0.234, "key": "a"},
    {"type": "key_down", "delay": 0.0307, "key": "s"},
    {"type": "key_up", "delay": 0.2902, "key": "a"},
    {"type": "key_up", "delay": 0.0021, "key": "s"},
    {"type": "key_down", "delay": 1.4866, "key": "f"},
    {"type": "key_up", "delay": 0.134, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.8987,
        "angle": 21,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.01,
        "angle": 90,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0817, "button": "left"},
    {"type": "mouse_up", "delay": 0.617, "button": "left"},
    {"type": "mouse_down", "delay": 0.113, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4883,
        "angle": 38,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1286, "button": "left"},
    {"type": "mouse_down", "delay": 0.133, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3383,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2786, "button": "left"},
    {"type": "mouse_down", "delay": 0.103, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4783,
        "angle": 11,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1386, "button": "left"},
    {"type": "mouse_down", "delay": 0.1125, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.2889,
        "angle": 6,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0303,
        "angle": 6,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.206, "button": "left"},
    {"type": "mouse_down", "delay": 0.1365, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.2782,
        "angle": 6,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.049,
        "angle": 3,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2916, "button": "left"},
    {"type": "mouse_down", "delay": 0.1635, "button": "left"},
    {"type": "mouse_up", "delay": 0.6194, "button": "left"},
    {"type": "mouse_down", "delay": 0.1342, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3413,
        "angle": 15,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 10,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4542, "button": "left"},
    {"type": "mouse_down", "delay": 0.1579, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.2979,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.01,
        "angle": 5,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2418, "button": "left"},
    {"type": "mouse_down", "delay": 0.1276, "button": "left"},
    {"type": "mouse_up", "delay": 0.5904, "button": "left"},
    {"type": "mouse_down", "delay": 0.183, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "mouse_down", "delay": 0.0797, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3955,
        "angle": 35,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4415, "button": "left"},
    {"type": "mouse_down", "delay": 0.1213, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "key_down", "delay": 0.2613, "key": "lshift"},
    {"type": "key_up", "delay": 0.0634, "key": "lshift"},
]

# 总时长: 71.53 秒, 动作数: 168

# ESCORT_PATH_A_4
ESCORT_PATH_A_4_RELATIVE = [
    {
        "type": "mouse_rotation",
        "delay": 0.2,
        "angle": 21,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1913, "button": "left"},
    {"type": "mouse_up", "delay": 0.3554, "button": "left"},
    {"type": "mouse_down", "delay": 0.159, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4243,
        "angle": 33,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1397, "button": "left"},
    {"type": "mouse_down", "delay": 0.0922, "button": "left"},
    {"type": "mouse_up", "delay": 0.5024, "button": "left"},
    {"type": "mouse_down", "delay": 0.1276, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3882,
        "angle": 20,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2843, "button": "left"},
    {"type": "mouse_down", "delay": 0.1276, "button": "left"},
    {"type": "mouse_up", "delay": 0.5724, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5157,
        "angle": 15,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.05,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "key_down", "delay": 0.0661, "key": "s"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.0105, "key": "s"},
    {"type": "key_up", "delay": 0.6325, "key": "d"},
    {"type": "key_down", "delay": 0.4571, "key": "w"},
    {"type": "mouse_down", "delay": 1.4299, "button": "left"},
    {"type": "key_up", "delay": 0.0505, "key": "w"},
    {"type": "mouse_up", "delay": 0.3395, "button": "left"},
    {"type": "mouse_down", "delay": 0.1429, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3611,
        "angle": 16,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2625, "button": "left"},
    {"type": "mouse_down", "delay": 0.1279, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.5096,
        "angle": 7,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1071, "button": "left"},
    {"type": "mouse_down", "delay": 0.1142, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1418,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0059,
        "angle": 9,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4031, "button": "left"},
    {"type": "mouse_down", "delay": 0.1526, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1443,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0006,
        "angle": 68,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.455, "button": "left"},
    {"type": "key_down", "delay": 0.1, "key": "d"},
    {"type": "key_down", "delay": 0.14, "key": "w"},
    {"type": "key_up", "delay": 0.2638, "key": "d"},
    {"type": "key_down", "delay": 0.0062, "key": "a"},
    {"type": "key_up", "delay": 0.3, "key": "a"},
    {"type": "key_up", "delay": 0.09, "key": "w"},
    {
        "type": "mouse_rotation",
        "delay": 0.0344,
        "angle": 1,
        "direction": "up",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.07,
        "angle": 69.5,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.1147, "button": "left"},
    {"type": "mouse_up", "delay": 0.6328, "button": "left"},
    {"type": "key_down", "delay": 0.6684, "key": "f"},
    {"type": "key_up", "delay": 0.121, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.7997,
        "angle": 56.5,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 3,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0358, "button": "left"},
    {"type": "mouse_up", "delay": 0.6318, "button": "left"},
    {"type": "mouse_down", "delay": 0.1082, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4242,
        "angle": 3,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1677, "button": "left"},
    {"type": "key_down", "delay": 0.1996, "key": "w"},
    {"type": "key_down", "delay": 0.24, "key": "d"},
    {"type": "key_up", "delay": 0.1217, "key": "d"},
    {"type": "key_up", "delay": 0.03, "key": "w"},
    {"type": "key_down", "delay": 0.0083, "key": "s"},
    {"type": "key_up", "delay": 0.5017, "key": "s"},
    {"type": "key_down", "delay": 0.0428, "key": "d"},
    {"type": "key_up", "delay": 0.3922, "key": "d"},
    {"type": "key_down", "delay": 1.4303, "key": "f"},
    {"type": "key_up", "delay": 0.131, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.6997,
        "angle": 64,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 34,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.7758, "button": "left"},
    {"type": "mouse_up", "delay": 0.5918, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1018,
        "angle": 2,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.02,
        "angle": 34,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.57, "button": "left"},
    {"type": "mouse_down", "delay": 0.1106, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4194,
        "angle": 51,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.04,
        "angle": 44,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1324, "button": "left"},
    {"type": "key_down", "delay": 0.0965, "key": "d"},
    {"type": "key_down", "delay": 0.32, "key": "w"},
    {"type": "key_up", "delay": 0.18, "key": "d"},
    {"type": "key_down", "delay": 0.0298, "key": "a"},
    {"type": "key_up", "delay": 0.279, "key": "a"},
    {"type": "key_up", "delay": 0.5416, "key": "w"},
    {"type": "key_down", "delay": 0.0495, "key": "s"},
    {"type": "key_down", "delay": 0.3398, "key": "a"},
    {"type": "key_up", "delay": 0.1406, "key": "s"},
    {"type": "key_up", "delay": 0.5784, "key": "a"},
    {"type": "key_down", "delay": 1.4355, "key": "f"},
    {"type": "key_up", "delay": 0.106, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.6997,
        "angle": 108,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 72,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0782, "button": "left"},
    {"type": "mouse_up", "delay": 0.5795, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 18,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.03,
        "angle": 28,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1877, "button": "left"},
    {"type": "mouse_down", "delay": 0.0915, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3208,
        "angle": 11,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2877, "button": "left"},
    {"type": "mouse_down", "delay": 0.1205, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3618,
        "angle": 12,
        "direction": "right",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.06,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1577, "button": "left"},
    {"type": "key_down", "delay": 0.8847, "key": "s"},
    {"type": "key_down", "delay": 0.0035, "key": "d"},
    {"type": "key_up", "delay": 1.3373, "key": "s"},
    {"type": "key_up", "delay": 0.0195, "key": "d"},
    {"type": "key_down", "delay": 0.234, "key": "a"},
    {"type": "key_down", "delay": 0.0307, "key": "s"},
    {"type": "key_up", "delay": 0.2902, "key": "a"},
    {"type": "key_up", "delay": 0.0021, "key": "s"},
    {"type": "key_down", "delay": 1.4866, "key": "f"},
    {"type": "key_up", "delay": 0.134, "key": "f"},
    {
        "type": "mouse_rotation",
        "delay": 6.8987,
        "angle": 21,
        "direction": "down",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.01,
        "angle": 90,
        "direction": "right",
        "sensitivity": 10,
    },
    {"type": "mouse_down", "delay": 0.0817, "button": "left"},
    {"type": "mouse_up", "delay": 0.617, "button": "left"},
    {"type": "mouse_down", "delay": 0.113, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4883,
        "angle": 37,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1286, "button": "left"},
    {"type": "mouse_down", "delay": 0.133, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3383,
        "angle": 12,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2786, "button": "left"},
    {"type": "mouse_down", "delay": 0.103, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.4783,
        "angle": 16.2,
        "direction": "left",
        "sensitivity": 10,
    },
    {
        "type": "mouse_rotation",
        "delay": 0.0,
        "angle": 15,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1386, "button": "left"},
    {"type": "mouse_down", "delay": 0.1125, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.1289,
        "angle": 15,
        "direction": "up",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2799, "button": "left"},
    {"type": "mouse_down", "delay": 0.3569, "button": "left"},
    {"type": "mouse_up", "delay": 0.5438, "button": "left"},
    {"type": "mouse_down", "delay": 0.1867, "button": "left"},
    {"type": "mouse_up", "delay": 0.5137, "button": "left"},
    {"type": "mouse_down", "delay": 0.1238, "button": "left"},
    {"type": "mouse_up", "delay": 0.6366, "button": "left"},
    {"type": "mouse_down", "delay": 0.0855, "button": "left"},
    {"type": "mouse_up", "delay": 0.5408, "button": "left"},
    {"type": "mouse_down", "delay": 0.1404, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3919,
        "angle": 12,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.1608, "button": "left"},
    {"type": "mouse_down", "delay": 0.1454, "button": "left"},
    {"type": "mouse_up", "delay": 0.5521, "button": "left"},
    {"type": "mouse_down", "delay": 0.1238, "button": "left"},
    {"type": "mouse_up", "delay": 0.5497, "button": "left"},
    {"type": "mouse_down", "delay": 0.1276, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3315,
        "angle": 0.4,
        "direction": "left",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.2588, "button": "left"},
    {"type": "mouse_down", "delay": 0.1064, "button": "left"},
    {"type": "mouse_up", "delay": 0.5634, "button": "left"},
    {"type": "mouse_down", "delay": 0.1131, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "mouse_down", "delay": 0.0797, "button": "left"},
    {
        "type": "mouse_rotation",
        "delay": 0.3955,
        "angle": 30,
        "direction": "down",
        "sensitivity": 10,
    },
    {"type": "mouse_up", "delay": 0.4415, "button": "left"},
    {"type": "mouse_down", "delay": 0.1113, "button": "left"},
    {"type": "mouse_up", "delay": 0.5721, "button": "left"},
    {"type": "key_down", "delay": 0.3284, "key": "s"},
    {"type": "key_down", "delay": 0.07, "key": "a"},
    {"type": "key_down", "delay": 0.1324, "key": "lshift"},
    {"type": "key_up", "delay": 0.1617, "key": "s"},
    {"type": "key_up", "delay": 0.01, "key": "a"},
    {"type": "key_up", "delay": 0.0082, "key": "lshift"},
]

# 总时长: 71.55 秒, 动作数: 165


class AutoEscortTask(DNAOneTimeTask, CommissionsTask, BaseCombatTask):
    """自动护送任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon = FluentIcon.FLAG
        self.name = "自动飞枪80护送（无需巧手）【需要游戏处于前台】"
        self.description = "全自动80护送任务，搬运自emt，欢迎路径作者署名。\n需要使用水母主控，近战武器选择0精春玦戟。魔之楔配置为金色迅捷+5，紫色穿引共鸣，紫色迅捷蓄势+5，紫色迅捷坠击+5，不要携带其他魔之楔，面板攻速为1.67。\n设置中控制设置水平灵敏度和垂直灵敏度设置为1.0，默认镜头距离设置为1.3。确认好自身魔之楔和设置后展开下方配置点击我已阅读后运行"
        self.group_name = "全自动"
        self.group_icon = FluentIcon.CAFE

        self.default_config.update(
            {
                "刷几次": 999,
                "我已阅读注意事项并确认配置": False,
            }
        )

        self.setup_commission_config()
        keys_to_remove = [
            "启用自动穿引共鸣",
            "使用技能",
            "技能释放频率",
            "发出声音提醒",
        ]
        for key in keys_to_remove:
            self.default_config.pop(key, None)

        self.config_description.update(
            {
                "刷几次": "完成几次护送任务后停止",
                "我已阅读注意事项并确认配置": "必须勾选才能执行任务！",
            }
        )

        self.action_timeout = 10
        self.escort_actions = ESCORT_PATH_A_RELATIVE

        # 统计信息
        self.stats = {
            "rounds_completed": 0,  # 完成轮数
            "total_time": 0.0,  # 总耗时
            "start_time": None,  # 开始时间
            "current_phase": "准备中",  # 当前阶段
            "failed_attempts": 0,  # 失败次数（重新开始）
            "selected_path": None,  # 当前选择的路径
        }

    def run(self):
        DNAOneTimeTask.run(self)
        self.move_mouse_to_safe_position()
        self.set_check_monthly_card()
        try:
            return self.do_run()
        except TaskDisabledException:
            pass
        except Exception as e:
            logger.error("AutoEscortTask error", e)
            raise

    def do_run(self):
        # 检查是否已阅读注意事项
        if not self.config.get("我已阅读注意事项并确认配置", False):
            logger.error("⚠️ 请先阅读注意事项并确认配置！")

            # 使用 info_set 显示详细配置要求
            self.info_set("错误", "未勾选配置确认")
            self.info_set("角色与武器", "使用水母主控，近战武器: 0精春玦戟")
            self.info_set(
                "武器mod(不要携带其他魔之楔)",
                "金色迅捷+5、紫色穿引共鸣、紫色迅捷蓄势+5、紫色迅捷坠击+5",
            )
            self.info_set("武器面板攻速", "面板攻速: 1.67")
            self.info_set("控制设置", "水平/垂直灵敏度: 1.0。镜头距离: 1.3")

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

                    # 先执行初始路径（使用相对时间版本）
                    self.escort_actions = ESCORT_PATH_A_RELATIVE
                    success = self.execute_escort_path()

                    # 如果初始路径执行失败，等待退出队伍并重新开始
                    if not success:
                        logger.warning("初始路径执行失败，等待退出队伍...")
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

                    self.sleep(1)
                    # 基于 track_point 位置选择后续路径
                    self.stats["current_phase"] = "检测路径"
                    self.info_set("当前阶段", "检测路径")
                    logger.info("检测 track_point 位置，选择护送路径...")
                    self.escort_actions = self.select_escort_path_by_position()

                    # 如果检测失败返回 None，说明已经调用了 give_up_mission，等待退出队伍
                    if self.escort_actions is None:
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

                    # 更新选择的路径
                    self.stats["current_phase"] = "执行护送路径"
                    self.info_set(
                        "当前阶段", f"执行路径{self.stats.get('selected_path', '?')}"
                    )

                    success = self.execute_escort_path()

                    # 如果后续路径执行失败（解密失败），等待退出队伍并重新开始
                    if not success:
                        logger.warning("后续路径执行失败，等待退出队伍...")
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

                    # 记录路径执行结束时间
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
                    max_rounds = self.config.get("刷几次", 999)
                    if max_rounds > 0:
                        remaining = max_rounds - self.stats["rounds_completed"]
                        logger.info(f"  剩余轮数: {remaining}")
                    logger.info("=" * 50)

                if _count >= self.config.get("刷几次", 999):
                    self.sleep(1)
                    self.open_in_mission_menu()
                    self.log_info_notify("任务终止")
                    self.soundBeep()
                    return
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

    def select_escort_path_by_position(self):
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
        # 定义 3840x2160 分辨率下的参考点
        reference_points = {
            1: (1902, 431),
            2: (1719, 438),
            3: (2284, 461),
            4: (2898, 688),
        }

        # 获取当前分辨率
        current_width = self.width
        current_height = self.height

        # 计算缩放比例
        scale_x = current_width / 3840
        scale_y = current_height / 2160

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
            track_point = AutoExcavation.find_track_point(self)

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

            # 返回对应的路径
            path_map = {
                1: ESCORT_PATH_A_1_RELATIVE,
                2: ESCORT_PATH_A_2_RELATIVE,
                3: ESCORT_PATH_A_3_RELATIVE,
                4: ESCORT_PATH_A_4_RELATIVE,
            }

            return path_map.get(selected_path, ESCORT_PATH_A_1_RELATIVE)

        except Exception as e:
            logger.error(f"❌ 检测 track_point 时出错: {e}，重新开始任务...")
            self.give_up_mission()
            return None

    def execute_escort_path(self):
        """执行护送路径中的所有动作，遇到 f 键时等待 AutoPuzzleTask 完成

        Returns:
            bool: True=成功完成, False=失败需要重新开始
        """
        if not self.escort_actions:
            logger.warning("没有加载护送路径，跳过移动")
            return True

        logger.info(f"开始执行护送路径，共 {len(self.escort_actions)} 个动作")

        # 将路径按 f 键拆分成多个片段
        path_segments = self.split_path_by_f_key()

        for segment_idx, segment in enumerate(path_segments):
            logger.info(f"执行路径片段 {segment_idx + 1}/{len(path_segments)}")

            # 如果前一个片段有 f 键（刚完成解密等待），跳过当前片段第一个动作的 delay
            skip_first_delay = segment_idx > 0 and self.segment_has_f_key(
                path_segments[segment_idx - 1]
            )

            self.execute_path_segment(segment, skip_first_delay=skip_first_delay)

            # 如果这个片段包含 f 键，等待 AutoPuzzleTask 完成解密
            if self.segment_has_f_key(segment):
                logger.info("检测到 f 键，等待 AutoPuzzleTask 完成解密...")
                success = self.wait_for_puzzle_completion()
                if not success:
                    # 解密失败，需要重新开始任务
                    return False

        logger.info("护送路径执行完成")
        return True

    def split_path_by_f_key(self):
        """将路径按 f 键拆分成多个片段"""
        segments = []
        current_segment = []

        for action in self.escort_actions:
            current_segment.append(action)

            # 检测到 key_up "f" 作为一个片段的结束
            if action.get("type") == "key_up" and action.get("key") == "f":
                segments.append(current_segment)
                current_segment = []

        # 如果还有剩余动作，添加为最后一个片段
        if current_segment:
            segments.append(current_segment)

        return segments if segments else [self.escort_actions]

    def segment_has_f_key(self, segment):
        """检查片段是否包含 f 键"""
        for action in segment:
            if (
                action.get("type") in ["key_down", "key_up"]
                and action.get("key") == "f"
            ):
                return True
        return False

    def execute_path_segment(self, segment, skip_first_delay=False):
        """执行单个路径片段（使用相对时间）

        新格式：每个动作包含 delay 字段（距离上一个动作的时间间隔）
        这样在解密等待后，后续动作可以立即继续，不会因为绝对时间错位

        Args:
            segment: 路径片段（动作列表）
            skip_first_delay: 是否跳过第一个动作的 delay（解密等待后使用）
        """
        for i, action in enumerate(segment):
            action_type = action.get("type")
            delay = action.get("delay", 0)

            # 如果是第一个动作且需要跳过 delay，则不等待
            if i == 0 and skip_first_delay:
                logger.debug(
                    f"跳过片段首个动作的 delay ({delay:.3f}s)，解密等待已消耗此时间"
                )
                delay = 1

            # 等待指定的延迟时间（使用高精度等待）
            if delay > 0:
                if delay > 0.001:
                    # 先 sleep 大部分时间，预留 0.5ms 缓冲
                    time.sleep(max(0, delay - 0.0005))

                    # 自旋等待，提高时间精度
                    end_time = time.perf_counter() + 0.0005
                    while time.perf_counter() < end_time:
                        pass
                else:
                    # 短延迟直接 sleep
                    time.sleep(delay)

            # 执行不同类型的动作
            if action_type == "mouse_rotation":
                self.execute_mouse_rotation(action)
            elif action_type == "mouse_down":
                button = action.get("button", "left")
                self.mouse_down(key=button)
                logger.debug(f"按下鼠标: {button}")
            elif action_type == "mouse_up":
                button = action.get("button", "left")
                self.mouse_up(key=button)
                logger.debug(f"释放鼠标: {button}")
            elif action_type == "key_down":
                key = action.get("key")
                self.send_key_down(key)
                logger.debug(f"按下键: {key}")
            elif action_type == "key_up":
                key = action.get("key")
                self.send_key_up(key)
                logger.debug(f"释放键: {key}")
            else:
                logger.warning(f"未知动作类型: {action_type}")

    def wait_for_puzzle_completion(self, timeout=30):
        """等待 AutoPuzzleTask 完成解密

        主动检测 puzzle 并触发解密，然后等待解密完成

        Returns:
            bool: True=成功完成或无需解密, False=检测失败需要重新开始任务
        """
        from src.tasks.AutoPuzzleTask import AutoPuzzleTask

        # 获取 AutoPuzzleTask 实例
        puzzle_task = self.get_task_by_class(AutoPuzzleTask)
        if not puzzle_task:
            logger.warning("未找到 AutoPuzzleTask，跳过等待")
            return True

        # 确保 AutoPuzzleTask 已初始化检测区域
        if (
            not puzzle_task.puzzle_boxes
            or puzzle_task.template_shape != self.frame.shape[:2]
        ):
            puzzle_task.init_boxes()
            logger.debug("已初始化 AutoPuzzleTask 检测区域")

        # 等待一小段时间让界面稳定
        self.sleep(0.5)

        # 等待直到屏幕上没有 puzzle 为止
        start_time = time.time()
        puzzle_detected = False
        puzzle_solving = False  # 标记是否正在解密

        while time.time() - start_time < timeout:
            # 更新当前帧（重要！确保检测最新画面）
            self.next_frame()

            # 检查是否有 puzzle
            has_puzzle = False

            for i in range(1, 9):
                puzzle_name = f"puzzle_{i}"
                if puzzle_name not in puzzle_task.puzzle_boxes:
                    continue

                try:
                    puzzle_box = self.find_one(
                        puzzle_name,
                        box=puzzle_task.puzzle_boxes[puzzle_name],
                        threshold=puzzle_task.detection_threshold,
                    )
                    if puzzle_box:
                        has_puzzle = True

                        # 如果检测到 puzzle 且还未开始解密，立即触发解密
                        if not puzzle_solving:
                            puzzle_detected = True
                            puzzle_solving = True
                            logger.info(f"🔍 检测到 {puzzle_name}，开始解密...")
                            # 主动调用 AutoPuzzleTask 的解密方法
                            puzzle_task.solve_puzzle(puzzle_name)
                            logger.info("解密操作已完成，等待 puzzle 消失...")
                        else:
                            logger.debug(f"解密后仍检测到 {puzzle_name}，继续等待...")
                        break
                except Exception as e:
                    logger.debug(f"检测 {puzzle_name} 时出错: {e}")
                    continue

            # 如果曾经检测到过 puzzle 并已解密，但现在没有了，说明解密完成
            if puzzle_solving and not has_puzzle:
                logger.info("✅ 解密完成，puzzle 已消失")
                self.sleep(0.3)  # 额外等待一下确保稳定
                return True

            # 如果从未检测到 puzzle，可能是：
            # 1. puzzle 还未出现（需要继续等待）
            # 2. 这个路径片段没有 puzzle
            # 持续等待一段时间，如果始终没有检测到就认为没有 puzzle
            if not puzzle_detected and time.time() - start_time > 3:
                logger.warning(
                    "❌ 3秒内未检测到解密拼图，路径可能有误，重新开始任务..."
                )
                self.give_up_mission()
                return False

            self.sleep(0.2)

        # 超时
        if puzzle_detected:
            logger.warning(f"❌ 等待解密完成超时（{timeout}秒），重新开始任务...")
            self.give_up_mission()
            return False
        else:
            logger.debug("未检测到解密拼图")
            return True

    def execute_mouse_rotation(self, action):
        """执行鼠标视角旋转动作

        使用 SendInput API（推荐方式，替代已弃用的 mouse_event）
        参考 escort-A.py 的实现，一次性转动后添加 0.1 秒延迟

        注意：MOUSEINPUT.time 字段是事件时间戳，不是移动持续时间
        设置为 0 表示系统自动提供时间戳
        """
        direction = action.get("direction", "up")
        angle = action.get("angle", 0)
        sensitivity = action.get("sensitivity", 10)

        # 根据 escort-A.py 的计算方式：pixels = angle * sensitivity
        pixels = angle * (sensitivity)

        # 计算移动方向
        if direction == "left":
            dx, dy = -pixels, 0
        elif direction == "right":
            dx, dy = pixels, 0
        elif direction == "up":
            dx, dy = 0, -pixels
        elif direction == "down":
            dx, dy = 0, pixels
        else:
            logger.warning(f"未知的鼠标方向: {direction}")
            return

        # 确保游戏窗口在前台（SendInput 需要窗口在前台）
        from ok import og

        if not og.device_manager.hwnd_window.is_foreground():
            logger.debug("游戏窗口不在前台，尝试激活窗口...")
            hwnd = og.device_manager.hwnd_window.hwnd
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)

        # 使用 SendInput 发送鼠标移动事件（推荐方式）
        try:
            # 定义 MOUSEINPUT 结构
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),  # 事件时间戳，0=系统自动提供
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
                ]

            # 定义 INPUT 结构
            class INPUT(ctypes.Structure):
                _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT)]

            # 创建鼠标输入结构
            mouse_input = MOUSEINPUT(
                dx=int(dx),
                dy=int(dy),
                mouseData=0,
                dwFlags=win32con.MOUSEEVENTF_MOVE,  # 0x0001 相对移动
                time=0,  # 0 表示使用系统时间戳
                dwExtraInfo=None,
            )

            # 创建 INPUT 结构
            x = INPUT(type=0, mi=mouse_input)  # INPUT_MOUSE = 0

            # 调用 SendInput
            ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

            logger.debug(f"鼠标视角旋转: {direction}, 角度: {angle}, 像素: {pixels}")

        except Exception as e:
            logger.error(f"鼠标移动失败: {e}")
