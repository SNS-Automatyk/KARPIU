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
import ustruct
from machine import SPI, Pin, Timer, I2S

# ----- Configuration: Network & Email -----
ssid = "Automatyk"
password = "automatyk5n5"

sender_email = 'karpiunator@gmail.com'
sender_name = 'ESP32'
sender_app_password = 'iwpemdqmrccpaknw'
recipient_email = '277768@student.pwr.edu.pl'
email_subject = 'Karpiu test'

# ----- Configuration: Hardware -----
DELAY_TIME = 5000  # Czas opóźnienia w ms przed zdjęciem
BUTTON_PIN = 6     # Przycisk na GPIO6
led_num = 16
pinout = 5
PIN_RELAY = Pin(44, Pin.OUT)

# ----- Configuration: Audio (I2S) -----
WAV_FILE = 'alarm2_short.wav'
WAV_BITS = 16
WAV_FORMAT = I2S.MONO
SAMPLE_RATE = 32000
BUFFER_LEN = 10000

# I2S Pins
I2S_ID = 0
I2S_BCLK = Pin(4)
I2S_LRCLK = Pin(3)
I2S_DATA = Pin(2)

# ----- Objects Initialization -----
ring = neopixel.NeoPixel(machine.Pin(pinout), led_num)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
ring_timer = Timer(-1)
startup_timer = Timer(0)
reset_timer = Timer(1) # Nowy timer do asynchronicznego resetu na końcu

# ----- Global Variables -----
ring_move = True
n = 0
startup_switch = True
DEBOUNCE_MS = 200
last_press = 0

# Flaga startowa
start_sequence_flag = False

# ----- SD Card Configuration -----
SD_CS_PIN = 21
SPI_MISO = 8
SPI_MOSI = 9
SPI_CLK = 7

spi = SPI(2, baudrate=20000000, sck=Pin(SPI_CLK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))

try:
    uos.mount(sd, "/sd")
except Exception:
    pass

# ----- I2S Initialization -----
try:
    audio_out = I2S(
        I2S_ID,
        sck=I2S_BCLK,
        ws=I2S_LRCLK,
        sd=I2S_DATA,
        mode=I2S.TX,
        bits=WAV_BITS,
        format=WAV_FORMAT,
        rate=SAMPLE_RATE,
        ibuf=BUFFER_LEN
    )
except Exception:
    pass

# ----- Helper Functions: Hardware -----
def clear_ring():
    global led_num
    for i in range(led_num):
        ring[i] = (0, 0, 0)
    ring.write()
    
def ring_flash():
    global ring_move
    ring_move = False
    try:
        ring_timer.deinit()
    except:
        pass
    for i in range(led_num):
        ring[i] = (128, 128, 128)
    ring.write()
    
def ring_startup(t): 
    global led_num, startup_switch
    if startup_switch:
        for i in range(led_num):
            if i % 2 == 0:
                ring[i] = (0, 0, 128)
            else:
                ring[i] = (0, 0, 0)
    else:
        for i in range(led_num):
            if i % 2 == 0:
                ring[i] = (0, 0, 0)
            else:
                ring[i] = (128, 0, 0)
    startup_switch = not startup_switch  
    ring.write()
    
def ring_error():
    for i in range(led_num):
        ring[i] = (128, 0, 0)
    ring.write()

def ring_succes():
    for i in range(led_num):
        ring[i] = (0, 128, 0)
    ring.write()

def move_one(t):
    global n
    if ring_move:
        n += 1
        if n == 16: n = 0
        for j in range(10):
            m = n + j
            if m > 15: m = m - 16
            ring[m] = (0, 0, j * 28)
        ring.write()
        
def relay_on():
    PIN_RELAY.on()
    
def relay_off():
    PIN_RELAY.off()

# ----- Audio Function -----
def play_wav_once():
    wav_path = "/sd/" + WAV_FILE
    
    wav = None
    try:
        wav = open(wav_path, "rb")
        wav.seek(44)
        
        buf = bytearray(2048)
        mv = memoryview(buf)
        
        while True:
            num_read = wav.readinto(mv)
            if num_read == 0:
                break
            
            total_written = 0
            while total_written < num_read:
                bytes_written = audio_out.write(mv[total_written:num_read])
                if bytes_written > 0:
                    total_written += bytes_written
                    
    except OSError:
        pass
    except Exception:
        pass
    finally:
        if wav:
            wav.close()
        silence = bytearray(1024)
        audio_out.write(silence)

# ----- Camera & Net Functions -----
def connect_wifi(ssid, password):
    station = network.WLAN(network.STA_IF)
    
    try:
        station.active(False)
        time.sleep(0.5)
        station.active(True)
    except OSError:
        machine.reset()
    
    if not station.isconnected():
        station.connect(ssid, password)
        start_time = time.time()
        while not station.isconnected():
            time.sleep(1)
            if time.time() - start_time > 15:
                break

def init_camera():
    try:
        camera.init()
        camera.framesize(9)  # VGA
        camera.quality(10)
    except Exception:
        pass

def take_photo():
    ring_flash()
    try:
        photo = camera.capture()
        if photo is None:
            return None
        return photo
    except Exception:
        return None

def save_photo_to_sd(photo, filename):
    if not isinstance(photo, (bytes, bytearray)):
        return None
    try:
        filepath = f"/sd/{filename}"
        with open(filepath, "wb") as file:
            file.write(photo)
        return filepath
    except Exception:
        return None

def send_file_from_sd_stream(filepath):
    try:
        smtp = umail.SMTP("smtp.gmail.com", 465, ssl=True)
        smtp.login(sender_email, sender_app_password)
        smtp.to(recipient_email)

        boundary = "BOUNDARY"
        filename = filepath.split("/")[-1]

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

        chunk_size = 768
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
        ring_succes()

    except Exception:
        ring_error()

# Funkcja wywoływana przez Timer w tle, żeby zresetować układ
def perform_reset(t):
    try:
        uos.umount("/sd")
    except:
        pass
    machine.reset()

def perform_capture_sequence():
    try:
        photo = take_photo()
        if photo:
            filename = f"photo_{int(time.time())}.jpg"
            filepath = save_photo_to_sd(photo, filename)
            if filepath:
                send_file_from_sd_stream(filepath)
            else:
                ring_error()
        else:
            ring_error()
            
    except Exception:
        ring_error()
        
    finally:
        relay_off()
        # --- ZMIANA: Zamiast time.sleep(5) uruchamiamy Timer na 5 sekund ---
        # ONE_SHOT oznacza, że wywoła się tylko raz i nie zablokuje procesora
        reset_timer.init(mode=Timer.ONE_SHOT, period=5000, callback=perform_reset)

def button_pressed(pin):
    global start_sequence_flag, last_press
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press) > DEBOUNCE_MS:
        relay_on() 
        start_sequence_flag = True
        last_press = current_time

# ----- Main Loop -----
def main():
    global start_sequence_flag, ring_move
    
    time.sleep(1)
    connect_wifi(ssid, password)
    init_camera()
    clear_ring()
    relay_off()
    startup_timer.init(period=500, mode=Timer.PERIODIC, callback=ring_startup)
    
    button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)
    
    # Zmienne do nieblokującego odliczania czasu do zdjęcia
    wait_for_capture = False
    capture_time = 0
    
    while True:
        # 1. Sprawdzanie, czy przycisk został naciśnięty
        if start_sequence_flag:
            start_sequence_flag = False
            
            # Ustawiamy punkt w czasie, kiedy ma się zrobić zdjęcie (np. teraz + 5000ms)
            capture_time = time.ticks_add(time.ticks_ms(), DELAY_TIME)
            wait_for_capture = True
            
            startup_timer.deinit()
            clear_ring()
            ring_move = True
            ring_timer.init(period=100, mode=Timer.PERIODIC, callback=move_one)
            
            # Odtwarzanie dźwięku
            play_wav_once()
            
        # 2. Nieblokujące sprawdzanie, czy nadszedł czas na zdjęcie
        # Pętla wykonuje się non-stop, więc układ w każdej chwili może zareagować na inne zdarzenia
        if wait_for_capture and time.ticks_diff(time.ticks_ms(), capture_time) >= 0:
            wait_for_capture = False
            perform_capture_sequence()

        time.sleep_ms(10) # Małe uśpienie tylko dla zachowania stabilności Watchdoga (WDT)

if __name__ == "__main__":
    main()