import machine, neopixel

"""ustawienia pierscienia"""
led_num = 16
pinout = 5
ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)

def wheel(pos):
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

while True:
    for j in range(255):
        for i in range(led_num):
            rc_index = (i * 256 // led_num) - j #zmien na "+ j" jesli ma sie krecic w druga strone
            ring[i] = wheel(rc_index & 255)
        ring.write()