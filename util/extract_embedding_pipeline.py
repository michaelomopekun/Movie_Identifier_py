import logging
from processTrailerService import ProcessTrailers
from process_movies import ProcessMovies
from downLoad_Trailer import DownloadMovieTrailers


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def safe_init(cls, name):
    try:
        return cls()
    except Exception as e:
        logger.error(f"Error initializing {name}: {e}")
        raise

def safe_run(func, name):
    try:
        func()
    except Exception as e:
        logger.error(f"Error running {name}: {e}")
        raise


if __name__ == "__main__":

    process_movies_instance = safe_init(ProcessMovies, "ProcessMovies")

    safe_run(process_movies_instance.process_movies, "process_movies")

    download_trailer_instance = safe_init(DownloadMovieTrailers, "DownloadMovieTrailers")

    safe_run(download_trailer_instance.download_trailer, "download_trailer")
    
    process_trailer_service_instance = safe_init(ProcessTrailers, "ProcessTrailers")

    safe_run(process_trailer_service_instance.processTrailer, "processTrailer")
    
    logger.info("All processes completed successfully.")