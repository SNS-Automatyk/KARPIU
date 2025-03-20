import audiocore
import board
import audiobusio
import os
import sdcardio
import storage

sd = sdcardio.SDCard(board.SPI(), board.SDCS)
vfs = storage.VfsFat(sd)
storage.mount(vfs, '/sd')
os.listdir('/sd')

LOOP = True  # Update to True loop WAV playback. False plays once.

audio = audiobusio.I2SOut(board.A2, board.A1, board.A0)

with open("/sd/alarm_beep.wav", "rb") as wave_file:
    wav = audiocore.WaveFile(wave_file)

    print("Playing wav file!")
    audio.play(wav, loop=LOOP)
    while audio.playing:
        pass

print("Done!")