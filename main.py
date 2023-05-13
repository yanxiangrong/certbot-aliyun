#!/usr/bin/env python
import os
import sys

from cmd.main import main

MIN_VERSION = 0x030900F0
MIN_VERSION_STR = '3.9'

if sys.hexversion < MIN_VERSION:
    print(f'需要在 Python 解释器版本 {MIN_VERSION_STR} 及以上运行！')
    exit(os.EX_SOFTWARE)

if __name__ == "__main__":
    main()
