import pandas as pd
import requests
import time
import os

# Load movies data
movies = pd.read_csv("filtered_movies_2015_plus_6.0_sorted.csv")



# TMDb API setup
API_KEY = os.getenv("TMDB_API_KEY")
if not API_KEY:
    raise ValueError("TMDB_API_KEY is not set in the environment variables.")



TMDB_SEARCH_URL = "https://api.themoviedb.org/3/find/{tconst}"
TMDB_VIDEO_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}/videos"



# Get movie details using IMDb ID
def get_tmdb_movie_by_imdb_id(tconst):

    url = TMDB_SEARCH_URL.format(tconst=tconst)

    params = {
        "api_key": API_KEY,
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



# Get YouTube trailer link
def get_trailer_url(tmdb_id):

    url = TMDB_VIDEO_URL.format(tmdb_id=tmdb_id)

    params = {"api_key": API_KEY}

    try:

        response = requests.get(url, params=params)
        response.raise_for_status()
        for video in response.json().get("results", []):
            if video["type"] == "Trailer" and video["site"] == "YouTube":

                return f"https://www.youtube.com/watch?v={video['key']}"
            
    except Exception as e:

        print(f"Error fetching trailer for TMDb ID {tmdb_id}: {e}")

    return None



# store fetched trailers
results = []

# subset movies
subset = movies.iloc[351:381]

# Process and fetch trailer for each movie
for index, row in subset.iterrows():

    title = row["primaryTitle"]
    year = row["startYear"]
    tconst = row["tconst"]


    # Skip if year is empty and log to file
    if year == "\\N" or not str(year).isdigit():

        with open("logs/process_log.txt", "a") as log_file:
            log_file.write(f"{tconst}, {title}, {year}, Skipped (invalid year)\n")
        continue


    # fetches movie details and logs to file if not found
    movie = get_tmdb_movie_by_imdb_id(tconst)
    if not movie:

        print(f"[{index + 1}/{len(movies)}] {title} ({year}): Movie not found")

        with open("logs/process_log.txt", "a") as log_file:
            log_file.write(f"[{index + 1}/{len(movies)}] {tconst}, {title}, {year}, Movie not found\n")
        continue


    # uses movieId in movie details to fetch trailer and logs to file if not found
    trailer_url = get_trailer_url(movie["id"])
    if not trailer_url:

        print(f"[{index + 1}/{len(movies)}] {title} ({year}): Trailer not found")

        with open("logs/process_log.txt", "a") as log_file:
            log_file.write(f"[{index + 1}/{len(movies)}] {tconst}, {title}, {year}, Trailer not found\n")
        continue

    print(f"[{index + 1}/{len(movies)}] {title} ({year}): {trailer_url}")
    
    with open("logs/process_log.txt", "a") as log_file:
        log_file.write(f"[{index + 1}/{len(movies)}] {tconst}, {title}, {year}, {trailer_url}\n")

    # Append found trailer to the results list
    results.append({
        "tconst": tconst,
        "title": title,
        "year": year,
        "trailer_url": trailer_url
    })

    # Sleep to avoid throttling
    time.sleep(0.25)



# Save to CSV
output_df = pd.DataFrame(results)
output_df.to_csv("movie_trailers_2.csv", mode='a', header=False, index=False)
