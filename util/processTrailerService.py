import os
import cv2
import numpy as np
from tqdm import tqdm
from PIL import Image
from pathlib import Path
import onnxruntime as ort
from datetime import datetime
from dotenv import load_dotenv
from chromadb import PersistentClient
from transformers import CLIPProcessor
load_dotenv()




class ProcessTrailers:

    def __init__(self):

        #file paths
        self.parent_dir = Path(__file__).resolve().parent.parent

        self.path_processed_frame_log = self.parent_dir / "logs" / "processed_frame_log.txt"
        if not self.path_processed_frame_log.exists():
            self.path_processed_frame_log.touch()

        self.path_processing_video_frame_log = self.parent_dir / "logs" / "processing_video_frame_log.txt"
        if not self.path_processing_video_frame_log.exists():
            self.path_processing_video_frame_log.touch()

        self.path_visual_onnx = self.parent_dir / "onnx" / "visual.onnx"

        self.path_chromadb = self.parent_dir / "chromaDB"


        # initialize onnx
        providers = ['DmlExecutionProvider']

        session = ort.InferenceSession(self.path_visual_onnx, providers = providers)

        self.clipProcessor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

        print("Active ONNX Providers:", session.get_providers())

        with open(self.path_processed_frame_log, "a", encoding="utf-8") as log_file:
            log_file.write(f"Input name: {session.get_inputs()[0].name} :: at logtime:: {datetime.now()}\n")


        # initialize chromadb
        chromaClient = PersistentClient(str(self.path_chromadb))

        self.collection = chromaClient.get_or_create_collection(name="moviesTrailerEmbeddings")




    def extractFrames(self, videoPath, numFrames=int(os.getenv("NUMBER_OF_FRAMES", 100))):

        cap = cv2.VideoCapture(videoPath)
        totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if totalFrames < numFrames:
            frameIds = list(range(totalFrames))
        else:
            step = totalFrames // numFrames
            frameIds = [i * step for i in range(numFrames)]


        frames = []

        for frameId in frameIds:

            cap.set(cv2.CAP_PROP_POS_FRAMES, frameId)

            success, frame = cap.read()

            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                frames.append(Image.fromarray(frame))

                with open(self.path_processed_frame_log, "a", encoding="utf-8") as log_file:
                    log_file.write(f"✅successfully read frame {frameId} from {videoPath}\n")

                print(f"✅successfully read frame {frameId} from {videoPath}")
            else:
                with open(self.path_processed_frame_log, "a", encoding="utf-8") as log_file:
                    log_file.write(f"❌Failed to read frame {frameId} from {videoPath}\n")

                print(f"❌Failed to read frame {frameId} from {videoPath}")
                continue

        cap.release()

        return frames



    def getClipEmbedding(self, frames):

        inputs = self.clipProcessor(images = frames, return_tensors = "pt", padding = True)["pixel_values"].numpy()

        outputs = self.session.run(None, {"input": inputs})

        embeddings = outputs[0]
        
        embeddings = embeddings / np.linalg.norm(embeddings, axis =- 1, keepdims = True)

        return embeddings.mean(axis = 0)



    def process_extracted_frames(self, tconst, path):

        frames = self.extractFrames(path)

        if not frames:
            with open(self.path_processing_video_frame_log, "a", encoding="utf-8") as log_file:
                log_file.write(f"❌Failed to extract frame for {tconst} from path: {path}\n")
            return

        vector = self.getClipEmbedding(frames)

        # vector

        self.collection.add( documents = [f"Trailer for {tconst}"],
                        embeddings = [vector],
                        ids = [tconst],
                        metadatas = [{"filename": path}]
                        )

        with open(self.path_processing_video_frame_log, "a", encoding="utf-8") as log_file:
            log_file.write(f"✅stored embedding for {tconst} from path: {path}\n")



    def processTrailer(self, tconst, path):

        # loop through each trailer to extract embedding
        trailerDirectory = os.path.join(self.parent_dir, "trailers")

        aboutToProcessTrailers = [f for f in os.listdir(trailerDirectory) if f.endswith(".mp4")][:100]

        for file in tqdm(aboutToProcessTrailers):

                tconst = file.replace(".mp4", "")

                filePath = os.path.join(trailerDirectory, file)

                self.process_extracted_frames(tconst, filePath)



