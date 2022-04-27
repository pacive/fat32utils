from datetime import datetime
from msilib.schema import Directory
import msvcrt
import win32file
import winioctlcon
import contextlib

import fat32
from fat32.utils import to_dos_date, to_dos_time, to_dos_time_ms

MAGIC_MARK = 0x84b5

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


def find(dir: fat32.Directory, file: str):
  for f in dir.get_files():
    if file in [f.lfn.filename(), f.meta.full_name()]:
      return f
  raise FileNotFoundError

def cd(dir: fat32.Directory, subdir: str):
  d = find(dir, subdir)
  return d if isinstance(d, fat32.Directory) else None

def get_file(root: fat32.Directory, path: str):
  parts = path.split('\\')
  if ':' in parts[0]:
    parts.pop(0)

  current_dir = root
  for dir in parts[:-1]:
    current_dir = cd(current_dir, dir)
  
  return find(current_dir, parts[-1])


def ls(dir, recurse = False, level = 0):
  prefix = "\t" * level
  for file in dir.get_files():
    if not file.meta.deleted():
      if file.lfn:
        filename = file.lfn.filename()
      else:
        filename = file.meta.full_name()
      if isinstance(file, fat32.Directory):
        print(f"{prefix}{filename} attrs: {file.meta.attributes}")
        if recurse and file.meta.short_name[0] != 46:
          ls(file, True, level + 1)
      else:
        print(f"{prefix}{filename} attrs: {file.meta.attributes} size: {file.meta.size}")

def mkfile(dir, name, **kwargs):
  dt = datetime.now()
  opts = {'extension': b'   ', 'attributes': 0x0, 'case_info': 0x24, 'ctime_ms': to_dos_time_ms(dt),
              'ctime': to_dos_time(dt), 'cdate': to_dos_date(dt), 'adate': to_dos_date(dt), 'mtime': to_dos_time(dt),
              'mdate': to_dos_date(dt), 'size': 0x0 }
  opts.update(kwargs)

  clusters = opts['size'] // (dir.fs.bpb.bytes_per_sector() * dir.fs.bpb.sectors_per_cluster())

def hide(file: fat32.File):
  orig_cluster = file.meta.start_cluster
  orig_size = file.meta.size
  cluster = fat32.Cluster(file.fs, file.fs.fat.allocate())
  cluster.write(MAGIC_MARK.to_bytes(2, fat32.LE) + orig_cluster.to_bytes(4, fat32.LE) + orig_size.to_bytes(4, fat32.LE))
  file.meta.start_cluster = cluster.number
  file.meta.size = 10
  file.write_metadata()
  file.fs.flush_cache()

def restore(file: fat32.File):
  data = file.read(10)
  if int.from_bytes(data[0:2], fat32.LE) != MAGIC_MARK:
    return False
  orig_cluster = int.from_bytes(data[2:6], fat32.LE)
  orig_size = int.from_bytes(data[6:10], fat32.LE)
  file.write(b"\x00" * 10)
  file.meta.start_cluster = orig_cluster
  file.meta.size = orig_size
  file.write_metadata()
  file.fs.fat.free(file.clusters[0].number)
  file.fs.flush_cache()
  return True
