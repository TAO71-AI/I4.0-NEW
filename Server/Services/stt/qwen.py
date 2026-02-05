from typing import Any
from collections.abc import Generator
from qwen_asr import Qwen3ASRModel
import json
import Utilities.model_utils as model_utils

def LoadModel(Configuration: dict[str, Any], InitMaxLength: int, Batch: int) -> Qwen3ASRModel:
    if ("_private_aligner_device" not in Configuration):
        Configuration["_private_aligner_device"] = "cpu"
    
    if ("aligner_dtype" not in Configuration):
        Configuration["aligner_dtype"] = "float32"
    
    model = Qwen3ASRModel.from_pretrained(
        pretrained_model_name_or_path = Configuration["_private_model_path"],
        max_inference_batch_size = Batch,
        max_new_tokens = InitMaxLength,
        device_map = Configuration["_private_device"],
        dtype = model_utils.StringToDType(Configuration["dtype"]),
        attn_implementation = model_utils.GetAttnImpl(Configuration),
        forced_aligner = Configuration["_private_aligner_path"] if ("_private_aligner_path" in Configuration) else None,
        forced_aligner_kwargs = {
            "device_map": Configuration["_private_aligner_device"],
            "dtype": model_utils.StringToDType(Configuration["aligner_dtype"]),
            "attn_implementation": model_utils.GetAttnImpl(Configuration, "aligner_attn")
        } if ("_private_aligner_path" in Configuration) else None
    )

    return model

def InferenceModel(
    InputPrompt: list[dict[str, str | dict[str, str]]],
    Model: Qwen3ASRModel,
    MaxLength: int | None
) -> Generator[dict[str, Any]]:
    audios = []
    latestTxt = "{}"

    for message in InputPrompt:
        if (message["role"] != "user"):
            continue

        for content in message["content"]:
            if (content["type"] == "audio"):
                audios.append(f"data:audio;base64,{content['audio']}")
            elif (content["type"] == "text"):
                latestTxt = content["text"]

    if (len(audios) == 0):
        raise ValueError("No input audios for ASR.")

    ctx = ""
    lang = None
    ts = False
    
    try:
        jsonData = json.loads(latestTxt)

        if ("ctx" in jsonData):
            ctx = jsonData["ctx"]
        
        if ("lang" in jsonData):
            lang = jsonData["lang"]
        
        if ("time_stamps" in jsonData):
            ts = jsonData["time_stamps"]
    except (json.JSONDecodeError, KeyError):
        yield {"warnings": ["Invalid JSON data. Ignoring and using default values."]}
    
    if (not isinstance(ctx, list)):
        ctx = [ctx]
    
    while (len(audios) > len(ctx)):
        ctx.append("")
    
    if (not isinstance(lang, list)):
        lang = [lang]
    
    while (len(audios) > len(lang)):
        lang.append(None)
    
    if (MaxLength is not None):
        Model.max_new_tokens = MaxLength

    results = Model.transcribe(audio = audios, context = ctx, language = lang, return_time_stamps = ts)

    for result in results:
        yield {"text": result.text, "extra": {"time_stamps": result.time_stamps, "language": result.language}}