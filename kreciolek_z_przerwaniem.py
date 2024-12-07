import machine, neopixel
from machine import Timer, Pin

"""ustawienia pierscienia"""
led_num = 16
pinout = 5
ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)

pin_button = 17
button = Pin(pin_button, mode=Pin.IN, pull=Pin.PULL_DOWN)

timer1 = Timer(0)

n = 0
def move_one(timer1):
    global n
    n += 1
    if n == 16: n = 0

    for j in range(10):
        m = n + j
        if m > 15:
            m = m - 16

        ring[m] = (0, 0, j*28)
    ring.write()

timer1.init(period=100, mode=Timer.PERIODIC, callback=move_one)

while True:
    if button.value() == 1: 
        timer1.deinit()
        for i in range(led_num):
            ring[i] = (0, 0, 0)
        ring.write()
        break