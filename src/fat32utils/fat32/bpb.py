from .constants import LE

class Fat32BPB:
  def __init__(self, boot_sector: bytes):
    self.bpb = boot_sector[0xb:0x5a]

  def bytes_per_sector(self):
    return int.from_bytes(self.bpb[:0x2], LE)

  def sectors_per_cluster(self):
    return int(self.bpb[2])

  def reserved_sectors(self):
    return int.from_bytes(self.bpb[0x3:0x5], LE)

  def number_of_fats(self):
    return int(self.bpb[0x5])

  def total_sectors(self):
    return int.from_bytes(self.bpb[0x15:0x19], LE)
  
  def sectors_per_fat(self):
    return int.from_bytes(self.bpb[0x19:0x1d], LE)

  def root_dir_cluster(self):
    return int.from_bytes(self.bpb[0x21:0x25], LE)

  def fat_sector(self):
    return [self.reserved_sectors() + i * self.sectors_per_fat() for i in range(self.number_of_fats())]

  def root_dir_sector(self):
    return self.reserved_sectors() + self.number_of_fats() * self.sectors_per_fat()

  def signature_byte(self):
    return int(self.bpb[0x37])

  def filesystem_type(self):
    return self.bpb[0x47:0x4f]
