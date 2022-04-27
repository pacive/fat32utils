import os
import sys
import msvcrt
import win32file
import winioctlcon
import contextlib
import fat32
from pathlib import Path
from fat32.tools import *

@contextlib.contextmanager
def lock_volume(vol):
    hVol = msvcrt.get_osfhandle(vol.fileno())
    win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_LOCK_VOLUME,
                              None, None)
    try:
        yield vol
    finally:
        try:
            vol.flush()
        finally:
            win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_UNLOCK_VOLUME,
                                      None, None)
command = sys.argv[1]
path = Path(os.path.abspath(sys.argv[-1]))

with open('\\\\.\\' + path.drive, 'rb+') as drive:
  with lock_volume(drive):
    fs = fat32.Drive(drive)
    root = fs.root_dir()
    file = get_file(root, str(path))
    if command == 'hide':
      hide(file)
    elif command == 'restore':
      restore(file)
    else:
      print('Invalid command')
