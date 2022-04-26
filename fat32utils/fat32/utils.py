from datetime import datetime, time, date
from fat32 import LE

def to_dos_date(dt):
  y = (dt.year - 1980) << 9
  m = dt.month << 5
  d = dt.day
  return (y + m + d).to_bytes(2, LE)

def to_dos_time(dt):
  h = dt.hour << 11
  m = dt.minute << 5
  s = dt.second // 2
  return (h + m + s).to_bytes(2, LE)

def to_dos_datetime(dt):
  return to_dos_time(dt) + to_dos_date(dt)

def from_dos_date(v):
  if isinstance(v, bytes):
    v = int.from_bytes(v, LE)
  y = (v >> 9) + 1980
  m = v >> 5 & 0xf
  d = v & 0xf
  return date(y, m, d)

def from_dos_time(v):
  if isinstance(v, bytes):
    v = int.from_bytes(v, LE)
  h = (v >> 11)
  m = (v >> 5) & 0x3f
  s = (v & 0xf) * 2
  print(h, m, s)
  return time(h, m, s)

def from_dos_datetime(v):
  if isinstance(v, bytes):
    t = from_dos_time(v[:2])
    d = from_dos_date(v[2:])
  else:
    t = from_dos_time(v >> 16)
    d = from_dos_date(v & 0xffff)

  return datetime.combine(d, t)
