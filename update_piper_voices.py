import tools

avaliable = tools.get_available_voices_to_download()


def flatten_dict(d, parent_key='', sep='__'):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if k == "model" or k == "config":
            if parent_key not in items:
                items[parent_key] = {}
            items[parent_key][k] = v
        elif isinstance(v, dict) and v:
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


flattened_dict = flatten_dict(avaliable)

save_voices_enum = """from enum import Enum


class PiperVoicesToDownload(Enum):
"""

for key, value in flattened_dict.items():
    save_voices_enum += f"    {key.upper()} = '{key.upper()}'\n"

save_voices_enum += "\n\nvoices_map = {\n"
for key, value in flattened_dict.items():
    models_info = str(value)
    name = value['model']
    onnx_index = name.index(".onnx?")
    name = name[name[:onnx_index].rfind(key.split("__")[1]):onnx_index]
    models_info = models_info[:-1] + ", 'name': '" + name + "'}"
    save_voices_enum += f"    PiperVoicesToDownload.{key.upper()}: {models_info},\n"

save_voices_enum += "}\n"
with open("api/piper_voices.py", "w", encoding='utf-8') as fp:
    fp.write(save_voices_enum)
