import winsound
import time

def play_alert():
    # Windows'ta sistem sesi çal
    winsound.Beep(1000, 500)  # 1000 Hz, 500 ms
    time.sleep(0.1)
    winsound.Beep(1000, 500)  # İkinci bip sesi 