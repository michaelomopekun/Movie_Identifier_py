import os
import time
import socket
import winsound
import datetime
import pandas as pd
from pathlib import Path
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from env_manager import envManager



parent_dir = Path(__file__).resolve().parent.parent

class DownloadMovieTrailers:

    def __init__(self, parent_dir=parent_dir):

        load_dotenv()
        
        self.parent_dir = parent_dir

        # self.initialize_process_movies = process_movies.ProcessMovies()

        self.batch = int(os.getenv("BATCH"))

        self.path_csv_trailer = os.getenv("TRAILER_CSV_PATH")

        self.END_INDEX = int(os.getenv("END_INDEX"))

        csv_path = parent_dir / "csv_files" / self.path_csv_trailer

        if not csv_path.exists():
            with open(csv_path, 'w', encoding="utf-8") as f:
                f.write("tconst,title,year,trailer_url\n")

        # Load CSV containing the movie trailers
        self.movies = pd.read_csv(csv_path,
                                  encoding='utf-8',
                                  index_col=0,
                                  on_bad_lines='skip')

        self.downloaded_trailers_summary = parent_dir / "csv_files" / "downloaded_trailers_summary.csv"

        # Create folder for trailers if not exists
        self.trailers_dir = parent_dir / "trailers"
        self.trailers_dir.mkdir(exist_ok=True)

        # yt-dlp options for 360p resolution
        self.ydl_opts = {
            'format': 'bestvideo[height<=360]',
            'outtmpl': str(self.trailers_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': r'C:\ffmpeg\ffmpeg-7-1-1',
        }


    def is_connected(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        
        except Exception as e:
            print(f"Socket error: {e}")
            return False
        

    def retry_on_no_internet_access(self, message = None, attempt = None):
        retry_count = 0
        while not self.is_connected():
            retry_count += 1
            attempt = f" will retry in 10s (attempts --{retry_count}--)========" if attempt is None else attempt
            print(message, attempt)
            winsound.Beep(1000, 500)
            time.sleep(10)
        return True


    # download trailer using yt-dlp
    def download_trailer_yt(self, tconst, trailer_url):

        try:

            filename = self.trailers_dir / f"{tconst}.mp4"

            if filename.exists():
                return str(filename)

            with YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(trailer_url, download=True)
                downloaded = Path(ydl.prepare_filename(info))

                if downloaded != filename:
                    if downloaded.exists():
                        downloaded.rename(filename)
                    else:
                        raise FileNotFoundError(f"Downloaded file not found: {downloaded}")
                    
            if not filename.exists():
                raise FileNotFoundError(f"Failed to download trailer to {filename}")
                    
            return str(filename)
        
        except Exception as e:
            raise Exception(f"Error downloading trailer for {tconst}: {str(e)}")



    def download_trailer(self):

        # Process specified range
        subset = self.movies.iloc[0:]

        summary_stats = {}
        results = []

        for index, row in subset.iterrows():

            tconst = row['tconst']
            url = row['trailer_url']

            if url == "Not found":
                continue

            try:

                print("⌚⌚⌚checking internet connection...")

                message = f"========❌❌❌No internet connection available at the moment while fetching trailer for TMDb ID {tconst},"
                self.retry_on_no_internet_access(message)

                print("✅Internet connection available, proceeding with download...")

                path = self.download_trailer_yt(tconst, url)

                if not path:
                    print(f"❌❌❌Failed to download trailer for {tconst} from {url}")
                    continue

                print(f"✅✅✅Successfully downloaded trailer for {tconst} from {url} to {path}")

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

        new_batch = self.batch + 1
        new_csv = f"movie_trailers_{new_batch}.csv"

        new_target = self.END_INDEX + 100

        envManager.update_env_variable("START_INDEX", self.END_INDEX)

        envManager.update_env_variable("END_INDEX", new_target)

        envManager.update_env_variable("TRAILER_CSV_PATH", new_csv)

        envManager.update_env_variable("BATCH", new_batch)


downloadTrailer = DownloadMovieTrailers()
