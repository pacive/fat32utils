import os
import sys
from pathlib import Path
from . import fat32
from .fat32.tools import *
from .usage import print_usage

sys.argv.pop(0)
command = sys.argv.pop(0)
path = Path(os.path.abspath(sys.argv.pop()))
options = {}
for i in range(0, len(sys.argv), 2):
  options[sys.argv[i].removeprefix('--')] = sys.argv[i + 1]

with open('\\\\.\\' + path.drive, 'rb+') as drive:
  with lock_volume(drive):
    try:
      fs = fat32.Drive(drive)
    except AssertionError:
      print('Not a FAT32 file system')
      sys.exit(1)
    
    root = fs.root_dir()
    if command == 'hide':
      file = get_file(root, path)
      hide(file)
      print(f'{path} has been hidden')
    elif command == 'restore':
      file = get_file(root, path)
      if restore(file):
        print(f'{path} has been restored')
      else:
        print(f"Unable to restore {path}: magic mark does not match. Perhaps it's restored already?")
    elif command == 'repoint':
      file = get_file(root, path)
      cluster = int(options.get('to-cluster', 0))
      size = int(options.get('size', 0))
      orig_cluster, orig_size = repoint(file, cluster, size)
      print(f"{path} has been repointed to a different cluster. To revert, use the following command:")
      print(f"python -m fat32utils repoint --to-cluster {orig_cluster} --size {orig_size} {path}")
    elif command == 'delete':
      file = get_file(root, path)
      mark_deleted(file)
      print(f'{path} is marked as deleted')
    elif command == 'undelete':
      filename = path.parts[-1]
      try:
        file = get_file(root, path, True)
      except FileNotFoundError:
        searched_file = path.parent / (b"\xe5" + bytes(filename[1:], 'ansi'))
        file = get_file(root, searched_file, True)
      unmark_deleted(file, filename)
      print(f'{path} is not marked as deleted')
    elif command == 'help':
      print_usage()
    else:
      print('Invalid command')
      print_usage()
