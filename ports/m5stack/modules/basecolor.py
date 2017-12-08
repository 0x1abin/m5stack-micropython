def color565(r, g, b):
    return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

black=color565(0,0,0)
gray=color565(190,190,190)
blue=color565(154,192,205)
white=color565(255,255,255)
red=color565(255,0,0)
green=color565(34,139,34)
