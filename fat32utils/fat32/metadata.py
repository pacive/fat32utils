from fat32 import LE

class Fat32Metadata:
  ATTR_READONLY = 0x1
  ATTR_HIDDEN = 0x2
  ATTR_SYSTEM = 0x4
  ATTR_VOLUMELABEL = 0x8
  ATTR_DIR = 0x10
  ATTR_ARCHIVE = 0x20

  VFAT_LFN = ATTR_READONLY | ATTR_HIDDEN | ATTR_SYSTEM | ATTR_VOLUMELABEL

  def __init__(self, data, location):
    self.attributes = int(data[0xb])
    self.short_name = data[0x0:0x8]
    self.extension = data[0x8:0xb]
    self.ctime_ms = int(data[0xd])
    self.ctime = int.from_bytes(data[0xe:0x10], LE)
    self.cdate = int.from_bytes(data[0x10:0x12], LE)
    self.adate = int.from_bytes(data[0x12:0x14], LE)
    self.mtime = int.from_bytes(data[0x16:0x18], LE)
    self.mdate = int.from_bytes(data[0x18:0x1a], LE)
    self.start_cluster = int.from_bytes(data[0x1a:0x1c] + data[0x14:0x16], LE)
    self.size = int.from_bytes(data[0x1c:0x20], LE)
    self.location = location

  def readonly(self):
    return self.attributes & self.ATTR_READONLY > 0

  def hidden(self):
    return self.attributes & self.ATTR_HIDDEN > 0

  def system(self):
    return self.attributes & self.ATTR_SYSTEM > 0

  def volume_label(self):
    return self.attributes & self.ATTR_VOLUMELABEL > 0

  def directory(self):
    return self.attributes & self.ATTR_DIR > 0

  def archive(self):
    return self.attributes & self.ATTR_ARCHIVE > 0

  def vfat_lfn(self):
    return self.attributes & self.VFAT_LFN > 0

  def deleted(self):
    return self.short_name[0] == 0xe5

  def encode(self):
    data = self.short_name + self.extension + self.attributes.to_bytes(1, LE) + b"\x00"
    data += self.ctime_ms.to_bytes(1, LE) + self.ctime.to_bytes(2, LE) + self.cdate.to_bytes(2, LE) + self.adate.to_bytes(2, LE)
    cluster = self.start_cluster.to_bytes(4, LE)
    data += cluster[2:] + self.mtime.to_bytes(2, LE) + self.mdate.to_bytes(2, LE) + cluster[:2] + self.size.to_bytes(4, LE)
    return data
