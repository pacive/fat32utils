from fat32.cluster import Fat32Cluster as Cluster
from fat32.location import Fat32Location as Location

class Fat32File:
  def __init__(self, fs, meta):
    self.fs = fs
    self.meta = meta
    self.clusters = [Cluster(self.fs, c) for c in fs.fats[0].get_file_clusters(meta)]
    self.pos = 0

  def seek(self, pos):
    self.pos = pos

  def read(self, length = None):
    cluster_size = self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster()
    start_cluster_index = self.pos // cluster_size
    rel_pos_start = self.pos % cluster_size
    if length == None:
      length = self.meta.size

    end_cluster_index = start_cluster_index + (length // cluster_size)

    if start_cluster_index == end_cluster_index:
      data = self.clusters[start_cluster_index].read(rel_pos_start, length)
    else:
      data = self.clusters[start_cluster_index].read(rel_pos_start)
      for i in range(start_cluster_index + 1, end_cluster_index):
        data += self.clusters[i].read()
      data += self.clusters[end_cluster_index].read(length=length % cluster_size)

    return data
  
  def cursor_location(self):
    return Location(self.fs.bpb, self.pos // self.fs.bpb.bytes_per_sector(), self.pos % self.fs.bpb.bytes_per_sector())

  def write(self, data):
    cluster_size = self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster()
    start_cluster_index = self.pos // cluster_size
    offset = self.pos % cluster_size
    length = len(data)
    total_length = (offset + length)
    total_length += total_length + (cluster_size - total_length % cluster_size)
    num_clusters = (total_length // cluster_size)

    total_bytes_written = 0
    if num_clusters == 1:
      total_bytes_written = self.clusters[start_cluster_index].write(data, offset)
    else:
      total_bytes_written = self.clusters[start_cluster_index].write(data[:cluster_size - offset], offset)
      i = 1
      while i < num_clusters:
        total_bytes_written += self.clusters[i].write(data[cluster_size * i - offset:cluster_size * (i + 1) - offset])
        i += 1
      total_bytes_written += self.clusters[i].write(data[cluster_size * i - offset:])
    return total_bytes_written

    
    