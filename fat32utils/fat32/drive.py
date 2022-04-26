from fat32.bpb import Fat32BPB as BPB
from fat32.directory import Fat32Dir as Directory
from fat32.file import Fat32File as File
from fat32.metadata import Fat32Metadata as Metadata
from fat32.fat import Fat32FAT as FAT
from fat32.location import Fat32Location as Location

class Fat32Drive:
  def __init__(self, io_obj):
    self.fs = io_obj
    self.bpb = BPB(self.fs.read(512))
    self.fats = [FAT(self, i) for i in range(self.bpb.number_of_fats())]
    self.cache = {}

  def root_dir(self):
    location = Location.of_cluster(self.bpb, self.bpb.root_dir_cluster())
    return Directory(self, Metadata(self.read_sector(location.sector)[:32], location))

  def get_file(self, meta):
    return File(self, meta)

  def read_cluster(self, n):
    location = Location.of_cluster(self.bpb, n)
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
