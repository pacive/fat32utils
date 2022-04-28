class Fat32Location:
  @staticmethod
  def of_cluster(bpb, n):
    sector = bpb.root_dir_sector() + (n - bpb.root_dir_cluster()) * bpb.sectors_per_cluster()
    return Fat32Location(bpb, sector, 0)

  @staticmethod
  def of_fat_cluster(bpb, fat_no, n):
    sector = bpb.fat_sector()[fat_no] + (n * 4) // bpb.bytes_per_sector()
    byte = (n * 4) % bpb.bytes_per_sector()
    return Fat32Location(bpb, sector, byte)

  def __init__(self, bpb, sector, byte):
    self.bpb = bpb
    self.sector = sector
    self.byte = byte

  def with_byte(self, byte):
    return Fat32Location(self.bpb, self.sector, byte)

  def plus_sectors(self, n):
    return Fat32Location(self.bpb, self.sector + n, self.byte)

  def plus_bytes(self, n):
    sector = self.sector + n // self.bpb.bytes_per_sector()
    byte = self.byte + n % self.bpb.bytes_per_sector()
    return Fat32Location(self.bpb, sector, byte)

  def abs_byte(self):
    return self.sector * self.bpb.bytes_per_sector() + self.byte

