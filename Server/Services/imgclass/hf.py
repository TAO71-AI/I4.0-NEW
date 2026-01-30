from typing import Any
from collections.abc import Generator
from PIL.Image import Image
from transformers import AutoModelForImageClassification, ViTImageProcessor
import torch
import torch.nn.functional as tnnf
import Server.Utilities.model_utils as model_utils

def LoadModel(Configuration: dict[str, Any]) -> list[AutoModelForImageClassification | ViTImageProcessor]:
    if ("_private_device" not in Configuration):
        Configuration["_private_device"] = "cpu"
    
    if ("dtype" not in Configuration):
        Configuration["dtype"] = "float32"
    
    Configuration["_private_bnb_model_config"] = model_utils.CreateBNBQuantization(Config = Configuration, FromModelConfig = True)
    model = AutoModelForImageClassification.from_pretrained(
        pretrained_model_name_or_path = Configuration["_private_model_path"],
        device_map = Configuration["_private_device"],
        dtype = model_utils.StringToDType(Configuration["dtype"]),
        quantization_config = Configuration["_private_bnb_model_config"],
        attn_implementation = model_utils.GetAttnImpl(Configuration)
    ),
    tokenizer = ViTImageProcessor.from_pretrained(
        pretrained_model_name_or_path = Configuration["_private_model_path"]
    )

    return [model, tokenizer]

def InferenceModel(
    Images: list[Image],
    Model: list[AutoModelForImageClassification | ViTImageProcessor],
    Device: str,
    DType: str
) -> Generator[dict[str, Any]]:
    for image in Images:
        with torch.no_grad():
            inputs = Model[1](
                images = image,
                return_tensors = "pt"
            ).to(device = Device, dtype = model_utils.StringToDType(DType))
            outputs = Model[0](**inputs)
            logits = outputs.logits
        
        probabilities = tnnf.softmax(logits, dim = -1)
        predictedID = logits.argmax(-1).item()

        confidence = probabilities[0, predictedID].item()
        predictedLabel = Model[0].config.id2label[predictedID]

        yield {"confidence": confidence, "label": predictedLabel}