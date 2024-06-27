import os
import re
import zipfile
import requests
import traceback
from api.config import api_logger as log


def get_suggested_filename(response, default_filename):
    content_disposition = response.headers.get('Content-Disposition')
    if not content_disposition:
        return default_filename

    filename_match = re.findall('filename="([^"]+)"', content_disposition)
    if filename_match:
        return filename_match[0]
    else:
        return default_filename


def download_file(file_url: str, local_file_name: str):
    response = requests.get(file_url)
    base_name = os.path.basename(
        get_suggested_filename(response, "temp")
    )
    local_file_name = os.path.join(
        local_file_name,
        base_name
    )
    if os.path.exists(local_file_name):
        return {"msg": f"{base_name} already exists!"}
    if response.status_code == 200:
        with open(local_file_name, 'wb') as file:
            file.write(response.content)
        log.debug(f"Download of '{local_file_name}' completed successfully.")
        return {"msg": f"New language voice {base_name}"}
    else:
        log.debug("Failed to download the file. Status code:", response.status_code)
        return {"msg": f"Error {base_name} {response.status_code}"}


def extract_zip(zip_file_path: str, destination_folder: str):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_folder)

    log.debug("ZIP file extracted successfully.")


def parse_model_config_links(text: str) -> dict:
    pattern = re.compile(r'\[\[model\]\(([^)]+)\)\] \[\[config\]\(([^)]+)\)\]')
    match = pattern.search(text)
    if match:
        model_url, config_url = match.groups()
        return {'model': model_url, 'config': config_url}
    else:
        return {}


def get_available_voices_to_download(file_path:str = "./piper_voices.md") -> dict:
    voices = {}
    with open(file_path, "r", encoding='utf-8') as fp:
        at_lang = ""
        at_voice = ""
        tag = ""
        try:
            for line in fp.readlines():
                if line.strip().startswith("#"):
                    continue
                elif line.startswith("*"):
                    at_lang = line[2:line.index("(")-1]
                    comma = ","
                    if "," not in line:
                        comma = ")"
                    tag = line[line.index("(")+1:line.index(comma)]
                    tag = tag.replace('`', '')
                    if at_lang not in voices:
                        voices[at_lang] = {
                            tag: {}
                        }
                    else:
                        voices[at_lang][tag] = {}

                elif line.startswith("    *"):
                    at_voice = line[line.index("*")+1:].strip()
                    voices[at_lang][tag][at_voice] = {}

                elif line.startswith("        *"):
                    v_type = line[line.index("*")+1: line.index("-")].strip()

                    voices[at_lang][tag][at_voice][v_type] = parse_model_config_links(line[line.index('['):])
        except Exception as e:
            traceback.print_exc()

    return voices


def split_text_with_punctuation(text):
    pattern = r'([\.\?!:;])'
    parts = re.split(pattern, text)

    splitted_text = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            splitted_text.append(parts[i] + parts[i + 1])
        elif i == len(parts) - 1:
            splitted_text.append(parts[i])

    return splitted_text
