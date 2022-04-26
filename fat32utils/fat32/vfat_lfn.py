class Fat32VFatLfn:
  def __init__(self, data, location):
    self.seqno = int(data[0]) & 0xf
    self.last_entry = (data[0] & 0x40) > 0
    self.text = data[0x1:0xb] + data[0xe:0x1a] + data[0x1c:0x20]
    self.checksum = int(data[0xd])
    self.location = location
