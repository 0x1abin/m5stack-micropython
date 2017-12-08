
def crc_1byte(data):
  crc_1byte = 0
  for i in range(0,8):
    if((crc_1byte^data)&0x01):
      crc_1byte ^= 0x18
      crc_1byte >>= 1
      crc_1byte |= 0x80
    else:
      crc_1byte >>= 1
    data >>= 1
  return crc_1byte

def crc_byte(data):
  ret = 0
  for byte in data:
    ret = (crc_1byte(ret^byte))
  return ret

