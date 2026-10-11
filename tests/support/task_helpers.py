"""测试之间共用的判据检查与挂机循环跑法。

判据/流程测试的写法各任务都一样，这里放两份共用实现，避免每个测试模块各抄一遍。
"""


def check_image(case, path, finder, expected=True):
    """在指定截图上跑一个判据，按期望断言（返回 Bool 的按 Bool 断言，否则按 命中/不命中）。"""
    case.set_image(path)
    feature = finder()
    case.logger.info(f'{path} -> {feature}')
    if isinstance(feature, bool):
        case.assertEqual(feature, expected, f'{path} should be {expected}')
    elif expected:
        case.assertIsNotNone(feature, f'{path} should match')
    else:
        case.assertIsNone(feature, f'{path} should not match')


def run_fight_case(case, module, result_label, in_combat_seq, exit_at, seconds_per_poll,
                   patch_names=(), setup=None):
    """跑一遍 `fight_until_result`，返回（返回值, 技能次数, 日志, 重开次数）。

    `in_combat_seq` 按轮次喂给 `is_in_combat()`，超出部分沿用最后一个值；
    第 `exit_at` 轮命中 `result_label`（结算页出现），时钟每轮前进 `seconds_per_poll` 秒。
    `patch_names` / `setup` 给各任务额外要替换或初始化的状态（比如波次、失败计数）。
    """
    task = case.task
    names = ('find_one', 'is_in_combat', 'skill_tick', 'log_info', 'sleep',
             'restart_in_mission', 'combat_seen_at', 'skills_stopped') + tuple(patch_names)
    original = {name: getattr(task, name) for name in names}
    original_time = module.time
    seq = list(in_combat_seq)
    logs, skills, restarts = [], [], []
    win = {'n': 0}
    clock = {'now': 0.0}

    def fake_find_one(name, *args, **kwargs):
        if name == result_label:
            win['n'] += 1
            return 'result' if win['n'] >= exit_at else None
        return None

    def fake_now():
        clock['now'] += seconds_per_poll
        return clock['now']

    try:
        task.find_one = fake_find_one
        task.is_in_combat = lambda: seq.pop(0) if seq else False
        task.skill_tick = lambda: skills.append(1)
        task.log_info = lambda message, *args, **kwargs: logs.append(message)
        task.sleep = lambda seconds: None
        task.restart_in_mission = lambda *args, **kwargs: restarts.append(1)
        task.combat_seen_at = 0.0            # 和假时钟对齐，让"停止释放技能"的计时可算
        task.skills_stopped = False
        if setup is not None:
            setup(task)
        module.time = type('FakeTime', (), {'time': staticmethod(fake_now)})
        return task.fight_until_result(), skills, logs, restarts
    finally:
        module.time = original_time
        for name, value in original.items():
            setattr(task, name, value)
