# Import libraries
import logging
from typing import Any
from collections.abc import Generator
import base64
import json
import copy

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
            pass  # TODO
        
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    __check_service_configuration__()
    conversation = UserParameters["conversation"]

    pass  # TODO

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
        pass  # TODO

    model = {}  # Temporary patch for it to not crash; will be removed. TODO
    __models__[Name] = Configuration | model