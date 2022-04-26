from fat32.file import Fat32File
from fat32.metadata import Fat32Metadata as Metadata
from fat32.vfat_lfn import Fat32VFatLfn as VFatLfn
from fat32.location import Fat32Location as Location
from fat32.cluster import Fat32Cluster as Cluster

class Fat32Dir(Fat32File):
  def __init__(self, fs, meta):
    super().__init__(fs, meta)
    self.entries = []
    if self.meta.volume_label():
      cluster = self.fs.bpb.root_dir_cluster()
      self.clusters = [Cluster(fs, cluster)]
    else:
      cluster = self.meta.start_cluster()
    location = Location.of_cluster(self.fs.bpb, cluster)
    data = self.fs.read_cluster(cluster)
    i = 0
    while entry := data[i:i+32]:
      if entry[0] == 0:
        break
      if int(entry[0xb]) & 15 == 15:
        self.entries.append(VFatLfn(entry, location.with_byte(i)))
      else:
        self.entries.append(Metadata(entry, location.with_byte(i)))
      i += 32

  def get_files(self):
    return [self.fs.get_file(entry) for entry in self.entries if isinstance(entry, Metadata)]