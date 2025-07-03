import time
import os
import requests
import winsound
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from env_manager import envManager
from downLoad_Trailer import downloadTrailer

# Load environment variables

class ProcessMovies:

    def __init__(self):
        
        load_dotenv()
        self.Path_trailer_csv = os.getenv("TRAILER_CSV_PATH")

        self.batch = int(os.getenv("BATCH"))

        #file paths
        parent_dir = Path(__file__).resolve().parent.parent


        self.path = parent_dir / "logs" / "process_log.txt"

        self.skipped_path = parent_dir / "logs" / "skipped_movies.txt"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

        self.path_movie_trailers_4 = parent_dir / "csv_files" / self.Path_trailer_csv
        if not self.path_movie_trailers_4.exists():
            self.path_movie_trailers_4.touch()

        self.path_movie_trailers_4.parent.mkdir(parents=True, exist_ok=True)
        if not self.path_movie_trailers_4.exists():
            self.path_movie_trailers_4.touch()

        self.path_env_file = parent_dir / ".env"


        # Load movies data
        try:
            self.movies = pd.read_csv(parent_dir / "csv_files" / "filtered_movies_2015_plus_6.0_sorted.csv")
        except FileNotFoundError:
            raise FileNotFoundError("The filtered_movies CSV file was not found.")


        # TMDb API setup
        self.API_KEY = os.getenv("TMDB_API_KEY")
        if not self.API_KEY:
            raise ValueError("TMDB_API_KEY is not set in the environment variables.")

        self.TMDB_SEARCH_URL = "https://api.themoviedb.org/3/find/{tconst}"
        self.TMDB_VIDEO_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}/videos"

        # index range
        self.START_INDEX = int(os.getenv("START_INDEX"))
        self.END_INDEX = int(os.getenv("END_INDEX"))



    # Get movie details using IMDb ID
    def get_tmdb_movie_by_imdb_id(self, tconst):

        message = f"========❌❌❌ No internet connection available at the moment while fetching for tconst {tconst},"
        downloadTrailer.retry_on_no_internet_access(message)
        print("✅✅✅Internet connection available, proceeding...")

        url = self.TMDB_SEARCH_URL.format(tconst=tconst)

        params = {
            "api_key": self.API_KEY,
            "external_source": "imdb_id"
        }

        try:
            response = requests.get(url, params=params)

            response.raise_for_status()

            results = response.json().get("movie_results", [])
            
            return results[0] if results else None
        
        except Exception as e:

            print(f"Error fetching TMDb movie for {tconst}: {e}")

            return None



    def get_trailer_url(self, tmdb_id):

        message = f"========❌❌❌ No internet connection available while fetching TMDb ID {tmdb_id}"
        downloadTrailer.retry_on_no_internet_access(message)
        print("✅✅✅ Internet connection available, proceeding...")

        url = self.TMDB_VIDEO_URL.format(tmdb_id=tmdb_id)
        params = {"api_key": self.API_KEY}

        try:
            response = requests.get(url, params=params)

            # to handle rate limiting
            MAX_RETRY_WAIT = 60

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))

                if retry_after > MAX_RETRY_WAIT:
                    print(f"⛔ Retry-After too long ({retry_after}s). Skipping TMDb ID {tmdb_id}")
                    winsound.PlaySound(f"Skipping TMDB ID {tmdb_id}, because Api Rate Limit has been hit and Retry-After is {retry_after}s which is too long", winsound.SND_ALIAS)

                    #log in a file
                    with open(self.skipped_path, "a") as log_file:
                        log_file.write(f"{tmdb_id}, because Retry-After is {retry_after}s which is too long\n")
                    return False

                print(f"⏳ TMDb rate limit hit for ID {tmdb_id}. Retrying after {retry_after}s")
                winsound.PlaySound(f"Api's Rate Limit has been hit. Retrying TMDB ID {tmdb_id} after {retry_after}s", winsound.SND_ALIAS)
                time.sleep(retry_after)
                return self.get_trailer_url(tmdb_id)

            for video in response.json().get("results", []):
                if video["type"] == "Trailer" and video["site"] == "YouTube":
                    return f"https://www.youtube.com/watch?v={video['key']}"

        except Exception as e:
            print(f"❌ Error fetching trailer for TMDb ID {tmdb_id}: {e}")

        return None



    def process_movies(self, target_num_of_trailers=100, header=True):

        # store fetched trailers
        results = []

        subset = self.movies.iloc[self.START_INDEX:self.END_INDEX]

        # Process and fetch trailer for each movie
        for index, row in subset.iterrows():

            title = row["primaryTitle"]
            year = row["startYear"]
            tconst = row["tconst"]


            if year == "\\N" or not str(year).isdigit():

                with open(self.path, "a") as log_file:
                    log_file.write(f"{tconst}, {title}, {year}, Skipped (invalid year)\n")
                continue


            # fetches movie details and logs to file if not found
            movie = self.get_tmdb_movie_by_imdb_id(tconst)
            if not movie:

                print(f"[{index + 1}/{len(self.movies)}] {title} ({year}): Movie not found")

                with open(self.path, "a") as log_file:
                    log_file.write(f"[{index + 1}/{len(self.movies)}] {tconst}, {title}, {year}, Movie not found\n")
                continue


            # uses movieId in movie details to fetch trailer and logs to file if not found
            trailer_url = self.get_trailer_url(movie["id"])
            if not trailer_url:

                print(f"[{index + 1}/{len(self.movies)}] {title} ({year}): Trailer not found")

                if trailer_url != False:
                    with open(self.path, "a") as log_file:
                        log_file.write(f"[{index + 1}/{len(self.movies)}] {tconst}, {title}, {year}, Trailer not found\n")
                    continue

            print(f"[{index + 1}/{len(self.movies)}] {title} ({year}): {trailer_url}")

            with open(self.path, "a") as log_file:
                log_file.write(f"[{index + 1}/{len(self.movies)}] {tconst}, {title}, {year}, {trailer_url}\n")

            # Append found trailer to the results list
            results.append({
                "tconst": tconst,
                "title": title,
                "year": year,
                "trailer_url": trailer_url
            })

            # Sleep to avoid throttling
            time.sleep(0.5)


        # Save to CSV
        output_df = pd.DataFrame(results)
        output_df.to_csv(self.path_movie_trailers_4, mode='a', header=header, index=True)


        number_of_trailers = pd.read_csv(self.path_movie_trailers_4).shape[0]

        if number_of_trailers <= target_num_of_trailers:
            remain_to_100 = target_num_of_trailers - number_of_trailers

            envManager.update_env_variable("START_INDEX", self.END_INDEX)
            envManager.update_env_variable("END_INDEX", self.END_INDEX + remain_to_100)

            self.__init__()

            self.process_movies(remain_to_100, header=False)



# processMovies = ProcessMovies()


