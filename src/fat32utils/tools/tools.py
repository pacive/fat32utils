import sys
import msvcrt
import win32file
import winioctlcon
import contextlib

from fat32utils.fat32 import Cluster, Directory, Drive, File
from fat32utils.fat32.constants import LE
from fat32utils.fat32.utils import to_dos_date, to_dos_time, to_dos_time_ms

MAGIC_MARK = 0x84b5

@contextlib.contextmanager
def open_drive(path):
  with open('\\\\.\\' + path.drive, 'rb+') as drive:
    hVol = msvcrt.get_osfhandle(drive.fileno())
    win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_LOCK_VOLUME,
                              None, None)
    try:
      fs = Drive(drive)
      yield fs
    except AssertionError:
      print('Not a FAT32 file system')
      sys.exit(1)
    # except:
    #   print('Unable to open drive')
    #   sys.exit(1)
    finally:
      try: 
        drive.flush()
      finally:
        win32file.DeviceIoControl(hVol, winioctlcon.FSCTL_UNLOCK_VOLUME,
                                      None, None)

def find(dir: Directory, file: str, include_deleted = False) -> File:
  for f in dir.get_files():
    if not f.meta.is_deleted() and file in [f.meta.filename(), f.meta.full_name()]:
      return f
    if include_deleted and file[1:] in [f.meta.filename()[1:], f.meta.full_name()[1:]]:
      return f
  raise FileNotFoundError()

def cd(dir: Directory, subdir: str) -> Directory:
  d = find(dir, subdir)
  if isinstance(d, Directory):
    return d
  
  raise FileNotFoundError()


def get_file(root: Directory, path, include_deleted = False) -> File:
  parts = path.parts[1:]

  current_dir = root
  for dir in parts[:-1]:
    current_dir = cd(current_dir, dir)
  
  return find(current_dir, parts[-1], include_deleted)


def ls(dir, recurse = False, level = 0) -> None:
  prefix = "\t" * level
  for file in dir.get_files():
    if not file.meta.is_deleted():
      if isinstance(file, Directory):
        print(f"{prefix}{file.meta.filename()} attrs: {file.meta.attributes}")
        if recurse and file.meta.short_name[0] != 46:
          ls(file, True, level + 1)
      else:
        print(f"{prefix}{file.meta.filename()} attrs: {file.meta.attributes} size: {file.meta.size}")

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
