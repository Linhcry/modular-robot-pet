"""Conservative stage gates; never terminate apps or change Windows settings."""
import ctypes
import json
from datetime import datetime
from pathlib import Path

GIB = 1024 ** 3
LOG = Path(__file__).resolve().parents[1] / 'validation/建模内存检查.jsonl'
POLICY = Path(__file__).resolve().parents[1] / 'data/cad_runtime_policy.json'
_WARNED = False


class MemoryBudgetExceeded(RuntimeError):
    pass


class MemoryStatus(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in
        ('total_phys', 'avail_phys', 'total_page', 'avail_page',
         'total_virtual', 'avail_virtual', 'avail_extended')]


def snapshot():
    value = MemoryStatus()
    value.length = ctypes.sizeof(value)
    api = ctypes.WinDLL('kernel32', use_last_error=True).GlobalMemoryStatusEx
    api.argtypes = [ctypes.POINTER(MemoryStatus)]
    api.restype = ctypes.c_int
    if not api(ctypes.byref(value)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {'physical_total_gib': value.total_phys / GIB,
            'physical_available_gib': value.avail_phys / GIB,
            'commit_available_gib': value.avail_page / GIB}


def require_memory(stage, physical_gib=4.0, commit_gib=6.0, *, observed=None):
    """Reserve headroom before new work; saving/closing must remain callable.

    This is a sampled admission check, not a hard memory cap or protection
    against a single COM call allocating more than the remaining headroom.
    """
    global _WARNED
    value = snapshot() if observed is None else observed
    action = json.loads(POLICY.read_text(encoding='utf-8')).get('low_memory_action','stop') if POLICY.exists() and observed is None else 'stop'
    allowed = (value['physical_available_gib'] >= physical_gib and
               value['commit_available_gib'] >= commit_gib)
    record = {'time': datetime.now().astimezone().isoformat(), 'stage': stage,
              **value, 'reserve_physical_gib': physical_gib,
              'reserve_commit_gib': commit_gib, 'headroom_sufficient': allowed,
              'low_memory_action': action, 'allowed': allowed or action=='warn'}
    if observed is None:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    if not allowed:
        if action=='warn':
            if not _WARNED:
                print(f'{stage}: 按用户当前要求继续；可用内存 {value["physical_available_gib"]:.2f} GiB。',flush=True)
                _WARNED=True
            return record
        raise MemoryBudgetExceeded(
            f'{stage}: 暂停新增CAD工作；可用物理内存 '
            f'{value["physical_available_gib"]:.2f} GiB（需 {physical_gib}），'
            f'提交余量 {value["commit_available_gib"]:.2f} GiB（需 {commit_gib}）。')
    return record


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(json.dumps(require_memory('后台CAD启动前检查'), ensure_ascii=False, indent=2))
    except MemoryBudgetExceeded as error:
        print(error)
        sys.exit(2)
