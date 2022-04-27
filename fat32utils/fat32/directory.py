from .cluster import Fat32Cluster
from .file import Fat32File
from .location import Fat32Location
from .metadata import Fat32Metadata
from .vfat_lfn import Fat32VFatLfn, Fat32VFatLfnSegment

class Fat32Dir(Fat32File):
  def __init__(self, fs, meta: Fat32Metadata, lfn: Fat32VFatLfn = None):
    super().__init__(fs, meta, lfn)
    self.entries = []
    if self.meta.volume_label():
      cluster = self.fs.bpb.root_dir_cluster()
      self.clusters = [Fat32Cluster(fs, cluster)]
    else:
      cluster = self.meta.start_cluster
    location = Fat32Location.of_cluster(self.fs.bpb, cluster)
    data = self.fs.read_cluster(cluster)
    i = 0
    while entry := data[i:i+32]:
      if entry[0] == 0:
        break
      if int(entry[0xb]) & 15 == 15:
        self.entries.append(Fat32VFatLfnSegment(entry, location.with_byte(i)))
      else:
        self.entries.append(Fat32Metadata(entry, location.with_byte(i)))
      i += 32

  def get_files(self):
    files = []
    lfn = Fat32VFatLfn()
    for entry in self.entries:
      if isinstance(entry, Fat32VFatLfnSegment):
        lfn.add_segment(entry)
      elif isinstance(entry, Fat32Metadata):
        if entry.directory():
          files.append(Fat32Dir(self.fs, entry, lfn))
        else:
          files.append(Fat32File(self.fs, entry, lfn))
        lfn = Fat32VFatLfn()

    return files

  def create_file(self, meta):
    clusters = meta.size // ((self.fs.bpb.bytes_per_sector() * self.fs.bpb.sectors_per_cluster())) + 1
    self.fs.fat.allocate(clusters, self.clusters[0].number)