import pygame
import keyboard

#define variables

music_playlist = []
folder_directory = "C:/Users/logan/OneDrive/Pictures/Documents/aaronsgame/"
#read songs file to get all the paths of the songs


#file_path = "C:/Users/logan/OneDrive/Pictures/Documents/aaronsgame/songs"

#open file and read all the lines into a list
f = open("/Users/logan/OneDrive/Pictures/Documents/aaronsgame/songs.txt", "r")
for line in f:
    music_playlist.append(line.strip())
f.close()

# Initialize the mixer
for i in range(len(music_playlist)):
    music_playlist[i] = music_playlist[i].replace("\\", "/")
    path = music_playlist[i]
    print(path)
    pygame.mixer.init()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

    # Keep the script running to allow the music to play
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

        if keyboard.is_pressed('q'):
            pygame.mixer.music.stop()
            exit()

    