class Fat32VFatLfnSegment:
  def __init__(self, data, location):
    self.seqno = int(data[0]) & 0x1f
    self.last_entry = bool(data[0] & 0x40)
    self.text = data[0x1:0xb] + data[0xe:0x1a] + data[0x1c:0x20]
    self.checksum = int(data[0xd])
    self.location = location

  def get_text(self):
    return self.text.rstrip(b'\xff').decode('utf-16le')

class Fat32VFatLfn:
  def __init__(self):
    self.segments: list[Fat32VFatLfnSegment] = []

  def add_segment(self, segment: Fat32VFatLfnSegment):
    self.segments.append(segment)

  def empty(self):
    return len(self.segments) == 0

  def filename(self):
    if self.empty():
      return None
    fn = ''
    for segment in reversed(self.segments):
      fn += segment.get_text()

    return fn.rstrip('\x00').strip()

  def validate(self, checksum: int):
    seqno = 0
    for i, segment in enumerate(self.segments):
      if segment.seqno != 0xe5:
        if i == 0:
          if not segment.last_entry:
            return False
        else:
          if segment.seqno != seqno - 1:
            return False
      if checksum != 0 and segment.checksum != checksum:
        return False
      seqno = segment.seqno
    
    return True
