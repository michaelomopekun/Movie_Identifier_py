import os
import cv2
from chromadb import PersistentClient
import numpy as np
from tqdm import tqdm
from PIL import Image
import onnxruntime as ort
from datetime import datetime
from dotenv import load_dotenv
from transformers import CLIPProcessor
load_dotenv()


# initialize onnx
providers = ['DmlExecutionProvider']
# ort.set_default_logger_severity(0) 
session = ort.InferenceSession("visual.onnx", providers = providers)
clipProcessor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")
print("Active ONNX Providers:", session.get_providers())

with open("session_input_log.txt", "a", encoding="utf-8") as log_file:
    log_file.write(f"Input name: {session.get_inputs()[0].name} :: at logtime:: {datetime.now()}\n")



# initialize chromadb
chromaClient = PersistentClient(path="./chromaDB")
collection = chromaClient.get_or_create_collection(name="moviesTrailerEmbeddings")



def extractFrames(videoPath, numFrames=int(os.getenv("NUMBER_OF_FRAMES", 50))):

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

            with open("processed_frame_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"✅successfully read frame {frameId} from {videoPath}\n")

            print(f"✅successfully read frame {frameId} from {videoPath}")
        else:
            with open("processed_frame_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"❌Failed to read frame {frameId} from {videoPath}\n")

            print(f"❌Failed to read frame {frameId} from {videoPath}")
            continue

    cap.release()

    return frames


def getClipEmbedding(frames):

    inputs = clipProcessor(images = frames, return_tensors = "pt", padding = True)["pixel_values"].numpy()

    outputs = session.run(None, {"input": inputs})

    embeddings = outputs[0]
    
    embeddings = embeddings / np.linalg.norm(embeddings, axis =- 1, keepdims = True)

    return embeddings.mean(axis = 0)


def processTrailer(tconst, path):

    frames = extractFrames(path)

    if not frames:
        with open("processing_vedio_frame_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"❌Failed to extract frame for {tconst} from path: {path}\n")
        return
    
    vector = getClipEmbedding(frames)

    # vector

    collection.add( documents = [f"Trailer for {tconst}"],
                    embeddings = [vector],
                    ids = [tconst],
                    metadatas = [{"filename": path}]
                    )
    
    with open("processing_vedio_frame_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"✅stored embedding for {tconst} from path: {path}\n")


# loop through each trailer to extract embedding
trailerDirectory = "trailers"

aboutToProcessTrailers = [f for f in os.listdir(trailerDirectory) if f.endswith(".mp4")][80:99]

for file in tqdm(aboutToProcessTrailers):

        tconst = file.replace(".mp4", "")

        filePath = os.path.join(trailerDirectory, file)

        processTrailer(tconst, filePath)


                

