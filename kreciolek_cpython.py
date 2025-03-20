import board, neopixel, time

"""ustawienia pierscienia"""
led_num = 16
pinout = board.D5
ring = neopixel.NeoPixel(pinout, led_num)

n = 0
while(True):
    n += 1
    if n == 16: n = 0

    for j in range(10):
        m = n + j
        if m > 15:
            m = m - 16

        ring[m] = (0, 0, j*28)
    ring.write()

    time.sleep(0.1) #nie mam pojecia jak to zrobic bez timera