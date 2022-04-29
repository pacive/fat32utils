class Fat32VFatLfn:
  def __init__(self):
    self.segments = []

  def add_segment(self, segment):
    self.segments.append(segment)

  def empty(self):
    return len(self.segments) == 0

  def filename(self):
    if self.empty():
      return None
    fn = ''
    for segment in reversed(self.segments):
      fn += segment.get_text()

    return fn

class Fat32VFatLfnSegment:
  def __init__(self, data, location):
    self.seqno = int(data[0]) & 0xf
    self.last_entry = (data[0] & 0x40) > 0
    self.text = data[0x1:0xb] + data[0xe:0x1a] + data[0x1c:0x20]
    self.checksum = int(data[0xd])
    self.location = location

  def get_text(self):
    return self.text.rstrip(b'\xff').decode('utf-16le').rstrip('\x00')