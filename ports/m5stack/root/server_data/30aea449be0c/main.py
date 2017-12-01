import m5, time

m5.print('Hi  M5Stack!', 2, 50)
# m5.print('Hello M5Stack!', 2, 150)
m5.fillRect(0, 100, 100, 100, 0xff0000)
# m5.fillRect(100, 100, 100, 100, 0x00ff00)
m5.fillRect(200, 100, 100, 100, 0x0000ff)
# m5.drawRect(200, 50, 100, 100, 0x0000ff)
for i in range(0, 0xffffff, 1000):
    m5.fillRect(200, 100, 100, 100, i)
    time.sleep_ms(100)