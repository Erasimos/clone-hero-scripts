import os
import re
import time
import yt_dlp
from mutagen.oggopus import OggOpus
from moviepy import VideoFileClip

def get_song_info(song_dir: str):
    
    re_match = re.match(r"^(.*) - (.*) \(.+\)", song_dir)
    if re_match:
        artist = re_match.group(1).strip()
        song = re_match.group(2).strip()
        return artist, song
    print("Error: could not extract song name or artist")
    return None, None

# Maybe add check for multiple video formats
def video_exists(song_dir: str):
    for file in os.listdir(song_dir):
        if file.endswith(".mp4"):
            return True
    return False


def download_video(song: str, artist: str, dest: str):
    video_file = os.path.join(dest, song + '-' + artist + '.mp4')
    search_query = f"{artist} {song} music video"
    ydl_opts = {
        'outtmpl': video_file,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{search_query}", download=False)
        
        video_url = result.get('entries', [{}])[0].get('url')
        if video_url:
            ydl.download([video_url])
            print(f"Video downloaded for: {song} by {artist}")
        else:
            print(f"No video found for: {song} by {artist}")

    return video_file

def mute_and_trim_video(video_file, opus_file, song_folder):

    # Mute
    video = VideoFileClip(video_file)
    video = video.without_audio()

    # Trim
    audio = OggOpus(opus_file)
    audio_length = audio.info.length
    if audio_length > video.duration:
        video = video.subclipped(0, audio_length)

    video.write_videofile(os.path.join(song_folder, 'video.mp4'))
    video.close()

def add_music_videos(dir: str):
    
    # Create tmp folder for downloaded music videos
    script_dir = os.path.dirname(os.path.realpath(__file__))
    tmp_dir = os.path.join(script_dir, 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    for song_folder in os.listdir(dir):
        song_folder_path = os.path.join(dir, song_folder)

        if os.path.isdir(song_folder_path):

            song, artist = get_song_info(song_folder)

            if song and artist:
                opus_file = None
                for file in os.listdir(song_folder_path):
                    if file == 'song.opus':
                        opus_file = os.path.join(song_folder_path, file)
                        break
                
                if opus_file:
                    if video_exists(song_folder_path):
                        print(f"Video already exist for: {song} by {artist}")
                        continue
                    else:

                        video_file = download_video(song, artist, tmp_dir)
                        if video_file:
                            mute_and_trim_video(video_file, opus_file, song_folder_path)
                        else:
                            print(f"Failed to download video for: {song} by {artist}")
                        
            else:
                print(f"Skipping folder: {song_folder}")
        else:
            print(f"Skipping non-directory: {song_folder_path }")


if __name__ == "__main__":
    #clone_hero_dir = os.path.dirname(os.path.realpath(__file__))
    clone_hero_dir = 'C:/Users/rasmu/Downloads/clone_hero'
    add_music_videos(clone_hero_dir)