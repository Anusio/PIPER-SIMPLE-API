from pydantic import BaseModel
from datetime import datetime
from typing import List
from fastapi import Depends, FastAPI, Request, Path, status

import api.piper_com as pc
from api.config import config
from api.config import api_logger as log

from api.piper_voices import voices_map

available_models = [str(e) for e in pc.PiperAvailableSpeaker(config.piper_speaker_path).get_available_speakers()]
available_models = available_models + [str(v['name']) for k, v in voices_map.items() if v['name'] not in available_models]


class TextToSpeech(BaseModel):
    text: str
    speaker: str = available_models[0]


class TextToSpeechResponse(BaseModel):
    dados: bytes


response_available = {
    status.HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {
                    "speaker": {
                        "audio": {
                            "sample_rate": 22000,
                            "quality": "low"
                        },
                        "espeak": {
                            "voice": "tag"
                        },
                        "piper_version": "0.1.0",
                        "language": {
                            "code": "tag",
                            "family": "tag",
                            "region": "tag",
                            "name_native": "Lang",
                            "name_english": "Lang",
                            "country_english": "Country"
                        },
                        "dataset": "dataset"
                    },
                }
            }
        }
    }
}

response_download_list = {
    status.HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {
                    "NAME__TAG__DATASET__QUALITY": {
                        "model": "url to download onnx",
                        "config": "url to download onnx.json",
                        "name": "speaker name"
                      }
                }
            }
        }
    }
}


response_download = {
    status.HTTP_200_OK: {
        "content": {
            "application/json": {
                "example": {
                    "model": {
                        "msg": "New language voice speaker.onnx"
                    },
                    "config": {
                        "msg": "New language voice speaker.onnx.json"
                    }
                }
            }
        }
    }
}




