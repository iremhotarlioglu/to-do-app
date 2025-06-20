import pygame
def play_alert():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load('ses_dosyaniz.wav')  # veya .mp3
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue  # Ses bitene kadar bekle
    except Exception as e:
        # Hata durumunda (örn. dosya bulunamazsa) ne yapılacağını belirleyin
        print(f"Ses çalınamadı: {e}") 
