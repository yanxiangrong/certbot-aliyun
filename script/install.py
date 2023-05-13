#!/usr/bin/env python
import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import typing
import urllib.error as error
import urllib.request as request
import urllib.response as response
from pathlib import Path

USER = 'yanxiangrong'
REPO = 'certbot-aliyun'
MIN_VERSION = 0x030900F0
MIN_VERSION_STR = '3.9'

if sys.hexversion < MIN_VERSION:
    print(f'需要在 Python 解释器版本 {MIN_VERSION_STR} 及以上运行！')
    exit(os.EX_SOFTWARE)


def retry(func):
    def wrapper(*args, **kwargs):
        for i in range(9):
            try:
                return func(*args, **kwargs)
            except error.URLError as err:
                if isinstance(err.reason, TimeoutError):
                    pass
                else:
                    raise err
        return func(*args, **kwargs)

    return wrapper


def bytes_to_hum(n: int) -> str:
    units = ['B', 'K', 'M', 'G', 'T', 'P']
    u = 0

    while n >= 1024:
        u += 1
        n /= 1024

    if u > 1:
        return f'{n:.2f}{units[u]}'
    return f'{n:.0f}{units[u]}'


def print_progress_bar(val: int, size: typing.Optional[int] = None, is_end=False):
    if size is None:
        proportion = 0
    else:
        proportion = val / size

    bar = '=' * int(38 * proportion)
    if len(bar) > 0:
        bar = bar[:-1] + '>'

    end = ''
    if is_end:
        end = '\n'
    if size is None:
        print(f'\r    - %[{bar:25s}] {bytes_to_hum(val)}/-', end=end)
    else:
        print(f'\r {proportion * 100:5.1f}%[{bar:38s}] {bytes_to_hum(val)}/{bytes_to_hum(size)}', end=end)


@retry
def get_version():
    url = f'https://github.com/{USER}/{REPO}/releases/latest/'
    print(f'Get {url}')
    res: response.addinfourl = request.urlopen(url)
    return Path(res.url).name


@retry
def download(url: str, save_dir: str):
    save_name = Path(save_dir).joinpath('save.tar.gz')
    crd_name = Path(str(save_name) + '.crdownload')

    print(f'Download {url} to {save_name}')

    req = request.Request(url)
    req.add_header('User-Agent', 'Python')

    if crd_name.exists():
        save_size = crd_name.stat().st_size
        req.add_header('Range', f'bytes={save_size}-')
    else:
        open(crd_name, 'wb').close()
    with request.urlopen(req) as r, open(crd_name, 'rb+') as f:
        downloaded = 0

        content_range = r.getheader('Content-Range')
        if content_range is not None:
            prog = re.compile(r'bytes (\d+)-(\d+)/(\d+)')
            result = prog.match(content_range)
            seek, _, length = result.groups()
            seek, length = int(seek), int(length)
            f.seek(seek)
            downloaded += seek
        else:
            f.seek(0)
            length = r.getheader('Content-Length')
            if length is not None:
                length = int(length)

        t0 = time.time()
        while True:
            data = r.read(io.DEFAULT_BUFFER_SIZE)
            if len(data) == 0:
                break
            f.write(data)
            downloaded += len(data)

            now = time.time()
            if now - t0 > 0.1:
                t0 = now
                print_progress_bar(downloaded, length)
        print_progress_bar(downloaded, length, True)
    crd_name.rename(save_name)
    return save_name


def check_root():
    if os.getgid() != 0:
        print('需要以 root 权限运行!')
        exit(os.EX_NOPERM)


def main():
    check_root()

    tmp_dir = tempfile.TemporaryDirectory()
    version_name = get_version()

    src_url = f'https://github.com/{USER}/{REPO}/archive/refs/tags/{version_name}.tar.gz'
    src_url = f'https://github.com/yanxiangrong/certbot-aliyun/archive/refs/tags/v1.0.0-pre-alpha.1.tar.gz'
    save_file = download(src_url, tmp_dir.name)

    print(f'Extract {save_file}')
    tar = tarfile.open(save_file, 'r:*')
    ext_dir = Path(tmp_dir.name).joinpath('extract')
    tar.extractall(ext_dir)
    proj_dir = next(Path(ext_dir).iterdir())

    cwd = os.getcwd()
    os.chdir(proj_dir)

    subprocess.run([sys.executable, 'main.py', 'install'])

    os.chdir(cwd)

    print('Cleanup')
    tmp_dir.cleanup()


if __name__ == '__main__':
    main()
