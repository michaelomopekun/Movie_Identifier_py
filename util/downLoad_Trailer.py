import os
import time
import pandas as pd
import datetime
from pathlib import Path
from yt_dlp import YoutubeDL



parent_dir = Path(__file__).resolve().parent.parent

class DownloadMovieTrailers:

    def __init__(self, parent_dir=parent_dir):
        
        self.parent_dir = parent_dir

        self.path_csv_trailer = os.getenv("TRAILER_CSV_PATH")

        # Load CSV containing the movie trailers
        self.movies = pd.read_csv(parent_dir / "csv_files" / self.path_csv_trailer)

        self.downloaded_trailers_summary = parent_dir / "csv_files" / "downloaded_trailers_summary.csv"

        # Create folder for trailers if not exists
        os.makedirs("trailers", exist_ok=True)


        # yt-dlp options for 360p resolution
        self.ydl_opts = {
            'format': 'bestvideo[height<=360]',
            'outtmpl': 'trailers/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': r'C:\ffmpeg\ffmpeg-7-1-1',
        }



    # download trailer using yt-dlp
    def download_trailer_yt(self, tconst, trailer_url):

        filename = f"trailers/{tconst}.mp4"

        if os.path.exists(filename):
            return filename

        with YoutubeDL(self.ydl_opts) as ydl:
            info = ydl.extract_info(trailer_url, download=True)

            downloaded = ydl.prepare_filename(info)

            if downloaded != filename:
                os.rename(downloaded, filename)
        return filename



    def download_trailer(self):

        # Process specified range
        subset = self.movies.iloc[0:]

        results = []

        for index, row in subset.iterrows():

            tconst = row['tconst']
            url = row['trailer_url']

            if url == "Not found":
                continue

            try:
                path = self.download_trailer_yt(tconst, url)
                results.append({f'[{index + 1}/{len(self.movies)}]': {'tconst': tconst, 'file_path': path}})

                time.sleep(0.5)

            except Exception as e:
                results.append({f'[{index + 1}/{len(self.movies)}]': {'tconst': tconst, 'error': f"Error downloading {tconst}: {e}"}})

        results.append(f"{'='*25} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} {'='*25}")
        results.append(f"Downloaded {len(results)} trailers successfully.")
        results.append(f"Total trailers processed: {len(subset)}")
        results.append(f"Total trailers downloaded: {len(results)}")
        results.append(f"Total trailers failed: {len(subset) - len(results)}")
        results.append(f"{'='*25} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} {'='*25}")


        # save download summary
        pd.DataFrame(results).to_csv(
                                    self.downloaded_trailers_summary,
                                    mode='a', 
                                    header=True, index=True)