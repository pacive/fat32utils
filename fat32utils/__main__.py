import os
import sys
import fat32
from pathlib import Path
from fat32.tools import *

command = sys.argv[1]
path = Path(os.path.abspath(sys.argv[-1]))

with open('\\\\.\\' + path.drive, 'rb+') as drive:
  with lock_volume(drive):
    try:
      fs = fat32.Drive(drive)
    except AssertionError:
      print('Not a FAT32 file system')
      sys.exit(1)
      
    root = fs.root_dir()
    file = get_file(root, str(path))
    if command == 'hide':
      hide(file)
    elif command == 'restore':
      restore(file)
    else:
      print('Invalid command')
