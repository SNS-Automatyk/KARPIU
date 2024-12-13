from machine import Pin, SPI, Timer
import urequests
import camera
import os
import time
import sdcard
import socket

# Konfiguracja GPIO i SD
BUTTON_PIN = 0  # Przycisk na GPIO0
LED_PIN = 10    # Wbudowana dioda LED
SD_CS_PIN = 4   # CS karty SD
SERVER_URL = "http://example.com/upload"  
DELAY_TIME = 5000  


button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)
camera_timer = Timer(-1)
photo_taken = False


SPI_MISO = 13
SPI_MOSI = 11
SPI_CLK = 12

spi = SPI(2, baudrate=20000000, sck=Pin(SPI_CLK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))
os.mount(sd, "/sd")

def init_camera():
    """Inicjalizacja kamery OV2640"""
    try:
        camera.init(0, format=camera.JPEG)
        camera.framesize(camera.FRAME_VGA)  
        camera.quality(10)  
        print("Kamera zainicjowana.")
    except Exception as e:
        print("Błąd inicjalizacji kamery:", e)

def take_photo():
    """Wykonuje zdjęcie"""
    led.on()
    photo = camera.capture()
    led.off()
    return photo

def save_photo_to_sd(photo, filename):
    """Zapisuje zdjęcie na kartę SD"""
    try:
        filepath = f"/sd/{filename}"
        with open(filepath, "wb") as file:
            file.write(photo)
        print(f"Zdjęcie zapisane na SD jako: {filepath}")
        return filepath
    except Exception as e:
        print("Błąd zapisu na SD:", e)
        return None

def send_photo(photo):
    """Wysyła zdjęcie na serwer"""
    headers = {'Content-Type': 'image/jpeg'}
    try:
        response = urequests.post(SERVER_URL, data=photo, headers=headers)
        print("Odpowiedź serwera:", response.text)
        response.close()
    except Exception as e:
        print("Błąd wysyłania zdjęcia:", e)

def on_timer(timer):
    """Uruchamiane po 5 sekundach od naciśnięcia przycisku"""
    global photo_taken
    if not photo_taken:
        print("Czas minął, wykonuję zdjęcie...")
        photo = take_photo()
        filename = f"photo_{int(time.time())}.jpg"
        filepath = save_photo_to_sd(photo, filename)
        photo_taken = True

def button_pressed(pin):
    """Obsługa wciśnięcia przycisku"""
    global photo_taken
    if not photo_taken:
        print("Przycisk wciśnięty, czekam 5 sekund...")
        camera_timer.init(period=DELAY_TIME, mode=Timer.ONE_SHOT, callback=on_timer)

def start_http_server():
    """Uruchamia serwer HTTP do przeglądania zdjęć"""
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("Serwer HTTP uruchomiony na 0.0.0.0:80")
    
    while True:
        client, addr = s.accept()
        print(f"Połączenie od: {addr}")
        request = client.recv(1024).decode('utf-8')
        if "GET /" in request:
            
            files = os.listdir("/sd")
            response = "<html><body><h1>Zapisane Zdjęcia</h1><ul>"
            for file in files:
                if file.endswith(".jpg"):
                    response += f'<li><a href="/sd/{file}">{file}</a></li>'
            response += "</ul></body></html>"
            client.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            client.send(response)
        elif "GET /sd/" in request:
            
            filepath = request.split("GET ")[1].split(" HTTP/1.1")[0]
            filepath = filepath.strip("/")
            try:
                with open(filepath, "rb") as file:
                    photo = file.read()
                client.send("HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n")
                client.send(photo)
            except Exception as e:
                client.send("HTTP/1.1 404 Not Found\r\n\r\n")
        client.close()

# Inicjalizacja
try:
    init_camera()
    print("Karta SD zainicjowana. Pliki na SD:", os.listdir("/sd"))
except Exception as e:
    print("Błąd inicjalizacji:", e)

button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)

print("Gotowy do pracy. Uruchamiam serwer HTTP...")
start_http_server()
