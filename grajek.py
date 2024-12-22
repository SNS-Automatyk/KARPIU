import os
from machine import I2S, Pin, SPI
import sdcard
import socket

#======= USER CONFIGURATION =======
WAV_FILE = 'alarm_beep.wav'
WAV_SAMPLE_SIZE_IN_BITS = 16
FORMAT = I2S.MONO
SAMPLE_RATE_IN_HZ = 16000
BUFFER_LENGTH_IN_BYTES = 40000

SD_CS_PIN = 21

SPI_MISO = 8
SPI_MOSI = 9
SPI_SCK = 7
#======= USER CONFIGURATION =======

SCK_PIN = Pin(3) 
WS_PIN = Pin(2)  
SD_PIN = Pin(1)
I2S_ID = 0

# channelformat settings:
#     mono WAV:  channelformat=I2S.ONLY_LEFT
audio_out = I2S(
    I2S_ID,
    sck=SCK_PIN,
    ws=WS_PIN,
    sd=SD_PIN,
    mode=I2S.TX,
    bits=WAV_SAMPLE_SIZE_IN_BITS,
    format=FORMAT,
    rate=SAMPLE_RATE_IN_HZ,
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

spi = SPI(2, baudrate=20000000, sck=Pin(SPI_SCK), mosi=Pin(SPI_MOSI), miso=Pin(SPI_MISO))
sd = sdcard.SDCard(spi, Pin(SD_CS_PIN))
os.mount(sd, "/sd")
wav_file = '/sd/{}'.format(WAV_FILE)
wav = open(wav_file,'rb')

# advance to first byte of Data section in WAV file
pos = wav.seek(44) 

# allocate sample arrays
#   memoryview used to reduce heap allocation in while loop
wav_samples = bytearray(10000)
wav_samples_mv = memoryview(wav_samples)

print('Starting')
# continuously read audio samples from the WAV file 
# and write them to an I2S DAC
try:
    while True:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            pos = wav.seek(44)
        else:
            pos = audio_out.write(wav_samples_mv[:num_read])
except (KeyboardInterrupt, Exception) as e:
    print("caught exception {} {}".format(type(e).__name__, e))

    
wav.close()
os.umount("/sd")
audio_out.deinit()
print('Done')
