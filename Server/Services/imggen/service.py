# Import libraries
import logging
from typing import Any
from collections.abc import Generator
import base64
import Services.imggen.sdcpp_utils as sdcpp_utils

__models__: dict[str, dict[str, Any]] = {}
ServiceConfiguration: dict[str, Any] | None = None
ServerConfiguration: dict[str, Any] | None = None

def __check_service_configuration__() -> None:
    if (ServiceConfiguration is None):
        raise ValueError("Service configuration is not defined.")
    
    if (ServerConfiguration is None):
        raise ValueError("Server configuration is not defined.")

def SERVICE_LOAD_MODELS(Models: dict[str, dict[str, Any]]) -> None:
    for name, configuration in Models.items():
        LoadModel(name, configuration)

def SERVICE_OFFLOAD_MODELS(Names: list[str]) -> None:
    # Define globals
    global __models__

    # Check configuration
    __check_service_configuration__()
    
    for name in Names:
        # Make sure the model is loaded
        if (__models__[name]["_private_model"] is None):
            continue
        
        logging.info("[service_imggen] Offloading model.")

        # Offload the model
        if (__models__[name]["_private_type"] == "sdcpp"):
            __models__[name]["_private_model"].close()
        
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    __check_service_configuration__()

    conversation = UserParameters["conversation"]
    prompt = None
    nPrompt = ""
    imgs = []

    for msg in conversation:
        if (msg["role"] != "user"):
            continue

        for content in msg["content"]:
            if (content["type"] == "text" and prompt is None):
                prompt = content["text"]
            elif (content["type"] == "text"):
                nPrompt = content["text"]
            elif (content["type"] == "image"):
                imgs.append(base64.b64decode(content["image"]))
    
    if (prompt is None or len(prompt.strip()) == 0):
        raise ValueError("Invalid or empty prompt.")
    
    # Set width and height
    width = int(UserConfig["width"]) if ("width" in UserConfig and UserConfig["width"] is not None) else __models__[Name]["width"] if ("width" in __models__[Name]) else ServiceConfiguration["width"]["default"]
    height = int(UserConfig["height"]) if ("height" in UserConfig and UserConfig["height"] is not None) else __models__[Name]["height"] if ("height" in __models__[Name]) else ServiceConfiguration["height"]["default"]

    if (width < ServiceConfiguration["width"]["min"]):
        width = ServiceConfiguration["width"]["min"]
    elif (width > ServiceConfiguration["width"]["max"]):
        width = ServiceConfiguration["width"]["max"]
    
    if (height < ServiceConfiguration["height"]["min"]):
        height = ServiceConfiguration["height"]["min"]
    elif (height > ServiceConfiguration["height"]["max"]):
        height = ServiceConfiguration["height"]["max"]
    
    # Set CFG scale
    cfgScale = float(UserConfig["cfg_scale"]) if ("cfg_scale" in UserConfig and UserConfig["cfg_scale"] is not None) else __models__[Name]["cfg_scale"] if ("cfg_scale" in __models__[Name]) else ServiceConfiguration["cfg_scale"]["default"]
    imgCfgScale = UserConfig["img_cfg_scale"] if ("img_cfg_scale" in UserConfig) else __models__[Name]["img_cfg_scale"] if ("img_cfg_scale" in __models__[Name]) else ServiceConfiguration["img_cfg_scale"]["default"]

    if (cfgScale < ServiceConfiguration["cfg_scale"]["min"]):
        cfgScale = ServiceConfiguration["cfg_scale"]["min"]
    elif (cfgScale > ServiceConfiguration["cfg_scale"]["max"]):
        cfgScale = ServiceConfiguration["cfg_scale"]["max"]
    
    if (imgCfgScale is not None):
        imgCfgScale = float(imgCfgScale)

        if (imgCfgScale < ServiceConfiguration["img_cfg_scale"]["min"]):
            imgCfgScale = ServiceConfiguration["img_cfg_scale"]["min"]
        elif (imgCfgScale > ServiceConfiguration["img_cfg_scale"]["max"]):
            imgCfgScale = ServiceConfiguration["img_cfg_scale"]["max"]
    
    # Set SLG scale
    slgScale = float(UserConfig["slg_scale"]) if ("slg_scale" in UserConfig) else __models__[Name]["slg_scale"] if ("slg_scale" in __models__[Name]) else ServiceConfiguration["slg_scale"]["default"]

    if (slgScale < ServiceConfiguration["slg_scale"]["min"]):
        slgScale = ServiceConfiguration["slg_scale"]["min"]
    elif (slgScale > ServiceConfiguration["slg_scale"]["max"]):
        slgScale = ServiceConfiguration["slg_scale"]["max"]

    # Set guidance
    guidance = float(UserConfig["guidance"]) if ("guidance" in UserConfig) else __models__[Name]["guidance"] if ("guidance" in __models__[Name]) else ServiceConfiguration["guidance"]["default"]

    if (guidance < ServiceConfiguration["guidance"]["min"]):
        guidance = ServiceConfiguration["guidance"]["min"]
    elif (guidance > ServiceConfiguration["guidance"]["max"]):
        guidance = ServiceConfiguration["guidance"]["max"]
    
    # Set steps
    steps = int(UserConfig["steps"]) if ("steps" in UserConfig) else None

    if (steps is None or steps <= 0):
        steps = __models__[Name]["steps"]["default"] if ("steps" in __models__[Name] and "default" in __models__[Name]["steps"]) else ServiceConfiguration["steps"]["default"]
    
    if ("steps" in __models__[Name] and "max" in __models__[Name]["steps"] and steps > __models__[Name]["steps"]["max"]):
        steps = __models__[Name]["steps"]["max"]
    elif (steps > ServiceConfiguration["steps"]["max"]):
        steps = ServiceConfiguration["steps"]["max"]
    
    # Set ETA
    eta = float(UserConfig["eta"]) if ("eta" in UserConfig) else __models__[Name]["eta"] if ("eta" in __models__[Name]) else ServiceConfiguration["eta"]["default"]

    if (eta < 0):
        eta = 0
    elif (eta > ServiceConfiguration["eta"]["max"]):
        eta = ServiceConfiguration["eta"]["max"]
    
    # Set timestep shift
    timestepShift = int(UserConfig["timestep_shift"]) if ("timestep_shift" in UserConfig) else __models__[Name]["timestep_shift"] if ("timestep_shift" in __models__[Name]) else ServiceConfiguration["timestep_shift"]["default"]

    if (timestepShift < ServiceConfiguration["timestep_shift"]["min"]):
        timestepShift = ServiceConfiguration["timestep_shift"]["min"]
    elif (timestepShift > ServiceConfiguration["timestep_shift"]["max"]):
        timestepShift = ServiceConfiguration["timestep_shift"]["max"]

    # Set seed
    seed = int(UserConfig["seed"]) if ("seed" in UserConfig) else __models__[Name]["seed"] if ("seed" in __models__[Name]) else ServiceConfiguration["seed"]

    # Set upscale factor
    upscaleFactor = int(UserConfig["upscale_factor"]) if ("upscale_factor" in UserConfig) else __models__[Name]["upscale_factor"] if ("upscale_factor" in __models__[Name]) else ServiceConfiguration["upscale_factor"]["default"]

    if (upscaleFactor < 1):
        upscaleFactor = 1
    elif (upscaleFactor > ServiceConfiguration["upscale_factor"]["max"]):
        upscaleFactor = ServiceConfiguration["upscale_factor"]["max"]

    # Set strength
    strength = float(UserConfig["strength"]) if ("strength" in UserConfig) else __models__[Name]["strength"] if ("strength" in __models__[Name]) else ServiceConfiguration["strength"]

    if (strength < 0.1):
        strength = 0.1
    elif (strength > 1):
        strength = 1
    
    # Set canny
    canny = bool(UserConfig["canny"]) if ("canny" in UserConfig) else __models__[Name]["canny"] if ("canny" in __models__[Name]) else False

    # Set sampler
    sampler = str(UserConfig["sampler"]) if ("sampler" in UserConfig and ServiceConfiguration["sampler"]["modified_by_user"]) else __models__[Name]["sampler"] if ("sampler" in __models__[Name]) else ServiceConfiguration["sampler"]["default"]

    # Set scheduler
    scheduler = str(UserConfig["scheduler"]) if ("scheduler" in UserConfig and ServiceConfiguration["scheduler"]["modified_by_user"]) else __models__[Name]["scheduler"] if ("scheduler" in __models__[Name]) else ServiceConfiguration["scheduler"]["default"]

    # Inference model
    if (__models__[Name]["_private_type"] == "sdcpp"):
        result = sdcpp_utils.Inference(
            Model = __models__[Name]["_private_model"],
            Type = "image",
            Prompt = prompt,
            NegativePrompt = nPrompt,
            RefImages = imgs,
            Width = width,
            Height = height,
            CFGScale = cfgScale,
            IMGCFGScale = imgCfgScale,
            SLGScale = slgScale,
            Guidance = guidance,
            Steps = steps,
            ETA = eta,
            TimestepShift = timestepShift,
            Seed = seed,
            UpscaleFactor = upscaleFactor,
            Strength = strength,
            Sampler = sampler,
            Scheduler = scheduler,
            IMG_Canny = canny
        )

    yield {"files": [{"type": "image", "image": base64.b64encode(result).decode("utf-8")}]}

def LoadModel(Name: str, Configuration: dict[str, Any]) -> None:
    # Define globals
    global __models__

    # Make sure the model is not loaded
    if (Name in __models__ and __models__[Name]["_private_model"] is not None):
        return
    
    # Check configuration
    __check_service_configuration__()
    
    logging.info("[service_imggen] Loading model.")

    # Get the model type
    if ("_private_type" in Configuration):
        modelType = Configuration["_private_type"]
    else:
        modelType = None
    
    if (not isinstance(modelType, str) or (modelType != "hf" and modelType != "sdcpp")):
        modelType = None
    
    if (modelType is None):
        raise AttributeError("[service_imggen] Model type is not valid or not defined.")
    
    # Load the model
    if (modelType == "sdcpp"):
        model = sdcpp_utils.LoadSDModel(Configuration)

    __models__[Name] = Configuration | model