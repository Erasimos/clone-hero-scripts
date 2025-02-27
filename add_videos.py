import os
import re
import subprocess

QUALITY = "medium" # Set to low, medium, high, to ajdust music video quality

def get_quality_settings():
    """Returns encoding settings based on global QUALITY variable."""
    quality_presets = {
        "low": {
            "crf": "30", "bitrate": "1.5M", "preset": "faster",
        },
        "medium": {
            "crf": "26", "bitrate": "3M", "preset": "veryfast",
        },
        "high": {
            "crf": "22", "bitrate": "5M", "preset": "slow",
        },
    }
    return quality_presets.get(QUALITY, quality_presets["medium"])

def clear_dir(dir: str):
    for file in os.listdir(dir):
        os.remove(os.path.join(dir, file))


def is_av1_encoded(video_file):
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-of", "csv=p=0",
        video_file
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    codec = result.stdout.strip()

    print("CODEC: ", codec)

    return codec == "av1"

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

def convert_av1_to_h264(video_file: str):

    settings = get_quality_settings()

    converted_video_file = video_file.replace('.mp4', "_h264.mp4")

    command = [
        "ffmpeg",
        "-i", video_file,
        "-c:v", "libx264",
        "-preset", settings["preset"],
        "-crf", settings["crf"],
        "-c:a", "aac",
        "-b:a", "128k",
        "-b:v", settings["bitrate"],
        "-strict", "experimental",
        converted_video_file
    ]
    subprocess.run(command)
    print(f"Conversion to H.264 completed: {video_file}")
    return converted_video_file

def download_video(song: str, artist:str, dest:str):

    search_query = f"{artist} {song}"
    video_file = f"{os.path.join(dest, search_query)}.mp4"

    command = [
        "yt-dlp",
        f"ytsearch:{search_query} music video",
        "--no-playlist",
        "-f" "bestaudio[ext=m4a]+bestvideo[ext=mp4]/mp4"
        "--quiet",
        "--output", video_file
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Video downloaded successfully to {video_file}")

        if is_av1_encoded(video_file):
            print("AV1 detected, converting to H.264...")
            video_file = convert_av1_to_h264(video_file)
        return video_file
    else:
        print("Error during download: ", result.stderr)
        return None


def get_audio_duration(opus_file):
    command = [
        "ffprobe",
        "-i", opus_file,
        "-show_entries", "format=duration",
        "-v", "quiet",
        "-of", "csv=p=0"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    duration = float(result.stdout.strip())
    return duration

def mute_and_trim_video(video_file, opus_file, song_folder):

    audio_length = get_audio_duration(opus_file)
    output_file = os.path.join(song_folder, 'video.mp4')

    command = [
        "ffmpeg",                       # Call ffmpeg
        "-ss", "0",                     # Start time (0 means starting from the beginning)
        "-i", video_file,               # Input video file
        "-t", str(audio_length),        # Duration of the video (trim based on audio length)
        "-an",                          # Remove audio (mute the video)
        "-c:v", "copy",              # Use the H.264 codec for the video
        "-preset", "ultrafast",              # Fast encoding preset (balance between speed and quality)
        "-crf", "28",                   # Constant Rate Factor (quality, lower is better, 23 is default)
        "-r", "30",                     # Set the frame rate to 30fps (optional, based on your needs)
        output_file                     # Output file
    ]

    subprocess.run(command)

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

    clear_dir(tmp_dir)


if __name__ == "__main__":
    clone_hero_songs_dir = 'C:/Users/rasmu/Documents/ch_songs'
    add_music_videos(clone_hero_songs_dir)