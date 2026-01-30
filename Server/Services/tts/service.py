from typing import Any
from collections.abc import Generator
import time
import Services.tts.qwen as qwen
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
        
        logs.WriteLog(logs.INFO, "[service_audgen] Offloading model.")
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    LoadModel(Name, ServerConfiguration["services"][Name])
    
    if ("max_length" in UserConfig and ServiceConfiguration["max_length"]["modified_by_user"]):
        maxLength = UserConfig["max_length"]
    elif ("max_length" in __models__[Name]):
        maxLength = __models__[Name]["max_length"]
    else:
        maxLength = ServiceConfiguration["max_length"]["default"]
    
    if (maxLength > ServiceConfiguration["max_length"]["default"] and not ServiceConfiguration["max_length"]["allow_greater_than_default"]):
        maxLength = ServiceConfiguration["max_length"]["default"]
    
    if ("temperature" in UserConfig and ServiceConfiguration["temperature"]["modified_by_user"]):
        temperature = UserConfig["temperature"]
    elif ("temperature" in __models__[Name]):
        temperature = __models__[Name]["temperature"]
    else:
        temperature = ServiceConfiguration["temperature"]["default"]
    
    if ("top_k" in UserConfig and ServiceConfiguration["top_k"]["modified_by_user"]):
        top_k = UserConfig["top_k"]
    elif ("top_k" in __models__[Name]):
        top_k = __models__[Name]["top_k"]
    else:
        top_k = ServiceConfiguration["top_k"]["default"]
    
    if ("top_p" in UserConfig and ServiceConfiguration["top_p"]["modified_by_user"]):
        top_p = UserConfig["top_p"]
    elif ("top_p" in __models__[Name]):
        top_p = __models__[Name]["top_p"]
    else:
        top_p = ServiceConfiguration["top_p"]["default"]
    
    if ("repeat_penalty" in UserConfig and ServiceConfiguration["repeat_penalty"]["modified_by_user"]):
        repeat_penalty = UserConfig["repeat_penalty"]
    elif ("repeat_penalty" in __models__[Name]):
        repeat_penalty = __models__[Name]["repeat_penalty"]
    else:
        repeat_penalty = ServiceConfiguration["repeat_penalty"]["default"]

    if (__models__[Name]["_private_type"] == "qwen"):
        return qwen.InferenceModel(
            InputPrompt = UserParameters["conversation"],
            Model = __models__[Name]["_private_model"],
            Type = __models__[Name]["voice_type"],
            TopK = top_k,
            TopP = top_p,
            Temperature = temperature,
            RepetitionPenalty = repeat_penalty,
            MaxLength = maxLength
        )

def LoadModel(ModelName: str, Configuration: dict[str, Any]) -> None:
    __check_service_configuration__()

    if (ModelName in __models__ and __models__[ModelName]["_private_model"] is not None):
        return
    
    loadTime = time.time()
    logs.WriteLog(logs.INFO, "[service_audgen] Loading model...")

    if ("_private_device" not in Configuration):
        Configuration["_private_device"] = "cpu"
    
    if ("dtype" not in Configuration):
        Configuration["dtype"] = "float32"
    
    Configuration["_private_bnb_model_config"] = model_utils.CreateBNBQuantization(Config = Configuration, FromModelConfig = True)

    if (Configuration["_private_type"] == "qwen"):
        model = qwen.LoadModel(Configuration)
    else:
        raise ValueError("Invalid model type.")
    
    __models__[ModelName] = Configuration | {
        "_private_model": model
    }

    loadTime = round(time.time() - loadTime, 3)
    logs.WriteLog(logs.INFO, f"[service_audgen] Model loaded in {loadTime} seconds.")