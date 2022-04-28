from .cluster import Fat32Cluster
from .location import Fat32Location
from .utils import chunk_data

class Fat32File:
  def __init__(self, fs, meta, lfn = None):
    self.fs = fs
    self.meta = meta
    self.lfn = lfn
    self.clusters = [Fat32Cluster(self.fs, c) for c in fs.fat.get_file_clusters(meta)]
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
    return Fat32Location(self.fs.bpb, self.pos // self.fs.bpb.bytes_per_sector(), self.pos % self.fs.bpb.bytes_per_sector())

  def write(self, data):
    cluster_size = self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster()
    start_cluster_index = self.pos // cluster_size
    offset = self.pos % cluster_size
    length = len(data)
    space_required = self.pos + length
    clusters_required = space_required // cluster_size + 1

    if clusters_required > len(self.clusters):
      self.extend(clusters_required - len(self.clusters))

    chunk_offsets = chunk_data(length, cluster_size, offset)
    total_bytes_written = 0

    for i, offsets in enumerate(chunk_offsets):
      start = offset if i == 0 else 0
      total_bytes_written = self.clusters[start_cluster_index + i].write(data[offsets[0]:offsets[1]], start)

    if space_required > self.meta.size:
      self.meta.size = space_required
      self.write_metadata()

    return total_bytes_written

  def write_metadata(self):
    sector = self.fs.read_sector(self.meta.location.sector)
    sector[self.meta.location.byte:self.meta.location.byte + 32] = self.meta.encode()
    return self.fs.flush_cache()
    
  def extend(self, clusters):
    alloc_clusters = self.fs.fat.get_file_clusters(self.meta)
    first_alloc_cluster = self.fs.fat.allocate(clusters, alloc_clusters[-2])
    self.fs.fat.set_cluster(alloc_clusters[-2], first_alloc_cluster)
    self.fs.flush_cache()
    return first_alloc_cluster