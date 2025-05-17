import os
import pandas as pd
from yt_dlp import YoutubeDL



# Load CSV containing the movie trailers
movies = pd.read_csv("movie_trailers_1.csv")


# Create folder for trailers if not exists
os.makedirs("trailers", exist_ok=True)


# yt-dlp options for 360p resolution
ydl_opts = {
    'format': 'bestvideo[height<=360]',
    'outtmpl': 'trailers/%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'ffmpeg_location': r'C:\ffmpeg\ffmpeg-7-1-1',
}


# download trailer using yt-dlp
def download_trailer(tconst, trailer_url):

    filename = f"trailers/{tconst}.mp4"

    if os.path.exists(filename):
        return filename
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(trailer_url, download=True)
        downloaded = ydl.prepare_filename(info)

        if downloaded != filename:
            os.rename(downloaded, filename)
    return filename



# Process specified range
subset = movies.iloc[41:42]

results = []

for index, row in subset.iterrows():

    tconst = row['tconst']
    url = row['trailer_url']

    if url == "Not found":
        continue

    try:
        path = download_trailer(tconst, url)
        results.append({f'[{index + 1}/{len(movies)}]': {'tconst': tconst, 'file_path': path}})

    except Exception as e:
        results.append({f'[{index + 1}/{len(movies)}]': {'tconst': tconst, 'error': f"Error downloading {tconst}: {e}"}})
        


# save download summary
pd.DataFrame(results).to_csv(
                              "downloaded_trailers_summary.csv",
                              mode='a', 
                              header=True, index=True)