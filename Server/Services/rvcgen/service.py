from typing import Any
from collections.abc import Generator
from io import BytesIO
from rvc.modules.vc.modules import VC
import os
import base64
import time
import psutil
import logging
import soundfile as sf
import Utilities.logs as logs
import Utilities.model_utils as model_utils

__models__: dict[str, dict[str, Any]] = {}
ServiceConfiguration: dict[str, Any] | None = None
ServerConfiguration: dict[str, Any] | None = None

def __check_service_configuration__() -> None:
    if (ServiceConfiguration is None):
        raise ValueError("Service configuration is not defined.")
    
    if (ServerConfiguration is None):
        raise ValueError("Server configuration is not defined.")

def SERVICE_LOAD_MODELS(Models: dict[str, dict[str, Any]]) -> None:
    for modelName, modelConfiguration in Models.items():
        LoadModel(modelName, modelConfiguration)

def SERVICE_OFFLOAD_MODELS(Names: list[str]) -> None:
    __check_service_configuration__()

    for name in Names:
        if (__models__[name]["_private_model"] is None):
            continue
        
        logs.WriteLog(logs.INFO, "[service_rvcgen] Offloading model.")
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    LoadModel(Name, ServerConfiguration["services"][Name])

    audios = []
    f0 = UserConfig["f0"] if ("f0" in UserConfig and isinstance(UserConfig["f0"], int) and ServiceConfiguration["f0"]["modified_by_user"]) else ServiceConfiguration["f0"]["default"]
    protect = UserConfig["protect"] if ("protect" in UserConfig and isinstance(UserConfig["protect"], float) and ServiceConfiguration["protect"]["modified_by_user"]) else ServiceConfiguration["protect"]["default"]
    filterR = UserConfig["filter_radius"] if ("filter_radius" in UserConfig and isinstance(UserConfig["filter_radius"], int) and ServiceConfiguration["filter_radius"]["modified_by_user"]) else ServiceConfiguration["filter_radius"]["default"]
    idxR = UserConfig["index_rate"] if ("index_rate" in UserConfig and isinstance(UserConfig["index_rate"], float) and ServiceConfiguration["index_rate"]["modified_by_user"]) else ServiceConfiguration["index_rate"]["default"]
    mixR = UserConfig["mix_rate"] if ("mix_rate" in UserConfig and isinstance(UserConfig["mix_rate"], float) and ServiceConfiguration["mix_rate"]["modified_by_user"]) else ServiceConfiguration["mix_rate"]["default"]

    for msg in UserParameters["conversation"]:
        if (msg["role"] != "user"):
            continue

        for cont in msg["content"]:
            if (cont["type"] != "audio"):
                continue

            audios.append(base64.b64decode(cont["audio"]))

    for audio in audios:
        fileID = 0

        while (os.path.exists(f"Temp/audio_{fileID}.wav")):
            fileID += 1
        
        with open(f"Temp/audio_{fileID}.wav", "wb") as f:
            f.write(audio)

        os.environ["rmvpe_root"] = __models__[Name]["_private_rmvpe"]
        sr, output, _, _ = __models__[Name]["_private_model"].vc_inference(
            sid = 1,
            input_audio_path = f"Temp/audio_{fileID}.wav",
            f0_method = __models__[Name]["_private_type"],
            f0_up_key = f0,
            protect = protect,
            filter_radius = filterR,
            hubert_path = __models__[Name]["_private_hubert"],
            index_file = __models__[Name]["_private_index_path"],
            index_rate = idxR,
            rms_mix_rate = mixR
        )
        buffer = BytesIO()
        sf.write(buffer, output, sr, format = "WAV")

        if (os.path.exists(f"Temp/audio_{fileID}.wav")):
            os.remove(f"Temp/audio_{fileID}.wav")

        yield {"files": [{"type": "audio", "audio": base64.b64encode(buffer.getvalue()).decode("utf-8")}]}
        buffer.close()

def LoadModel(ModelName: str, Configuration: dict[str, Any]) -> None:
    __check_service_configuration__()

    if (ModelName in __models__ and __models__[ModelName]["_private_model"] is not None):
        return
    
    loadTime = time.time()
    logs.WriteLog(logs.INFO, "[service_rvcgen] Loading model...")
    logs.PrintLog(logs.WARNING, "[service_rvcgen] Keep in mind that Retrieval-based Voice Conversion (RVC) does not receive updates often. The library is old and may be deprecated, newer dependencies versions or hardware may break it. This module does not work out of the box, you need to modify Python scripts to be able to get it work properly.")

    if ("index_root" not in os.environ):
        os.environ["index_root"] = ""
    
    if ("rmvpe_root" not in os.environ):
        os.environ["rmvpe_root"] = ""
    
    #if ("hubert_path" not in os.environ):
    #    os.environ["hubert_path"] = ""

    if ("_private_device" not in Configuration):
        Configuration["_private_device"] = "cpu"
    
    if ("dtype" not in Configuration):
        Configuration["dtype"] = "float32"
    
    if ("_private_threads" not in Configuration):
        Configuration["_private_threads"] = -1
    
    if ("_private_version" not in Configuration):
        Configuration["_private_version"] = "v2"
    
    model = VC()
    model.version = Configuration["_private_version"]

    if (Configuration["_private_device"] in ["cuda", "xpu"]):
        model.config.use_cuda()
    elif (Configuration["_private_device"] == "dml"):
        model.config.use_dml()
    elif (Configuration["_private_device"] == "mps"):
        model.config.use_mps()
    elif (Configuration["_private_device"] == "cpu"):
        model.config.use_cpu()
    else:
        raise ValueError("Invalid device for RVC.")
    
    if (Configuration["_private_threads"] == -1):
        model.config.n_cpu = psutil.cpu_count()
    elif (not isinstance(Configuration["_private_threads"], int) or Configuration["_private_threads"] <= 0 or Configuration["_private_threads"] > psutil.cpu_count()):
        raise ValueError("Invalid threads number for RVC.")
    else:
        model.config.n_cpu = Configuration["_private_threads"]

    if ("_private_type" not in Configuration or Configuration["_private_type"] not in ["rmvpe", "crepe", "harvest", "pm"]):
        raise ValueError("Invalid RVC type.")

    if ("_private_model_path" not in Configuration or not os.path.exists(Configuration["_private_model_path"]) or not os.path.isfile(Configuration["_private_model_path"])):
        raise FileNotFoundError("RVC model file not found.")
    
    if ("_private_hubert_model_path" in Configuration and os.path.exists(Configuration["_private_hubert_model_path"]) and os.path.isfile(Configuration["_private_hubert_model_path"])):
        # Recommended HUBERT: https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/hubert_base.pt
        hubert = Configuration["_private_hubert_model_path"]
    else:
        if (os.path.exists(ServiceConfiguration["hubert_model_path"]) and os.path.isfile(ServiceConfiguration["hubert_model_path"])):
            hubert = ServiceConfiguration["hubert_model_path"]
        else:
            raise FileNotFoundError("HUBERT model not found for RVC.")
    
    if ("_private_rmvpe_model_dir" in Configuration and os.path.exists(f"{Configuration['_private_rmvpe_model_dir']}/rmvpe.pt") and os.path.isfile(f"{Configuration['_private_rmvpe_model_dir']}/rmvpe.pt")):
        # Recommended RMVPE: https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/rmvpe.pt
        rmvpe = Configuration["_private_rmvpe_model_dir"]
    else:
        if (os.path.exists(f"{ServiceConfiguration['rmvpe_model_dir']}/rmvpe.pt") and os.path.isfile(f"{ServiceConfiguration['rmvpe_model_dir']}/rmvpe.pt")):
            rmvpe = ServiceConfiguration["rmvpe_model_dir"]
        elif (Configuration["_private_type"] == "rmvpe"):
            raise FileNotFoundError("RMVPE model not found for RVC.")
        else:
            rmvpe = ""

    if ("_private_index_path" not in Configuration):
        Configuration["_private_index_path"] = None
    
    model.config.use_jit = False
    model.config.is_half = model_utils.StringToDType(Configuration["dtype"]) in [model_utils.torch.float16, model_utils.torch.bfloat16]
    model.get_vc(Configuration["_private_model_path"])
    
    __models__[ModelName] = Configuration | {
        "_private_model": model,
        "_private_hubert": hubert,
        "_private_rmvpe": rmvpe
    }

    loadTime = round(time.time() - loadTime, 3)
    logs.WriteLog(logs.INFO, f"[service_rvcgen] Model loaded in {loadTime} seconds.")

logging.disable(logging.CRITICAL)