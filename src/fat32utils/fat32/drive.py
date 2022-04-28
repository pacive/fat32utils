from .bpb import Fat32BPB
from .directory import Fat32Dir
from .file import Fat32File
from .metadata import Fat32Metadata
from .fat import Fat32FAT
from .location import Fat32Location

class Fat32Drive:
  def __init__(self, io_obj):
    self.fs = io_obj
    self.bpb = Fat32BPB(self.fs.read(512))
    self.verify_fs()
    self.fats = [Fat32FAT(self, i) for i in range(self.bpb.number_of_fats())]
    self.fat = self.fats[0]
    self.cache = {}

  def root_dir(self):
    location = Fat32Location.of_cluster(self.bpb, self.bpb.root_dir_cluster())
    return Fat32Dir(self, Fat32Metadata(self.read_sector(location.sector)[:32], location))

  def get_file(self, meta):
    return Fat32File(self, meta)

  def read_cluster(self, n):
    location = Fat32Location.of_cluster(self.bpb, n)
    self.fs.seek(location.abs_byte())
    return self.fs.read(self.bpb.bytes_per_sector() * self.bpb.sectors_per_cluster())

  def read_sector(self, n, cache = True):
    if cache:
      if n in self.cache:
        return self.cache[n]
      else:
        return self.cache_sector(n)
    else:
      self.fs.seek(n * self.bpb.bytes_per_sector())
      return self.fs.read(self.bpb.bytes_per_sector())

  def cache_sector(self, sector_offset):
    self.cache[sector_offset] = bytearray(self.read_sector(sector_offset, False))
    return self.cache[sector_offset]

  def clear_cache(self, sector = None):
    if sector == None:
      self.cache.clear()
    elif sector in self.cache:
      del self.cache[sector]

  def flush_cache(self):
    bytes_written = 0
    for sector, data in self.cache.items():
      bytes_written += self.write_sector(sector, data)
    self.fs.flush()
    self.clear_cache()
    return bytes_written

  def write_sector(self, n, data):
    self.fs.seek(n * self.bpb.bytes_per_sector())
    return self.fs.write(data)

  def verify_fs(self):
    valid_fat = self.bpb.bytes_per_sector() in [512, 1024, 2048, 4096] and \
                self.bpb.sectors_per_cluster() in [1, 2, 4, 8, 16, 32, 64, 128] and \
                self.bpb.bytes_per_sector() * self.bpb.sectors_per_cluster() < 32 * 1024
    if not valid_fat:
      raise AssertionError()
                
