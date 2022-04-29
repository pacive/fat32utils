from .cluster import Fat32Cluster
from .file import Fat32File
from .location import Fat32Location
from .metadata import Fat32Metadata
from .vfat_lfn import Fat32VFatLfn, Fat32VFatLfnSegment

class Fat32Dir(Fat32File):
  def __init__(self, fs, meta: Fat32Metadata):
    super().__init__(fs, meta)
    self.entries = []
    if self.meta.is_volume_label():
      cluster = self.fs.bpb.root_dir_cluster()
      self.clusters = [Fat32Cluster(fs, cluster)]
    else:
      cluster = self.meta.start_cluster
    location = Fat32Location.of_cluster(self.fs.bpb, cluster)
    data = self.fs.read_cluster(cluster)
    i = 0
    lfn = Fat32VFatLfn()
    while entry := data[i:i+32]:
      if entry[0] == 0:
        break
      if int(entry[0xb]) & Fat32Metadata.VFAT_LFN == Fat32Metadata.VFAT_LFN:
        lfn.add_segment(Fat32VFatLfnSegment(entry, location.plus_bytes(i)))
      else:
        self.entries.append(Fat32Metadata(entry, location.plus_bytes(i), lfn))
        lfn = Fat32VFatLfn()
      i += 32

  def get_files(self):
    files = []
    for entry in self.entries:
      if isinstance(entry, Fat32Metadata):
        if entry.is_directory():
          files.append(Fat32Dir(self.fs, entry))
        else:
          files.append(Fat32File(self.fs, entry))

    return files

  def create_file(self, meta):
    clusters = meta.size // ((self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster())) + 1
    self.fs.fat.allocate(clusters, self.clusters[0].number)