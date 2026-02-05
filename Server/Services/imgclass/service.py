from typing import Any
from collections.abc import Generator
from io import BytesIO
from PIL import Image
import time
import json
import base64
import Services.imgclass.hf as hf
import Utilities.model_utils as model_utils
import Utilities.logs as logs

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
        
        logs.WriteLog(logs.INFO, "[service_imgclass] Offloading model.")
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    LoadModel(Name, ServerConfiguration["services"][Name])
    imgs = []

    for message in UserParameters["conversation"]:
        for content in message["content"]:
            if (content["type"] != "image"):
                continue

            buffer = BytesIO(base64.b64decode(content["image"]))
            img = Image.open(buffer)

            imgs.append([buffer, img])
    
    if (len(imgs) == 0):
        return

    if (__models__[Name]["_private_type"] == "hf"):
        gen = hf.InferenceModel(
            Images = [i[1] for i in imgs],
            Model = __models__[Name]["_private_model"],
            Device = __models__[Name]["_private_device"],
            DType = __models__[Name]["dtype"]
        )
    
    for token in gen:
        yield {"text": json.dumps(token), "extra": token}

    for img in imgs:
        img[1].close()
        img[0].close()
    
    imgs.clear()

def LoadModel(ModelName: str, Configuration: dict[str, Any]) -> None:
    __check_service_configuration__()

    if (ModelName in __models__ and __models__[ModelName]["_private_model"] is not None):
        return
    
    loadTime = time.time()
    logs.WriteLog(logs.INFO, "[service_imgclass] Loading model...")

    if ("_private_device" not in Configuration):
        Configuration["_private_device"] = "cpu"
    
    if ("dtype" not in Configuration):
        Configuration["dtype"] = "float32"

    Configuration["_private_bnb_model_config"] = model_utils.CreateBNBQuantization(Config = Configuration, FromModelConfig = True)

    if (Configuration["_private_type"] == "hf"):
        model = hf.LoadModel(Configuration)
    else:
        raise ValueError("Invalid model type.")
    
    __models__[ModelName] = Configuration | {
        "_private_model": model
    }

    loadTime = round(time.time() - loadTime, 3)
    logs.WriteLog(logs.INFO, f"[service_imgclass] Model loaded in {loadTime} seconds.")

    if ("_private_test_inference" in Configuration and Configuration["_private_test_inference"]):
        logs.WriteLog(logs.INFO, "[service_imgclass] Testing inference of the model.")
        files = []

        if ("test_inference_images" in ServiceConfiguration):
            for file in ServiceConfiguration["test_inference_images"]:
                with open(file, "rb") as f:
                    files.append(base64.b64encode(f.read()).decode("utf-8"))
        else:
            logs.WriteLog(logs.INFO, "[service_imgclass] Inference test files not specified.")
        
        response = SERVICE_INFERENCE(
            ModelName,
            {},
            {
                "conversation": [{"role": "user", "content": [{"type": "image", "image": f} for f in files]}]
            }
        )
        testInferenceResponse = "["

        for token in response:
            testInferenceResponse += token["text"] + ", "
        
        if (len(testInferenceResponse) > 1):
            testInferenceResponse = testInferenceResponse[:-2]

        testInferenceResponse += "]"
        logs.WriteLog(logs.INFO, f"[service_imgclass] Test inference response for model `{ModelName}`:\n```json\n{testInferenceResponse}\n```")