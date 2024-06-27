import json
import os
import re
import time
import tempfile
import traceback

import tools

from abc import ABC
from typing import Generator

from api.config import api_logger as log
from api.config import config


try:
    from piper.voice import PiperVoice
    from piper.download import get_voices
except Exception as e:
    traceback.print_exc()
    log.debug("PIPER ERROR No piper instalation found, not using piper")


def generate_wav_header(sample_rate, bits_per_sample, channels):
    datasize = 2000*10**6
    o = bytes("RIFF",'ascii')                                 # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4, 'little') # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                # (4byte) File type
    o += bytes("fmt ",'ascii')                                # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, 'little')            # (4byte) Length of above format data
    o += (1).to_bytes(2, 'little')             # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2, 'little')                     # (2byte)
    o += (sample_rate).to_bytes(4, 'little')                  # (4byte)
    o += ((sample_rate * channels * bits_per_sample // 8).
          to_bytes(4, 'little'))               # 4byte)
    o += ((channels * bits_per_sample // 8).
          to_bytes(2, 'little'))               # (2byte)
    o += (bits_per_sample).to_bytes(2, 'little')              # (2byte)
    o += bytes("data", 'ascii')                               # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4, 'little')      # (4byte) Data size in bytes
    return o


class PiperAvailableSpeaker:

    def __init__(self, speaker_paths: str = "./piper_speakers"):
        self.speaker_paths = speaker_paths
        self.speakers = {}
        try:
            self.load()
        except FileNotFoundError:
            log.debug(f"{speaker_paths} not found!!!")

    def load(self):
        for f in os.listdir(self.speaker_paths):
            if f.endswith(".onnx"):
                try:
                    with open(os.path.join(self.speaker_paths, f"{f}.json"), "r", encoding='utf-8') as fp:
                        speak_info = json.load(fp)
                except FileNotFoundError:
                    continue
                to_show = [
                    "audio",
                    "espeak",
                    "piper_version",
                    "language",
                    "dataset"
                ]
                self.speakers[f[:-5]] = {k: speak_info[k] for k in to_show if k in speak_info}

    def validate(self, speaker: str):
        if speaker in self.speakers:
            return True
        return False

    def get_available_speakers(self):
        self.load()
        return self.speakers

    def get_donloadable_voices(self):
        return tools.get_available_voices_to_download()

    def download(self, to_download: dict):
        if not os.path.exists(self.speaker_paths):
            os.makedirs(self.speaker_paths)
        resp1 = tools.download_file(to_download['model'], self.speaker_paths)
        resp2 = tools.download_file(to_download['config'], self.speaker_paths)
        log.info(f"download complet at {self.speaker_paths}")
        return {"model": resp1, "config": resp2}


class PiperOffline(ABC):

    def __init__(
            self,
            speaker: str = "",
            speaker_paths: str = "./piper_speakers",
    ):
        self.speaker = speaker
        piper_info = PiperAvailableSpeaker(config.piper_speaker_path)
        voice_info = piper_info.get_available_speakers().get(speaker, {})
        self.sample_rate = voice_info.get("audio", {}).get("sample_rate", 22050)

        self.speaker_paths = speaker_paths

    def download_windows(self):
        #  TODO
        save_dir = os.path.join(config.piper_speaker_path, "piper")
        self.piper_exe = str(os.path.abspath(os.path.join(save_dir, "piper/piper.exe")))
        if os.path.exists(save_dir):
            return
        with tempfile.NamedTemporaryFile(mode='w+', delete=True) as ta:

            tools.download_file(
                "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip",
                ta.tmp_file
            )
            tools.extract_zip(
                ta.tmp_file,
                save_dir
            )

    def set_speaker(self, speaker: str):
        self.speaker = speaker
        piper_info = PiperAvailableSpeaker(config.piper_speaker_path)
        voice_info = piper_info.get_available_speakers().get(speaker, {})
        self.sample_rate = voice_info.get("audio", {}).get("sample_rate", 22050)

    async def streaming(self, text: str) -> Generator[bytes, None, None]:
        start_time = time.time()
        voice = PiperVoice.load(
            model_path=os.path.join(self.speaker_paths, self.speaker),
            config_path=None,
            use_cuda=config.piper_gpu
        )
        text = text.replace('\n', '')
        bits_per_sample = 16
        num_channels = 1

        yield generate_wav_header(self.sample_rate, bits_per_sample, num_channels)
        for t in tools.split_text_with_punctuation(text):
            t = t.strip()
            if t == "":
                continue
            log.debug("|" + t + "|")
            try:
                for raw_audio_chunk in voice.synthesize_stream_raw(t, sentence_silence=1.0):
                    yield raw_audio_chunk
                    log.debug(f"Time raw to wav: {time.time() - start_time}")
            except Exception as e:
                # Fix a bug in piper to long texts
                log.debug("|Retrying|")
                voice = PiperVoice.load(
                    model_path=self.speaker,
                    config_path=None,
                    use_cuda=config.piper_gpu
                )
                for raw_audio_chunk in voice.synthesize_stream_raw(t, sentence_silence=1.0):
                    yield raw_audio_chunk
                    log.debug(f"Time raw to wav: {time.time() - start_time}")


