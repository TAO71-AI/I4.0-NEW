"""
> [!WARNING]
> THIS SCRIPT MIGHT NOT WORK WITH NEWER PYTORCH VERSIONS. THIS SCRIPT STILL NEEDS TO BE TESTED.
"""
from typing import Any
from collections.abc import Generator
from io import BytesIO
from heartlib import HeartMuLaGenPipeline
import json
import base64
import torch
import Server.Utilities.model_utils as model_utils

def LoadModel(Configuration: dict[str, Any]) -> HeartMuLaGenPipeline:
    if (isinstance(Configuration["_private_device"], dict) and (
        "mula" in Configuration["_private_device"] and "codec" in Configuration["_private_device"]
    )):
        mulaDeviceM = Configuration["_private_device"]["mula"]
        mulaDeviceC = Configuration["_private_device"]["codec"]
    elif (isinstance(Configuration["_private_device"], str)):
        mulaDeviceM = Configuration["_private_device"]
        mulaDeviceC = Configuration["_private_device"]
    else:
        raise ValueError("Invalid device for MuLa.")
        
    if (isinstance(Configuration["dtype"], dict) and (
        "mula" in Configuration["dtype"] and "codec" in Configuration["dtype"]
    )):
        mulaDTypeM = Configuration["dtype"]["mula"]
        mulaDTypeC = Configuration["dtype"]["codec"]
    elif (isinstance(Configuration["dtype"], str)):
        mulaDTypeM = Configuration["dtype"]
        mulaDTypeC = Configuration["dtype"]
    else:
        raise ValueError("Invalid dtype for MuLa.")
        
    lazyLoad = Configuration["_private_mula_lazy"] if ("_private_mula_lazy" in Configuration) else True
    model = HeartMuLaGenPipeline.from_pretrained(
        pretrained_path = Configuration["_private_model_path"],
        device = {
            "mula": torch.device(mulaDeviceM),
            "codec": torch.device(mulaDeviceC)
        },
        dtype = {
            "mula": model_utils.StringToDType(mulaDTypeM),
            "codec": model_utils.StringToDType(mulaDTypeC)
        },
        version = Configuration["mula_version"],
        lazy_load = lazyLoad
    )

    return model

def InferenceModel(
    InputPrompt: str | dict[str, str],
    Model: HeartMuLaGenPipeline,
    MaxLength: int,
    TopK: int,
    Temperature: float,
    CFGScale: float
) -> Generator[dict[str, Any]]:
    try:
        if (isinstance(InputPrompt, str)):
            txtJson = json.loads(InputPrompt)
        else:
            txtJson = InputPrompt

        lyrics = txtJson["lyrics"]
        tags = txtJson["tags"]
    except (json.JSONDecodeError, KeyError):
        yield {"errors": ["Could not inference model. Text must be in a JSON format and must include the tags 'lyrics' and 'tags'."]}
        return
    
    buffer = BytesIO()
    
    with torch.no_grad():
        Model(
            {
                "lyrics": lyrics,
                "tags": tags
            },
            max_audio_length_ms = MaxLength * 1000,
            save_path = buffer,
            topk = TopK,
            temperature = Temperature,
            cfg_scale = CFGScale
        )
    
    bufferBytes = buffer.getvalue()
    buffer.close()

    yield {"files": [{"type": "audio", "audio": base64.b64encode(bufferBytes).decode("utf-8")}]}  # Streaming not allowed for now