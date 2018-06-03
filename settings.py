from datetime import datetime

import glob
import os.path
import posixpath

conf_files = glob.glob(
    os.path.join(os.path.dirname(__file__), 'settings', '*.py'))
conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))
