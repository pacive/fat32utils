import fat32

class Fat32Metadata:
  ATTR_READONLY = 0x1
  ATTR_HIDDEN = 0x2
  ATTR_SYSTEM = 0x4
  ATTR_VOLUMELABEL = 0x8
  ATTR_DIR = 0x10
  ATTR_ARCHIVE = 0x20
  LCASE_NAME = 0x8
  LCASE_EXT = 0x16

  VFAT_LFN = ATTR_READONLY | ATTR_HIDDEN | ATTR_SYSTEM | ATTR_VOLUMELABEL

  def __init__(self, data, location):
    self.short_name = data[0x0:0x8]
    self.extension = data[0x8:0xb]
    self.attributes = int(data[0xb])
    self.case_info = int(data[0xc])
    self.ctime_ms = int(data[0xd])
    self.ctime = data[0xe:0x10]
    self.cdate = data[0x10:0x12]
    self.adate = data[0x12:0x14]
    self.mtime = data[0x16:0x18]
    self.mdate = data[0x18:0x1a]
    self.start_cluster = int.from_bytes(data[0x1a:0x1c] + data[0x14:0x16], fat32.LE)
    self.size = int.from_bytes(data[0x1c:0x20], fat32.LE)
    self.location = location

  def readonly(self):
    return bool(self.attributes & self.ATTR_READONLY)

  def hidden(self):
    return bool(self.attributes & self.ATTR_HIDDEN)

  def system(self):
    return bool(self.attributes & self.ATTR_SYSTEM)

  def volume_label(self):
    return bool(self.attributes & self.ATTR_VOLUMELABEL)

  def directory(self):
    return bool(self.attributes & self.ATTR_DIR)

  def archive(self):
    return bool(self.attributes & self.ATTR_ARCHIVE)

  def vfat_lfn(self):
    return bool(self.attributes & self.VFAT_LFN)

  def deleted(self):
    return self.short_name[0] == 0xe5

  def lowercase_name(self):
    return bool(self.case_info & self.LCASE_NAME)

  def lowercase_extension(self):
    return bool(self.case_info & self.LCASE_EXT)

  def full_name(self):
    name = self.short_name.decode('ansi').strip()
    ext = self.extension.decode('ansi').strip()
    name = name.lower() if self.lowercase_name() else name
    ext = ext.lower() if self.lowercase_extension() else ext
    return f'{name}.{ext}' if len(ext) > 0 else name

  def encode(self):
    cluster = self.start_cluster.to_bytes(4, fat32.LE)
    data = self.short_name + self.extension + self.attributes.to_bytes(1, fat32.LE) + self.case_info.to_bytes(1, fat32.LE) + \
           self.ctime_ms.to_bytes(1, fat32.LE) + self.ctime + self.cdate + self.adate + cluster[2:] + \
           self.mtime + self.mdate + cluster[:2] + self.size.to_bytes(4, fat32.LE)
    return data

  def filename_checksum(self):
    sum = 0
    for c in (self.short_name + self.extension):
      sum = (((sum & 1) << 7) + (sum >> 1) + c) % 256

    return sum
    