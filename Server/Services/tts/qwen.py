from typing import Any, Literal
from collections.abc import Generator
from io import BytesIO
from qwen_tts import Qwen3TTSModel
import json
import base64
import soundfile as sf
import Utilities.model_utils as model_utils

def LoadModel(Configuration: dict[str, Any]) -> Qwen3TTSModel:
    model = Qwen3TTSModel.from_pretrained(
        pretrained_model_name_or_path = Configuration["_private_model_path"],
        device_map = Configuration["_private_device"],
        dtype = model_utils.StringToDType(Configuration["dtype"]),
        attn_implementation = model_utils.GetAttnImpl(Configuration)
    )

    return model

def InferenceModel(
    InputPrompt: list[dict[str, str | dict[str, str]]],
    Model: Qwen3TTSModel,
    Type: Literal["voice_design", "voice_clone"],
    TopK: int,
    TopP: float,
    Temperature: float,
    RepetitionPenalty: float,
    MaxLength: int
) -> Generator[dict[str, Any]]:
    latestInstruction = ""
    latestAudio = None
    latestTxt = None

    for message in InputPrompt:
        if (message["role"] != "user" and message["role"] != "system"):
            continue

        for content in message["content"]:
            if (content["type"] == "audio" and message["role"] == "user"):
                latestAudio = f"data:audio;base64,{content['audio']}"
            elif (content["type"] == "text"):
                if (message["role"] == "user"):
                    latestTxt = content["text"]
                elif (message["role"] == "system"):
                    latestInstruction = content["text"]

    if (latestTxt is None):
        raise ValueError("No input text for TTS.")
    
    try:
        jsonData = json.loads(latestTxt)
        ttsPrompt = str(jsonData["prompt"])
        ttsLanguage = str(jsonData["lang"]) if ("lang" in jsonData) else str(jsonData["language"]) if ("language" in jsonData) else None  # None = Automatic
        ttsReferenceText = str(jsonData["reference_text"]) if ("reference_text" in jsonData) else str(jsonData["ref_text"]) if ("ref_text" in jsonData) else None  # None = Use X-vector only
        ttsSpeaker = str(jsonData["speaker"]) if ("speaker" in jsonData) else None
    except (json.JSONDecodeError, KeyError):
        raise ValueError("Invalid prompt for TTS. Make sure you're using a JSON format and it has all the required keys (`prompt`).")

    globalModelArgs = {
        "text": ttsPrompt,
        "language": ttsLanguage,
        "non_streaming_mode": True,
        "top_k": TopK,
        "top_p": TopP,
        "temperature": Temperature,
        "repetition_penalty": RepetitionPenalty,
        "max_new_tokens": MaxLength
    }
    
    if (Type == "voice_design"):
        wavs, sr = Model.generate_voice_design(
            instruct = latestInstruction,
            **globalModelArgs
        )
    elif (Type == "voice_custom"):
        wavs, sr = Model.generate_custom_voice(
            speaker = ttsSpeaker,
            instruct = latestInstruction,
            **globalModelArgs
        )
    elif (Type == "voice_clone"):
        if (latestAudio is None):
            raise ValueError("No reference audio for TTS voice cloning.")

        wavs, sr = Model.generate_voice_clone(
            ref_audio = latestAudio,
            ref_text = ttsReferenceText,
            x_vector_only_mode = ttsReferenceText is None,
            **globalModelArgs
        )
    else:
        raise ValueError("Invalid Qwen3-TTS type.")
    
    for wav in wavs:
        buffer = BytesIO()
        sf.write(buffer, wav, sr, format = "WAV")

        yield {"files": [{"type": "audio", "audio": base64.b64encode(buffer.getvalue()).decode("utf-8")}]}
        buffer.close()