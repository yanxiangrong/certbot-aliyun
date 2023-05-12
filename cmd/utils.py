import os
import shutil
from pathlib import Path


def is_root() -> bool:
    return os.geteuid() == 0


def cmd(c: str, err_exit: bool = True):
    print(c)
    ret = os.system(c)
    if ret == 0:
        return
    if err_exit:
        exit(ret)


def remove(name: str | Path):
    if isinstance(name, str):
        name = Path(name)
    try:
        print(f'remove {name}', end='  ')
        if name.is_dir():
            shutil.rmtree(name)
        else:
            os.remove(name)
        print('OK')
    except FileNotFoundError:
        print('Not found')


def link(src: str | Path, dst: str | Path):
    print(f'link {src} to {dst}')
    os.symlink(src, dst)


def copy(src: str | Path, dst: str | Path):
    print(f'copy {src} to {dst}')

    if isinstance(src, str):
        src = Path(src)
    if isinstance(dst, str):
        dst = Path(dst)

    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy(src, dst)


def write_file(filename: str | Path, data: str, re_name: bool = True):
    if isinstance(filename, str):
        filename = Path(filename)
    if not re_name:
        if filename.exists():
            raise FileExistsError(f"[Errno 17] File exists: '{filename}'")

    filename.parent.mkdir(parents=True, exist_ok=True)

    for i in range(1000):
        if i == 0:
            t_filename = filename
        else:
            t_filename = f'{filename}.{i}'
        if Path(t_filename).exists():
            continue

        print(f'Write to: {t_filename}')
        with open(t_filename, 'w') as f:
            f.write(data)
        break


def input_string(pmt: str):
    while True:
        ret = input(f'{pmt}: ')
        if len(ret) == 0:
            continue

        return ret


def input_yes_no(pmt: str) -> bool:
    while True:
        ret = input(f'{pmt} yes / no: ')
        if len(ret) == 0:
            continue
        ret = ret.lower()
        match ret:
            case 'yes':
                return True
            case 'y':
                return True
            case 'no':
                return False
            case 'n':
                return False


def input_select(sel: str, opt: list[str]):
    for i in range(len(sel)):
        print(f'    {sel[i]}. {opt[i]}')

    pmt = f'{sel[0]}'
    for i in range(1, len(sel)):
        pmt += f' / {sel[i]}'
    pmt += ': '
    while True:
        ret = input(pmt)
        if len(ret) == 0:
            continue
        if ret in sel:
            return ret


class Systemctl:
    ctl = 'systemctl'

    @classmethod
    def reload(cls):
        cmd(f'{cls.ctl} daemon-reload', err_exit=False)

    @classmethod
    def start(cls, dst):
        cmd(f'{cls.ctl} start {dst}', err_exit=False)

    @classmethod
    def stop(cls, dst):
        cmd(f'{cls.ctl} stop {dst}', err_exit=False)

    @classmethod
    def enable(cls, dst):
        cmd(f'{cls.ctl} enable {dst}', err_exit=False)

    @classmethod
    def disable(cls, dst):
        cmd(f'{cls.ctl} disable {dst}', err_exit=False)
