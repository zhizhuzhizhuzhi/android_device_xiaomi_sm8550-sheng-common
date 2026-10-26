#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import runpy,sys
entry=Path(__file__).with_name('extract-files.py')
sys.argv=[str(entry),'--regenerate_makefiles',*sys.argv[1:]]
runpy.run_path(str(entry),run_name='__main__')
