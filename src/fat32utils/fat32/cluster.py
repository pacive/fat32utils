from .location import Fat32Location
from .utils import chunk_data

class Fat32Cluster:
  def __init__(self, fs, number):
    self.fs = fs
    self.number = number
    self.location = Fat32Location.of_cluster(fs.bpb, number)

  def read(self, offset = 0, length = None):
    sector_offset = offset // self.fs.bpb.bytes_per_sector()
    start_location = self.location.plus_bytes(offset)

    if length is None or length > self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster():
      length = self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster() - offset
    
    total_length = length + (self.fs.bpb.bytes_per_sector() - length % self.fs.bpb.bytes_per_sector()) + sector_offset * self.fs.bpb.bytes_per_sector()

    self.fs.fs.seek(start_location.with_byte(0).abs_byte())
    data = self.fs.fs.read(total_length)

    return data[start_location.byte:start_location.byte + length]

  def write(self, data, offset = 0):
    start_location = self.location.plus_bytes(offset)
    length = len(data)
    chunk_offsets = chunk_data(length, self.fs.bpb.bytes_per_sector(), start_location.byte)

    for i, offsets in enumerate(chunk_offsets):
      start = offset if i == 0 else 0
      end = offsets[1] - offsets[0]
      sector = self.fs.read_sector(start_location.sector + i)
      sector[start:end] = data[offsets[0]:offsets[1]]
    
    return self.fs.flush_cache()
