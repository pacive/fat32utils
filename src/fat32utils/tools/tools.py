import errno
import os
import msvcrt
import win32file
import winioctlcon
import contextlib

from fat32utils.fat32 import Cluster, Directory, Drive, File
from fat32utils.fat32.constants import LE
from fat32utils.fat32.utils import to_dos_date, to_dos_time, to_dos_time_ms, from_dos_date, from_dos_datetime, from_dos_time_ms

MAGIC_MARK = 0x84b5

@contextlib.contextmanager
def open_drive(path):
  with open('\\\\.\\' + path.drive, 'rb+') as drive:
    handle = msvcrt.get_osfhandle(drive.fileno())
    try:
      win32file.DeviceIoControl(handle, winioctlcon.FSCTL_LOCK_VOLUME, None, None)
      try:
        fs = Drive(drive)
      except ValueError as ve:
        print(ve)
      else:
        yield fs
      finally:
        win32file.DeviceIoControl(handle, winioctlcon.FSCTL_UNLOCK_VOLUME, None, None)
    except:
      raise PermissionError(errno.EPERM, os.strerror(errno.EPERM), drive.name)

def find(dir: Directory, file: str, include_deleted = False) -> File:
  for f in dir.get_files():
    if not f.meta.is_deleted() and file in [f.meta.filename(), f.meta.full_name()]:
      return f
    if include_deleted and file[1:] in [f.meta.filename()[1:], f.meta.full_name()[1:]]:
      return f
  raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file)

def cd(dir: Directory, subdir: str) -> Directory:
  d = find(dir, subdir)
  if isinstance(d, Directory):
    return d
  
  raise NotADirectoryError(errno.ENOTDIR, os.strerror(errno.ENOTDIR), subdir)


def get_file(root: Directory, path, include_deleted = False) -> File:
  parts = path.parts[1:]

  if len(parts) == 0:
    return root

  current_dir = root
  for dir in parts[:-1]:
    current_dir = cd(current_dir, dir)
  
  return find(current_dir, parts[-1], include_deleted)

def pretty_print(file: File, short = True):
  if short:
    return (file.meta.filename(), print_attrs(file.meta), file.meta.size)
  else:
    return (f'Name:                {file.meta.filename()}\n',
            f'DOS short name:      {file.meta.full_name()}\n',
            'Attributes:\n',
            print_attrs(file.meta, False),
            f'Create time:         {(from_dos_datetime(file.meta.ctime + file.meta.cdate) + from_dos_time_ms(file.meta.ctime_ms)).isoformat()}\n',
            f'Last access date:    {from_dos_date(file.meta.adate).isoformat()}\n',
            f'Modify time:         {from_dos_datetime(file.meta.mtime + file.meta.mdate).isoformat()}\n',
            f'Clusters:            {str([cluster.number for cluster in file.clusters])}\n',
            f'Size:                {file.meta.size}\n',
            f'File entry location: {file.meta.location.sector} + {file.meta.location.byte}')

def print_attrs(meta, short = True):
  if short:
    return (f"--{'a' if meta.is_archive() else '-'}"
            f"{'d' if meta.is_directory() else '-'}"
            f"{'v' if meta.is_volume_label() else '-'}"
            f"{'s' if meta.is_system() else '-'}"
            f"{'h' if meta.is_hidden() else '-'}"
            f"{'r' if meta.is_readonly() else '-'}")
  else:
    return ''.join(('  readonly\n' if meta.is_readonly() else '',
                    '  hidden\n' if meta.is_hidden() else '',
                    '  system\n' if meta.is_system() else '',
                    '  volume label\n' if meta.is_volume_label() else '',
                    '  directory\n' if meta.is_directory() else '',
                    '  archive\n' if meta.is_archive() else ''))

def ls(dir, recurse = False, all = False, level = 0) -> None:
  rows = []
  for file in dir.get_files():
    if all or not file.meta.is_deleted():
      rows.append((level, pretty_print(file)))
      if isinstance(file, Directory) and recurse and not file.meta.short_name.strip() in [b'.', b'..']:
        rows += ls(file, recurse, all, level + 1)
  return rows

# def mkfile(dir, name, **kwargs):
#   dt = datetime.now()
#   opts = {'extension': b'   ', 'attributes': 0x0, 'case_info': 0x24, 'ctime_ms': to_dos_time_ms(dt),
#               'ctime': to_dos_time(dt), 'cdate': to_dos_date(dt), 'adate': to_dos_date(dt), 'mtime': to_dos_time(dt),
#               'mdate': to_dos_date(dt), 'size': 0x0 }
#   opts.update(kwargs)

#   clusters = opts['size'] // (dir.fs.bpb.bytes_per_sector() * dir.fs.bpb.sectors_per_cluster())

def repoint(file: File, to_cluster: int = 0, set_size: int = 0) -> tuple[int, int]:
  orig_cluster = file.meta.start_cluster
  orig_size = file.meta.size
  file.meta.start_cluster = to_cluster
  file.meta.size = set_size
  file.write_metadata()
  return orig_cluster, orig_size

def hide(file: File) -> None:
  cluster = Cluster(file.fs, file.fs.fat.allocate())
  orig_cluster, orig_size = repoint(file, cluster.number, 10)
  cluster.write(MAGIC_MARK.to_bytes(2, LE) + orig_cluster.to_bytes(4, LE) + orig_size.to_bytes(4, LE))
  file.fs.flush_cache()

def restore(file: File) -> bool:
  data = file.read(10)
  if int.from_bytes(data[0:2], LE) != MAGIC_MARK:
    return False
  orig_cluster = int.from_bytes(data[2:6], LE)
  orig_size = int.from_bytes(data[6:10], LE)
  file.write(b"\x00" * 10)
  repoint(file, orig_cluster, orig_size)
  file.fs.fat.free(file.clusters[0].number)
  file.fs.flush_cache()
  return True

def mark_deleted(file: File) -> None:
  filename = file.meta.short_name
  file.meta.short_name = b'\xe5' + filename[1:]
  file.write_metadata()

def unmark_deleted(file: File, orig_filename) -> None:
  file.meta.short_name = bytes(orig_filename[0].upper(), 'ansi') + file.meta.short_name[1:]
  file.write_metadata()

def set_time(file: File, ctime = None, atime = None, mtime = None):
  if ctime is not None:
    file.meta.ctime_ms = to_dos_time_ms(ctime)
    file.meta.ctime = to_dos_time(ctime)
    file.meta.cdate = to_dos_date(ctime)
  
  if atime is not None:
    file.meta.adate = to_dos_date(atime)

  if mtime is not None:
    file.meta.mtime = to_dos_time(mtime)
    file.meta.mdate = to_dos_date(mtime)

  file.write_metadata()
