import os
from machine import I2S, Pin, SPI
import sdcard
import ustruct

# ===== CONFIG =====
WAV_FILE = 'alarm2.wav'
WAV_BITS = 16       # PCM 16-bit
WAV_FORMAT = I2S.STEREO
SAMPLE_RATE = 16000
BUFFER_LEN = 4096

# SD card SPI
SD_CS_PIN = 21
SPI_MISO = 8
SPI_MOSI = 9
SPI_SCK  = 7

# I2S pins
I2S_ID = 0
BCLK = Pin(3)   # BCK
LRCLK = Pin(2)  # LRCK
DATA = Pin(1)   # DIN

# ===== INIT I2S =====
audio_out = I2S(
    I2S_ID,
    sck=BCLK,
    ws=LRCLK,
    sd=DATA,
    mode=I2S.TX,
    bits=WAV_BITS,
    format=WAV_FORMAT,
    rate=SAMPLE_RATE,
    ibuf=BUFFER_LEN
)

# ===== INIT SD =====
spi = SPI(2, baudrate=20000000, sck=Pin(SPI_SCK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))
os.mount(sd, "/sd")
print("✓ SD mounted")

# ===== OPEN WAV =====
wav_file = "/sd/" + WAV_FILE
print('zmontowano')
wav = open(wav_file, "rb")
wav.seek(44)  # skip header

# ===== PLAY =====
buf = bytearray(1024)
mv = memoryview(buf)

print("Starting playback...")

try:
    while True:
        n = wav.readinto(mv)
        if n == 0:
            wav.seek(44)  # loop
        else:
            audio_out.write(mv[:n])
        if Pin(6, Pin.IN, Pin.PULL_UP).value() == 0:
            print('wcisniety')
            break

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    wav.close()
    os.umount("/sd")
    audio_out.deinit()
    print("Done")
