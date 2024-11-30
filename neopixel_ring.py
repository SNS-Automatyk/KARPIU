import machine, neopixel, time

"""ustawienia pierscienia"""
led_num = 16
pinout = 5
ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)

sent = False #wiadomosc

"""flash"""
for i in range(led_num):
    ring[i] = (255, 255, 255)
ring.write()

time.sleep(3) #tymczasowo

for i in range(led_num):
    ring[i] = (0, 0, 0)
ring.write()

"""animacja krecenia"""
"""mysle ze trzeba tu dac While ktory zakonczy sie po probie wyslania wiadomosci"""
"""i dac na poczatku i =+ 1"""
for i in range(50): #to zmieniasz na w zaleznosci ile ma trwac
    n = i % 15
    for j in range(10):
        m = n + j
        if m > 15:
            m = m - 16

        ring[m] = (0, 0, j*28)
    ring.write()
             
    time.sleep_ms(100) #nie mam pojecia jak to zrobic bez timera

"""status wiadomosci"""
if sent:
    for i in range(led_num):
        ring[i] = (0, 255, 0)
    ring.write()
else:
    for i in range(led_num):
        ring[i] = (255, 0, 0)
    ring.write()