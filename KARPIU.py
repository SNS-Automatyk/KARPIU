import neopixel
import machine
from machine import Pin, SPI, Timer
import camera
import os
import base64
import time
import sdcard
import umail
import network
import uos  

# Konfiguracja sieci i maila
ssid = "Automatyk"
password = "automatyk5n5"

sender_email = 'karpiunator@gmail.com'
sender_name = 'ESP32'
sender_app_password = 'iwpemdqmrccpaknw'
recipient_email = '275414@student.pwr.edu.pl'
email_subject = 'Karpiu test'

# Konfiguracja GPIO i SD
BUTTON_PIN = 0  # Przycisk na GPIO0
led_num = 16
pinout = 5

ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)
DELAY_TIME = 5000  # Opóźnienie w milisekundach
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

camera_timer = Timer(-1)
photo_taken = False  # Flaga wskazująca, czy zdjęcie zostało już wykonane
timer_active = False  # Flaga, aby zapobiec wielokrotnemu uruchamianiu tim era
ring_timer = Timer(0)
n = 0 

SD_CS_PIN = 21
SPI_MISO = 8
SPI_MOSI = 9
SPI_CLK = 7

spi = SPI(2, baudrate=20000000, sck=Pin(SPI_CLK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))

def move_one(ring_timer):
    global n
    n += 1
    if n == 15: n = 0
    
    for j in range(10):
        m = n + j
        if m > 15:
            m = m - 15
        ring[m] = (0, 0, j * 28)
    ring.write()

ring_timer.init(period=100, mode=Timer.PERIODIC, callback=move_one)

def on_timer(timer):
    """Uruchamiane po 5 sekundach od naciśnięcia przycisku"""
    global photo_taken, timer_active
    print("Timer uruchomiony.")  # Debugowanie
    if not photo_taken:
        print("Czas minął, wykonuję zdjęcie...")
        photo = take_photo()
        if photo:
            filename = f"photo_{int(time.time())}.jpg"
            filepath = save_photo_to_sd(photo, filename)
            if filepath:
                send_email_with_photo(filepath)  # Przekazujemy ścieżkę do pliku
            photo_taken = True  # Ustawiamy flagę, żeby zdjęcie było wykonane tylko raz
        else:
            print("Błąd: zdjęcie nie zostało wykonane.")  # Debugowanie błędu
    timer_active = False  # Reset flagi timera

def init_camera():
    """Inicjalizacja kamery"""
    try:
        camera.init()  # Inicjalizacja kamery
        camera.framesize(9)  # VGA (640x480) — dostosuj wartość w razie potrzeby
        camera.quality(10)  # Jakość obrazu: 1 (najwyższa jakość) do 63
        print("Kamera zainicjowana.")
    except Exception as e:
        print("Błąd inicjalizacji kamery:", e)

def init_sd():
    """Inicjalizuje i montuje kartę SD"""
    try:
        uos.mount(sd, "/sd")
        print("Karta SD zamontowana.")
    except Exception as e:
        print("Błąd montowania karty SD:", e)

def check_sd_mount():
    """Sprawdza, czy karta SD jest dostępna"""
    try:
        files = os.listdir('/sd')
        print("Pliki na karcie SD:", files)
    except Exception as e:
        print("Błąd podczas dostępu do karty SD:", e)

def take_photo():
    """Wykonuje zdjęcie"""
    print("Próba wykonania zdjęcia...")  # Debugowanie
    try:
        photo = camera.capture()
        if photo is None:
            print("Błąd: zdjęcie nie zostało zrobione.")  # Debugowanie
            raise ValueError("Nie udało się wykonać zdjęcia.")
        print("Zdjęcie wykonane.")  # Debugowanie
    except Exception as e:
        print("Błąd podczas wykonywania zdjęcia:", e)  # Debugowanie
        photo = None
    
    return photo

def save_photo_to_sd(photo, filename):
    """Zapisuje zdjęcie na kartę SD"""
    if not isinstance(photo, (bytes, bytearray)):
        print("Błąd: zdjęcie nie jest w formacie bajtowym.")
        return None
    try:
        filepath = f"/sd/{filename}"
        print(f"Zapisuję zdjęcie jako: {filepath}")
        with open(filepath, "wb") as file:
            file.write(photo)
        print(f"Zdjęcie zapisane na SD jako: {filepath}")
        return filepath
    except Exception as e:
        print("Błąd zapisu na SD:", e)
        return None

def send_email_with_photo(filepath):
    """Wysyła zdjęcie na podany adres e-mail"""
    print(f"Próba wysłania zdjęcia jako załącznik: {filepath}")  # Debugowanie
    try:
        with open(filepath, "rb") as photo_file:
            photo_data = photo_file.read()
        
        # Kodowanie zdjęcia w base64
        encoded_photo = base64.b64encode(photo_data).decode('utf-8')

        # Tworzenie wiadomości e-mail w formacie MIME
        message = f"""\
From: {sender_name} <{sender_email}>
To: {recipient_email}
Subject: {email_subject}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary"

--boundary
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

W załączeniu przesyłam zdjęcie wykonane przez ESP32.

--boundary
Content-Type: image/jpeg; name="{os.path.basename(filepath)}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{os.path.basename(filepath)}"

{encoded_photo}
--boundary--
"""

        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)  # Gmail's SSL port
        print("Połączono z serwerem SMTP...")  # Debugowanie
        smtp.login(sender_email, sender_app_password)
        print("Zalogowano do SMTP.")  # Debugowanie
        smtp.to(recipient_email)
        smtp.write(message)
        smtp.send()
        print("Zdjęcie wysłane na e-mail.")  # Debugowanie
        smtp.quit()
    except Exception as e:
        print("Błąd wysyłania e-maila:", e)  # Debugowanie

def button_pressed(pin):
    """Obsługa wciśnięcia przycisku"""
    global photo_taken, timer_active
    if not photo_taken and not timer_active:
        print("Przycisk wciśnięty, czekam 5 sekund...")
        timer_active = True  # Ustawienie flagi, aby zapobiec wielokrotnemu uruchomieniu
        camera_timer.init(period=DELAY_TIME, mode=Timer.ONE_SHOT, callback=on_timer)

def connect_wifi(ssid, password):
    """Łączy z siecią Wi-Fi"""
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    while not station.isconnected():
        pass
    print('Połączenie z Wi-Fi udane')
    print('Adres IP:', station.ifconfig()[0])

# Inicjalizacja
try:
    connect_wifi(ssid, password)
    init_camera()
    init_sd()  # Dodajemy inicjalizację karty SD
    check_sd_mount()  # Sprawdzamy, czy karta SD jest dostępna
except Exception as e:
    print("Błąd inicjalizacji:", e)

button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)

print("Gotowy do pracy. Naciśnij przycisk, aby wykonać zdjęcie i wysłać na e-mail.")

# Program działa w tle, obsługuje przerwania. Jeśli problem nadal występuje, spróbuj dodać więcej komunikatów debugujących w funkcji `send_email_with_photo`, aby zidentyfikować, w którym miejscu kod się zatrzymuje. Możesz również spróbować wysłać prosty e-mail bez załącznika, aby sprawdzić, czy problem leży w wysyłaniu załącznika. Oto jak możesz to zrobić:


def send_simple_email():
    """Wysyła prosty e-mail bez załącznika"""
    print("Próba wysłania prostego e-maila...")  # Debugowanie
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)  # Gmail's SSL port
        print("Połączono z serwerem SMTP...")  # Debugowanie
        smtp.login(sender_email, sender_app_password)
        print("Zalogowano do SMTP.")  # Debugowanie
        smtp.to(recipient_email)
        smtp.write("From:" + sender_name + "<" + sender_email + ">\n")
        smtp.write("Subject: Test e-mail\n")
        smtp.write("To: " + recipient_email + "\n")
        smtp.write("Wiadomość testowa wysłana z ESP32.\n")
        smtp.send()
        print("E-mail wysłany.")  # Debugowanie
        smtp.quit()
    except Exception as e:
        print("Błąd wysyłania e-maila:", e)  # Debugowanie
