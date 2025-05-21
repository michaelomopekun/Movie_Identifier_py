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

        summary = {}
        results = []

        for index, row in subset.iterrows():

            tconst = row['tconst']
            url = row['trailer_url']

            if url == "Not found":
                continue

            try:
                path = self.download_trailer_yt(tconst, url)

                results.append({
                    'index': f'[{index + 1}/{len(self.movies)}]',
                    'tconst': tconst,
                    'file_path': path,
                    'status': 'success'
                })

                time.sleep(0.5)

            except Exception as e:
                results.append({
                    'index': f'[{index + 1}/{len(self.movies)}]',
                    'tconst': tconst,
                    'file_path': '',
                    'status': f'error: {str(e)}'
                })

        successful_downloads = len([r for r in results if r['status'] == 'success'])
        summary_stats = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'total_processed': len(subset),
            'total_downloaded': successful_downloads,
            'total_failed': len(subset) - successful_downloads
        }

        results_df = pd.DataFrame(results)
        summary_df  = pd.DataFrame([summary_stats])

        # save download summary
        results_df.to_csv(
            self.downloaded_trailers_summary,
            mode='a',
            header=True, index=True
        )

        # save summary stats
        summary_df.to_csv(
            self.downloaded_trailers_summary,
            mode='a',
            header=True, index=True
        )
