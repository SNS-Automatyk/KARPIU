import machine
import network
import time
import uos
import os
import camera
import sdcard
import umail
import base64
import neopixel
from machine import SPI, Pin, Timer

# ----- Configuration -----
ssid = "Automatyk"
password = "automatyk5n5"

sender_email = 'karpiunator@gmail.com'
sender_name = 'ESP32'
sender_app_password = 'iwpemdqmrccpaknw'
recipient_email = '277768@student.pwr.edu.pl'
email_subject = 'Karpiu test'

DELAY_TIME = 5000
BUTTON_PIN = 0  # Przycisk na GPIO0
led_num = 16
pinout = 5
ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

camera_timer = Timer(-1)
photo_taken = False  # Flaga wskazująca, czy zdjęcie zostało już wykonane
timer_active = False  # Flaga, aby zapobiec wielokrotnemu uruchamianiu tim era
ring_timer = Timer(0)
n = 0 


# SD card SPI configuration
SD_CS_PIN = 21
SPI_MISO = 8
SPI_MOSI = 9
SPI_CLK = 7

spi = SPI(2, baudrate=20000000, sck=Pin(SPI_CLK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))

try:
    uos.mount(sd, "/sd")
    print("SD card mounted at /sd")
except Exception as e:
    print("Error mounting SD card:", e)


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
    print("Timer uruchomiony.")  # Debugowanie do usunięcia jak już będziemy mieli finalną wersję :)
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

def connect_wifi(ssid, password):
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, password)
    print("Connecting to Wi-Fi...")
    while not station.isconnected():
        time.sleep(1)
    print("Connected to Wi-Fi.")
    print("IP address:", station.ifconfig()[0])



def init_camera():
    try:
        camera.init()
        camera.framesize(9)  # VGA
        camera.quality(10)
        print("Camera initialized.")
    except Exception as e:
        print("Camera initialization error:", e)

def take_photo():
    print("Trying to take photo...")
    try:
        photo = camera.capture()
        if photo is None:
            print("Error: photo is None")
            return None
        print("Photo taken successfully.")
        return photo
    except Exception as e:
        print("Photo capture error:", e)
        return None

def save_photo_to_sd(photo, filename):
    if not isinstance(photo, (bytes, bytearray)):
        print("Error: photo not in byte format.")
        return None
    try:
        filepath = f"/sd/{filename}"
        with open(filepath, "wb") as file:
            file.write(photo)
        print(f"Photo saved: {filepath}")
        return filepath
    except Exception as e:
        print("Error saving to SD:", e)
        return None

def send_file_from_sd_stream(filepath):
    print("Attempting to send file:", filepath)
    try:
        smtp = umail.SMTP("smtp.gmail.com", 465, ssl=True)
        smtp.login(sender_email, sender_app_password)
        smtp.to(recipient_email)

        boundary = "BOUNDARY"
        filename = filepath.split("/")[-1]

        # Nagłówki wiadomości MIME
        header = f"""From: {sender_name} <{sender_email}>
To: {recipient_email}
Subject: {email_subject}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{boundary}"

--{boundary}
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

Załącznik z ESP32.

--{boundary}
Content-Type: image/jpeg; name="{filename}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{filename}"

"""
        footer = f"--{boundary}--"

        smtp.write(header)

        chunk_size = 1020  # musi być wielokrotnością 3 dla base64
        with open(filepath, "rb") as photo_file:
            while True:
                chunk = photo_file.read(chunk_size)
                if not chunk:
                    break
                encoded_chunk = base64.b64encode(chunk).decode()
                smtp.write(encoded_chunk)
                smtp.write("\r\n")

        smtp.write("\r\n" + footer)
        smtp.send()
        smtp.quit()
        print("Email sent successfully.")

    except Exception as e:
        print("Email sending error:", e)

def button_pressed(pin):
# nie działa to XD
    global photo_taken, timer_active
    if not photo_taken and not timer_active:
        print("Przycisk wciśnięty, czekam 5 sekund...")
        timer_active = True  # Ustawienie flagi, aby zapobiec wielokrotnemu uruchomieniu
        camera_timer.init(period=DELAY_TIME, mode=Timer.ONE_SHOT, callback=on_timer)




def main():
    connect_wifi(ssid, password)
    init_camera()
    photo = take_photo()
    
    button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)
    if photo:
        filename = f"photo_{time.ticks_ms()}.jpg"
        filepath = save_photo_to_sd(photo, filename)
        if filepath:
            send_file_from_sd_stream(filepath)
        else:
            print("Failed to save photo to SD.")
    else:
        print("Photo capture failed. Email not sent.")

main()

