import os
import yaml
import logging

from pydantic import Field
from dotenv import load_dotenv
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings


# CONFIG MAP
_FORMAT = '[%(levelname)s] %(asctime)s %(funcName)s %(message)s - '
logging.basicConfig(format=_FORMAT)
api_logger = logging.getLogger(__name__)

_log_levels = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
    'NOTSET': 0
}

api_logger.setLevel(_log_levels.get(os.getenv("LOG_LEVEL", 'DEBUG')))

# load .env
load_dotenv()


# --- Config
class AppConfig(BaseSettings):
    prefix: Optional[str] = ""
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 5501
    workers: Optional[int] = 2
    debug: bool = Field(default=False)
    piper_gpu: bool = Field(default=False)
    api_key: Optional[str] = "<not use in production>"
    piper_speaker_path: Optional[str] = "piper_speakers"

    class Config:
        env_prefix = ''
        env_file = ".env"


# --- Load
def load_config() -> AppConfig:
    config_path = os.getenv('CONFIG_PATH', 'config.yaml')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                return AppConfig(**yaml.safe_load(file))
        except Exception as e:
            api_logger.info(f"Load {config_path} fail! {e}")
    return AppConfig()


config = load_config()
if config.debug:
    api_logger.debug(config.model_dump())
