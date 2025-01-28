import os
import traceback

from fastapi import FastAPI
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from api import doc_speech
from api.piper_voices import PiperVoicesToDownload, voices_map

from api.config import config
from api.config import api_logger as log

import api.piper_com as pc
from api.version import __version__


app = FastAPI(
    title="Single TTS API Piper.",
    version=__version__,
    contact={
        "name": "Anusio",
        "email": "anusio@gmail.com",
    },
    root_path=config.prefix
)


allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/text_to_speech/",
    response_model=doc_speech.TextToSpeechResponse,
    responses={
        status.HTTP_200_OK: {"content": {"audio/wav": {"example": "voice.wav"}}}
    },
    response_class=StreamingResponse,
    tags=["TTS"]
    )
async def text_to_speech(
        payload: doc_speech.TextToSpeech
):
    """
    get text and returns its AI generated audio
    """
    piper_info = pc.PiperAvailableSpeaker(config.piper_speaker_path)
    if not piper_info.validate(payload.speaker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "msg": f"speaker {payload.speaker} not avaliable",
                "available": [x for x in piper_info.get_available_speakers()]
            }
        )

    tts_inst = pc.PiperOffline(payload.speaker+".onnx")
    return StreamingResponse(tts_inst.streaming(payload.text), media_type="audio/wav")


@app.get(
    "/text_to_speech/",
    response_model=doc_speech.TextToSpeechResponse,
    responses={
        status.HTTP_200_OK: {"content": {"audio/wav": {"example": "voice.wav"}}},
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {
                "example": {
                        "msg": "Speaker not found",
                        "available": ["Speaker1", "Speaker2"]
                    }
                }
            }
        }
    },
    response_class=StreamingResponse,
    tags=["TTS"]
)
async def text_to_speech_get(
        text: str,
        speaker: str = doc_speech.available_models[0]
):
    """
    get text and returns its AI generated audio (as **get** to be used by swagger)
    """
    piper_info = pc.PiperAvailableSpeaker(config.piper_speaker_path)
    if not piper_info.validate(speaker):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "msg": f"speaker {speaker} not avaliable",
                "available": [x for x in piper_info.get_available_speakers()]
            }
        )

    tts_inst = pc.PiperOffline(speaker+".onnx")
    return StreamingResponse(tts_inst.streaming(text), media_type="audio/wav")


@app.get(
    "/list_to_avalilable/",
    # response_model=doc_speech.AvailableResponse,
    responses=doc_speech.response_available,
    tags=["Models"]
)
async def list_to_avalilable():
    """
    List all models available to use
    """
    piper_info = pc.PiperAvailableSpeaker(config.piper_speaker_path)
    return piper_info.get_available_speakers()


@app.get(
    "/list_to_download/",
    # response_model=doc_speech.DownloadListResponse,
    responses=doc_speech.response_download_list,
    tags=["Models"]
)
async def list_to_download():
    """
    List all models available to download by piper
    """
    return {m.name: voices_map[m] for m in PiperVoicesToDownload}


@app.get(
    "/download/",
    # response_model=doc_speech.DownloadResponse,
    responses=doc_speech.response_download,
    tags=["Models"]
)
async def download(
        voice: PiperVoicesToDownload
):
    """
    Download a model available to download by piper
    """
    piper_info = pc.PiperAvailableSpeaker(config.piper_speaker_path)
    return piper_info.download(voices_map[voice])

