from fat32 import LE
from fat32.location import Fat32Location as Location

class Fat32FAT:
  EOC = 0x0fffffff
  EOC_MIN = 0x0ffffff8

  def __init__(self, fs, fat_no):
    self.fs = fs
    self.fat_no = fat_no
    self.start_sector = fs.bpb.fat_sector()[fat_no]
  
  def read_cluster(self, n, cache = True):
    location = Location.of_fat_cluster(self.fs.bpb, self.fat_no, n)
    sector_data = self.fs.read_sector(location.sector, cache)
    return int.from_bytes(sector_data[location.byte:location.byte + 4], LE)

  def first_free_cluster(self, start_cluster = 0, cache = False):
    location = Location.of_fat_cluster(self.fs.bpb, self.fat_no, start_cluster)
    byte_offset = location.byte
    for s in range(location.sector, self.start_sector + self.fs.bpb.sectors_per_fat()):
      sector = self.fs.read_sector(s, cache)
      for c in range(byte_offset, self.fs.bpb.bytes_per_sector(), 4):
        cluster = int.from_bytes(sector[c:c + 4], LE)
        if cluster == 0:
          return c // 4
      byte_offset = 0
      if cache:
        self.fs.clear_cache(s)

    return None

  def get_file_clusters(self, meta):
    clusters = [meta.start_cluster]
    while (fat_cluster := self.read_cluster(clusters[-1])) < self.EOC_MIN:
      clusters.append(fat_cluster)
    return clusters

  def set_cluster(self, cluster, value):
    location = Location.of_fat_cluster(self.fs.bpb, self.fat_no, cluster)
    sector = self.fs.read_sector(location.sector, True)
    sector[location.byte:location.byte + 4] = value.to_bytes(4, LE)

  def allocate(self, n = 1, cluster_offset = 0):
    start_cluster = self.first_free_cluster(cluster_offset, True)
    clusters = [start_cluster]
    alloc = 1
    while alloc < n:
      cluster_index = clusters[-1] + 1
      cluster_data = self.read_cluster(cluster_index)
      if cluster_data == 0:
        clusters.append(cluster_index)
      else:
        clusters.append(self.first_free_cluster(cluster_index, True))
      alloc += 1
    i = 0
    print(clusters)
    while i < len(clusters) - 1:
      print(i)
      self.set_cluster(clusters[i], clusters[i + 1])
      i += 1
    self.set_cluster(clusters[i], self.EOC)
    return self.fs.flush_cache()