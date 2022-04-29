import os
import sys
from pathlib import Path
from datetime import datetime
from .tools import *
from .usage import print_usage
from .fat32.utils import from_dos_date, from_dos_datetime, from_dos_time_ms

def do_hide(root, path, *_):
  file = get_file(root, path)
  hide(file)
  print(f'{path} has been hidden')

def do_restore(root, path, *_):
  file = get_file(root, path)
  if restore(file):
    print(f'{path} has been restored')
  else:
    print(f"Unable to restore {path}: magic mark does not match. Perhaps it's restored already?")

def do_delete(root, path, *_):
  file = get_file(root, path)
  mark_deleted(file)
  print(f'{path} is marked as deleted')

def do_undelete(root, path, *_):
  filename = path.parts[-1]
  file = get_file(root, path, True)
  unmark_deleted(file, filename)
  print(f'{path} is not marked as deleted')

def do_repoint(root, path, **options):
  file = get_file(root, path)
  cluster = int(options.get('to-cluster', 0))
  size = int(options.get('size', 0))
  orig_cluster, orig_size = repoint(file, cluster, size)
  print(f"{path} has been repointed to a different cluster. To revert, use the following command:")
  print(f"fat32utils repoint --to-cluster {orig_cluster} --size {orig_size} {path}")

def show_info(root, path, *_):
  file = get_file(root, path)
  print(
    f'Name:                {file.meta.filename()}\n',
    f'DOS short name:      {file.meta.full_name()}\n',
    'Attributes:\n',
    '  readonly\n' if file.meta.is_readonly() else '',
    '  hidden\n' if file.meta.is_hidden() else '',
    '  system\n' if file.meta.is_system() else '',
    '  volume label\n' if file.meta.is_volume_label() else '',
    '  directory\n' if file.meta.is_directory() else '',
    '  archive\n' if file.meta.is_archive() else '',
    f'Create time:         {(from_dos_datetime(file.meta.ctime + file.meta.cdate) + from_dos_time_ms(file.meta.ctime_ms)).isoformat()}\n',
    f'Last access date:    {from_dos_date(file.meta.adate).isoformat()}\n',
    f'Modify time:         {from_dos_datetime(file.meta.mtime + file.meta.mdate).isoformat()}\n',
    f'Clusters:            {str([cluster.number for cluster in file.clusters])}\n',
    f'Size:                {file.meta.size}\n',
    f'File entry location: {file.meta.location.sector} + {file.meta.location.byte}',
    sep = ''
  )

def do_set_time(root, path, **options):
  file = get_file(root, path)
  datetimes = {}
  for key, time_str in options.items():
    datetimes[key] = datetime.fromisoformat(time_str)

  set_time(file, **datetimes)


COMMANDS = { 'hide': do_hide,
             'restore': do_restore,
             'repoint': do_repoint,
             'delete': do_delete,
             'undelete': do_undelete,
             'info': show_info,
             'settime': do_set_time }

def parse_args(args: list[str]):
  command = args.pop(0) if len(args) else 'help'

  if command not in COMMANDS:
    return ('help', None, { 'command': args[0] }) if len(args) else ('help', None, { 'command': None })

  path = Path(os.path.abspath(args.pop())) if len(args) else None

  options = {}
  while len(args) > 0:
    key = args.pop(0).removeprefix('--')
    if not args[0].startswith('--'):
      options[key] = args.pop(0)
    else:
      options[key] = True

  return command, path, options

def main():
  command, path, options = parse_args(sys.argv[1:])

  if command == 'help':
    print_usage(**options)
    exit(0)
  elif path is None:
    print('No file specified')
    print_usage(command = command)
    exit(1)

  with open_drive(path) as fs:
    root = fs.root_dir()
    COMMANDS[command](root, path, **options)

if __name__ == '__main__':
  main()