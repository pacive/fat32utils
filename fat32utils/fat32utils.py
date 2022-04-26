import imp
import msvcrt
import win32file
import winioctlcon
import contextlib
import os
import sys
import fat32
from pathlib import Path

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

file = Path(os.path.abspath('e:/test.txt'))

with open('\\\\.\\' + file.drive, 'rb+') as f:
  with lock_volume(f):
    fs = fat32.Drive(f)
    dir = fs.root_dir()
    files = dir.get_files()
    for file in files:
      print(f"{file.meta.short_name.rstrip().decode('ansi')}.{file.meta.extension.rstrip().decode('ansi')} attrs: {file.meta.attributes} size: {file.meta.size}")
    test_file = files[3]
    test_file.meta.start_cluster = 5
    test_file.meta.size = 7
    # print(f'{test_file.meta.location.sector} + {test_file.meta.location.byte}')
    # print(test_file.meta.location.abs_byte())
    # print(f'{dir.clusters[0].location.sector} + {dir.clusters[0].location.byte}')
    # print(dir.clusters[0].location.abs_byte())
    # print(fs.bpb.root_dir_cluster())
    # root_dir_cluster = fat32.Location.of_cluster(fs.bpb, fs.bpb.root_dir_cluster())
    # print(f'{root_dir_cluster.sector} + {root_dir_cluster.byte}')

    dir.seek(test_file.meta.location.abs_byte() - dir.clusters[0].location.abs_byte())
    dir.write(test_file.meta.encode())

