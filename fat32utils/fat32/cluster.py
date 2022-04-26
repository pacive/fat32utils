from fat32.location import Fat32Location as Location

class Fat32Cluster:
  def __init__(self, fs, number):
    self.fs = fs
    self.number = number
    self.location = Location.of_cluster(fs.bpb, number)

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
    total_length = (start_location.byte + length)
    total_length += total_length + (self.fs.bpb.bytes_per_sector() - total_length % self.fs.bpb.bytes_per_sector())
    num_sectors = total_length // self.fs.bpb.bytes_per_sector()

    if num_sectors == 1:
      sector = self.fs.read_sector(start_location.sector)
      sector[start_location.byte:start_location.byte + length] = data
    else:
      first_sector = self.fs.read_sector(start_location.sector)
      first_sector[offset:] = data[:self.fs.bpb.bytes_per_sector() - offset]
      i = 1
      while i < num_sectors - 1:
        sector = self.fs.read_sector(start_location.sector + i)
        sector = data[self.fs.bpb.bytes_per_sector() * i - offset:self.fs.bpb.bytes_per_sector() * (i + 1) - offset]
        i += 1
      last_sector = self.fs.read_sector(start_location.sector + i)
      last_sector[:len(data[self.fs.bpb.bytes_per_sector() * i - offset])] = data[self.fs.bpb.bytes_per_sector() * i - offset]
    
    return self.fs.flush_cache()
