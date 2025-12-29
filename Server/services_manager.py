from typing import Any
from collections.abc import Generator
from io import BytesIO
from pydub import AudioSegment
from PIL import Image as PILImage
import os
import copy
import shutil
import time
import types
import importlib.util
import yaml
import json
import base64
import tiktoken
import av
import math
import exceptions
import keys_manager
import services_queue as queue
import Utilities.install_requirements as requirements
import Utilities.logs as logs

SERVICES_DIR = "./Services/"
SERVICES_FILE_NAME = [
    "service.py",
    "serv.py"
]
SERVICES_REQUIREMENTS_FILES = [
    "requirements.py",
    "requirements.txt"
]
SERVICES_CONFIG_FILES = [
    "default_service_configuration.yaml",
    "default_config.yaml",
    #"default_service_configuration.json",
    #"default_config.json"
]
Configuration: dict[str, Any] = {}
TextEncoder = tiktoken.get_encoding("o200k_base")

class Service():
    def __init__(
            self,
            Name: str,
            LoadOnStart: bool | tuple[bool, bool, bool] | list[bool],
            ServFilePath: str,
            ReqFilePath: str | None = None,
            ConfFilePath: str | None = None
        ) -> None:
        self.Name: str = Name

        self.ServiceFilePath: str = ServFilePath
        self.RequirementsFilePath: str | None = ReqFilePath
        self.DefaultConfigurationFilePath: str | None = ConfFilePath

        self.ServiceModuleName: str = Name.strip().replace("/", "_").replace(" ", "_")
        self.RequirementsModuleName: str | None = f"req_{self.ServiceModuleName}" if (ReqFilePath is not None and ReqFilePath.endswith(".py")) else None

        self.ServiceModule: types.ModuleType | None = None
        self.RequirementsModule: types.ModuleType | None = None
        self.Configuration: dict[str, Any] | None = None

        if (isinstance(LoadOnStart, bool)):
            self.LoadModules(LoadOnStart, LoadOnStart, LoadOnStart)
        elif ((isinstance(LoadOnStart, tuple) or isinstance(LoadOnStart, list)) and len(LoadOnStart) == 3):
            self.LoadModules(LoadOnStart[0], LoadOnStart[1], LoadOnStart[2])
        else:
            raise AttributeError("`LoadOnStart` must be bool, tuple[bool, bool, bool], list[bool] (with 3 booleans).")
    
    def LoadModules(self, LoadService: bool = True, LoadRequirements: bool = True, LoadConfiguration: bool = True) -> None:
        if (self.ServiceModule is None and LoadService):
            logs.WriteLog(logs.INFO, f"[services_manager] Loading service module for `{self.Name}`.")

            spec = importlib.util.spec_from_file_location(
                self.ServiceModuleName,
                self.ServiceFilePath
            )
            self.ServiceModule = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.ServiceModule)

        if (self.RequirementsModule is None and self.RequirementsModuleName is not None and LoadRequirements):
            logs.WriteLog(logs.INFO, f"[services_manager] Loading requirements module for `{self.Name}`.")

            reqSpec = importlib.util.spec_from_file_location(
                self.RequirementsModuleName,
                self.RequirementsFilePath
            )
            self.RequirementsModule = importlib.util.module_from_spec(reqSpec)
            reqSpec.loader.exec_module(self.RequirementsModule)
        
        if (self.Configuration is None and self.DefaultConfigurationFilePath is not None and LoadConfiguration):
            logs.WriteLog(logs.INFO, f"[services_manager] Loading service configuration for `{self.Name}`.")

            with open(self.DefaultConfigurationFilePath, "r", encoding = "utf-8") as configFile:
                if (self.DefaultConfigurationFilePath.endswith(".yaml")):
                    self.Configuration = yaml.safe_load(configFile)
                elif (self.DefaultConfigurationFilePath.endswith(".json")):
                    self.Configuration = json.loads(configFile.read())
                else:
                    raise TypeError("Invalid configuration file type. Must be YAML or JSON.")
            
            if (self.ServiceModule is not None):
                self.SetModuleVariable(self.ServiceModule, "ServiceConfiguration", self.Configuration, True)
                self.SetModuleVariable(self.ServiceModule, "ServerConfiguration", copy.deepcopy(Configuration), True)
    
    def UnloadModules(self, UnloadService: bool = True, UnloadRequirements: bool = True, UnloadConfiguration: bool = True) -> None:
        if (self.ServiceModule is not None and UnloadService):
            del self.ServiceModule
            self.ServiceModule = None
        
        if (self.RequirementsModule is not None and UnloadRequirements):
            del self.RequirementsModule
            self.RequirementsModule = None
        
        if (self.Configuration is not None and UnloadConfiguration):
            self.Configuration.clear()
            self.Configuration = None
    
    def HasModel(self, ModelName: str) -> bool:
        global ServicesModels
        return ModelName in ServicesModels[self.Name]
    
    @staticmethod
    def ModuleContainsFunction(Module: types.ModuleType, FunctionName: str) -> bool:
        return hasattr(Module, FunctionName) and callable(getattr(Module, FunctionName))
    
    @staticmethod
    def ModuleContainsVariable(Module: types.ModuleType, VariableName: str) -> bool:
        return hasattr(Module, VariableName) and not callable(getattr(Module, VariableName))
    
    @staticmethod
    def RunModuleFunction(Module: types.ModuleType, FunctionName: str, Args: list[Any] = [], Kwargs: dict[str, Any] = {}) -> Any:
        if (Service.ModuleContainsFunction(Module, FunctionName)):
            func = getattr(Module, FunctionName)
            return func(*Args, **Kwargs)
        
        raise TypeError("Not a function or doesn't exists.")
    
    @staticmethod
    def GetModuleVariable(Module: types.ModuleType, VarName: str, Default: Any | ValueError = ValueError) -> Any:
        if (Service.ModuleContainsVariable(Module, VarName)):
            return getattr(Module, VarName)
        
        if (Default is ValueError):
            raise ValueError("Not a variable or doesn't exists.")
        
        return Default
    
    @staticmethod
    def SetModuleVariable(Module: types.ModuleType, VarName: str, Value: Any, CreateIfNotExists: bool = True) -> None:
        if (Service.ModuleContainsVariable(Module, VarName) or CreateIfNotExists):
            return setattr(Module, VarName, Value)
        
        raise TypeError("Not a variable or doesn't exists.")

ServicesModules: dict[str, Service] = {}  # {"service name": service class}
ServicesModels: dict[str, dict[str, dict[str, Any]]] = {}  # {"service name": {"model name": model config}}

def __delete_modules_and_info__() -> None:
    global ServicesModules, ServicesModels

    if (ServicesModules is not None):
        for _, service in ServicesModules.items():
            service.UnloadModules(True, True, True)
        
        ServicesModules.clear()
    
    if (ServicesModels is not None):
        ServicesModels.clear()

def __load_modules_and_info__(Models: dict[str, dict[str, Any]]) -> None:
    global ServicesModules, ServicesModels

    for modelName, modelConfig in Models.items():
        if ("service" not in modelConfig):
            raise RuntimeError(f"Model service not defined (`{modelName}`).")
        
        service = None

        for serv in GetServices():
            if (modelConfig["service"] == serv.Name):
                service = serv
        
        if (service is None):
            raise RuntimeError(f"Invalid service for the model `{modelName}`.")
        
        if (modelConfig["service"] not in ServicesModules):
            service.LoadModules(True, False, True)

            if (
                not Service.ModuleContainsFunction(service.ServiceModule, "SERVICE_LOAD_MODELS") or
                not Service.ModuleContainsFunction(service.ServiceModule, "SERVICE_OFFLOAD_MODELS") or
                not Service.ModuleContainsFunction(service.ServiceModule, "SERVICE_INFERENCE")
            ):
                raise RuntimeError(f"Service module does not contains the required functions (`{service.Name}`).")
            
            ServicesModules[modelConfig["service"]] = service
        
        if (modelConfig["service"] not in ServicesModels):
            ServicesModels[modelConfig["service"]] = {}

        ServicesModels[modelConfig["service"]][modelName] = modelConfig

def GetServices() -> list[Service]:
    global ServicesModules

    if (len(ServicesModules) > 0):
        return list(ServicesModules.values())

    services = []
    inputServDir = os.listdir(SERVICES_DIR)

    logs.WriteLog(logs.INFO, f"[services_manager] Fetched services: `{inputServDir}`.")

    for servDir in os.listdir(SERVICES_DIR):
        logs.WriteLog(logs.INFO, f"[services_manager] Getting service information of the directory `{servDir}`.")

        if (" " in servDir):
            raise RuntimeError("Service directory must not contain spaces.")

        pathDir = os.path.join(SERVICES_DIR, servDir)
        pathServFile = None
        pathReqFile = None
        pathDefConfig = None

        if (not os.path.isdir(pathDir)):
            raise FileNotFoundError(f"`{pathDir}` is not a directory.")
        
        for name in SERVICES_FILE_NAME:
            fp = os.path.join(pathDir, name)
            logs.WriteLog(logs.INFO, f"[services_manager] Got service file at `{fp}`.")

            if (os.path.exists(fp)):
                pathServFile = fp
                break
        
        for name in SERVICES_REQUIREMENTS_FILES:
            fp = os.path.join(pathDir, name)
            logs.WriteLog(logs.INFO, f"[services_manager] Got requirements file at `{fp}`.")

            if (os.path.exists(fp)):
                pathReqFile = fp
                break
        
        if (os.path.exists(f"./config_{servDir}.yaml")):
            pathDefConfig = f"./config_{servDir}.yaml"
            logs.WriteLog(logs.INFO, f"[services_manager] Got service configuration file at `{fp}`. No need to copy.")
        else:
            for name in SERVICES_CONFIG_FILES:
                fp = os.path.join(pathDir, name)
                logs.WriteLog(logs.INFO, f"[services_manager] Got service configuration file at `{fp}`. Copying.")

                if (os.path.exists(fp)):
                    shutil.copy2(fp, f"./config_{servDir}.yaml")
                    pathDefConfig = f"./config_{servDir}.yaml"

                    break
        
        services.append(Service(
            Name = servDir,
            LoadOnStart = False,
            ServFilePath = pathServFile,
            ReqFilePath = pathReqFile,
            ConfFilePath = pathDefConfig
        ))
    
    return services

def IsServiceInstalled(Name: str) -> bool:
    for service in GetServices():
        if (service.Name == Name):
            return True
        
    return False

def InstallAllRequirements(Services: list[Service] | None = None) -> None:
    if (Services is None):
        Services = GetServices()
    
    for service in Services:
        if (service.RequirementsFilePath is None):
            logs.PrintLog(logs.INFO, f"[services_manager] No requirements for the service `{service.Name}`. Ignoring.")
            continue

        if (service.RequirementsFilePath is not None and service.RequirementsModuleName is None):
            with open(service.RequirementsFilePath, "r") as f:
                reqs = f.read()
            
            logs.PrintLog(logs.INFO, f"[services_manager] Installing requirements for the service `{service.Name}` (using requirements file)...")
            requirements.InstallPackage(reqs.splitlines())
            logs.PrintLog(logs.INFO, f"[services_manager] Requirements for the service `{service.Name}` installed!")
        else:
            logs.PrintLog(logs.INFO, f"[services_manager] Installing requirements for the service `{service.Name}` (using module)...")
            service.LoadModules(False, True, False)

            if (Service.ModuleContainsFunction(service.RequirementsModule, "Install")):
                Service.RunModuleFunction(service.RequirementsModule, "Install", [None])
                logs.PrintLog(logs.INFO, f"[services_manager] Requirements for the service `{service.Name}` installed!")
            else:
                logs.PrintLog(
                    logs.ERROR,
                    f"[services_manager] Could not install requirements for the service `{service.Name}`. Possibly no `Install` function."
                )

def LoadModels(Models: dict[str, dict[str, Any]]) -> None:
    global ServicesModules, ServicesModels
    __load_modules_and_info__(Models)
    
    for serviceName, service in ServicesModules.items():
        Service.RunModuleFunction(service.ServiceModule, "SERVICE_LOAD_MODELS", [ServicesModels[serviceName]])

def FindServiceForModel(ModelName: str, ReturnServiceName: bool = False) -> Service | str:
    global ServicesModules

    for _, servModule in ServicesModules.items():
        if (servModule.HasModel(ModelName)):
            return servModule.Name if (ReturnServiceName) else servModule
    
    raise RuntimeError("Could not find model in service.")

def GetModelConfiguration(ModelName: str) -> dict[str, Any]:
    def get_private_conf(D: dict[str, Any]) -> dict[str, Any]:
        conf = {}

        for configParamName, configParamValue in D.items():
            if (
                configParamName.startswith("_") or
                configParamName.startswith(".") or
                configParamName.startswith("_priv_") or
                configParamName.startswith("_private_")
            ):
                continue

            if (isinstance(configParamValue, dict)):
                conf[configParamName] = get_private_conf(configParamValue)
                continue

            conf[configParamName] = D[configParamName]
        
        return copy.deepcopy(conf)

    global ServicesModels
    return get_private_conf(ServicesModels[FindServiceForModel(ModelName, True)][ModelName])

def OffloadModels(Names: list[str]) -> None:
    global ServicesModules, ServicesModels
    modelsToOffload = {}

    for modelName, modelConfig in ServicesModels.items():
        if (modelName in Names):
            modelsToOffload[modelConfig["service"]] = modelName
    
    for _, service in ServicesModules.items():
        Service.RunModuleFunction(service.ServiceModule, "SERVICE_OFFLOAD_MODELS", [modelsToOffload])

def CalculateTokenPrice(ModelNameOrConfig: str | dict[str, Any], GetOutputPricing: bool, MessageContent: list[dict[str, str]]) -> float:
    if (isinstance(ModelNameOrConfig, str)):
        serviceName = FindServiceForModel(ModelNameOrConfig, True)
        modelConfiguration = ServicesModels[serviceName][ModelNameOrConfig]
    else:
        modelConfiguration = ModelNameOrConfig
    
    price = 0

    if ("pricing" in modelConfiguration):
        modelPricing = modelConfiguration["pricing"]
    else:
        logs.WriteLog(logs.WARNING, "[services_manager] Pricing not set. Everything will default to 0 (free of charge).")
        modelPricing = {}

    if (GetOutputPricing):
        textPrice = modelPricing["text_output"] if ("text_output" in modelPricing) else 0
        imagePrice = modelPricing["image_output"] if ("image_output" in modelPricing) else 0
        audioPrice = modelPricing["audio_output"] if ("audio_output" in modelPricing) else 0
        videoPriceS = modelPricing["video_output_s"] if ("video_output_s" in modelPricing) else 0
        videoPriceR = modelPricing["video_output_r"] if ("video_output_r" in modelPricing) else 0
        otherPrice = modelPricing["other_output"] if ("other_output" in modelPricing) else 0
    else:
        textPrice = modelPricing["text_input"] if ("text_output" in modelPricing) else 0
        imagePrice = modelPricing["image_input"] if ("image_output" in modelPricing) else 0
        audioPrice = modelPricing["audio_input"] if ("audio_output" in modelPricing) else 0
        videoPriceS = modelPricing["video_input_s"] if ("video_output_s" in modelPricing) else 0
        videoPriceR = modelPricing["video_input_r"] if ("video_output_r" in modelPricing) else 0
        otherPrice = modelPricing["other_input"] if ("other_output" in modelPricing) else 0
    
    for content in MessageContent:
        if (len(content[content["type"]]) == 0):
            continue

        if (content["type"] == "text"):
            price += len(TextEncoder.encode(content["text"])) * textPrice / 1000000.0
        elif (content["type"] == "image"):
            imgBuffer = BytesIO(base64.b64decode(content["image"]))
            img = PILImage.open(imgBuffer)
            price += (img.size[0] / 1024) * (img.size[1] / 1024) * imagePrice

            img.close()
            imgBuffer.close()
        elif (content["type"] == "audio"):
            audioBuffer = BytesIO(base64.b64decode(content["audio"]))

            audio = AudioSegment.from_file(audioBuffer)
            durationInSeconds = len(audio) / 1000

            price += durationInSeconds * audioPrice
            audioBuffer.close()
        elif (content["type"] == "video"):
            videoBuffer = BytesIO(base64.b64decode(content["video"]))

            try:
                reader = av.open(videoBuffer)
                stream = next(s for s in reader.streams if (s.type == "video"))

                fps = float(stream.average_rate) if (stream.average_rate) else 0
                numberOfFrames = stream.frames
                duration = float(reader.duration / av.time_base) if (reader.duration) else (numberOfFrames / fps if (fps) else 0)
                durationInSeconds = math.floor(duration)

                width = stream.width
                height = stream.height

                price += (durationInSeconds * videoPriceS) + ((width / 1024) * (height / 1024) * videoPriceR)

                reader.close()
                videoBuffer.close()
            except Exception as ex:
                videoBuffer.close()
                raise RuntimeError(f"Could not calculate pricing for video. Reason: {ex}")
        elif (isinstance(otherPrice, float) or isinstance(otherPrice, int)):
            price += len(content[content["type"]]) / 1048576 * otherPrice
        elif (isinstance(otherPrice, dict)):
            if (content["type"] in otherPrice):
                price += len(content[content["type"]]) / 1048576 * otherPrice[content["type"]]
            else:
                price += len(content[content["type"]]) / 1048576 * otherPrice["global"]
        else:
            raise ValueError("Invalid content type or pricing.")
    
    return price

def InferenceModel(
    ModelName: str,
    Prompt: dict[str, str | list[dict[str, str]] | dict[str, Any]],
    UserParameters: dict[str, Any]
) -> Generator[dict[str, Any]]:
    global ServicesModules, ServicesModels, TextEncoder

    if (
        "key_info" not in UserParameters
    ):
        raise ValueError("Required user parameters not defined.")
    
    serviceName = FindServiceForModel(ModelName, True)
    
    if (ModelName not in ServicesModels[serviceName]):
        raise ValueError("Model name not found.")

    modelConfiguration = ServicesModels[serviceName][ModelName]
    serviceModule = ServicesModules[serviceName]

    if ("max_simul_users" in modelConfiguration and modelConfiguration["max_simul_users"] > 0):
        maxSimulUsers = modelConfiguration["max_simul_users"]
    else:
        logs.WriteLog(logs.INFO, "[services_manager] Max simultaneously users not set in model configuration. Setting to 1.")
        maxSimulUsers = 1

    modelQueue = queue.GetQueueForModel(ModelName)

    if (modelQueue is None):
        modelQueue = queue.Queue(ModelName = ModelName, MaxSimultaneousUsers = maxSimulUsers)
        queue.Queues.append(modelQueue)

    queueUID = modelQueue.CreateNewWaitingID(Prioritize = ModelName in UserParameters["key_info"]["PrioritizeModels"])
    modelQueue.WaitForProcessing(queueUID)

    # TODO: Automatic blacklist

    conversation = Prompt["conversation"] if ("conversation" in Prompt) else []
    userConfig = Prompt["parameters"] if ("parameters" in Prompt) else {}
    price = 0

    for msg in conversation:
        if (isinstance(msg["content"], str)):
            msg["content"] = [{"type": "text", "text": msg["content"]}]
        
        price += CalculateTokenPrice(modelConfiguration, False, msg["content"])

    if (UserParameters["key_info"]["Tokens"] < price):
        raise exceptions.NotEnoughTokensException(price, UserParameters["key_info"]["Tokens"])
        
    UserParameters["key_info"]["Tokens"] -= price

    firstToken = True
    lastTokenTime = time.time()
    exc = None
    tokensProcessingTime = None

    try:
        for token in Service.RunModuleFunction(serviceModule.ServiceModule, "SERVICE_INFERENCE", [
            ModelName,
            userConfig,
            UserParameters | {
                "conversation": conversation
            }
        ]):
            outputToken = {
                "response": {
                    "text": token["text"] if ("text" in token) else "",
                    "files": token["files"] if ("files" in token) else []
                } | (token["extra"] if ("extra" in token) else {}),
                "warnings": token["warnings"] if ("warnings" in token) else [],
                "errors": token["errors"] if ("errors" in token) else [],
                "_queue_uid": queueUID
            }
            tokenPrice = CalculateTokenPrice(modelConfiguration, True, [
                {
                    "type": "text",
                    "text": outputToken["response"]["text"]
                }
            ] + outputToken["response"]["files"])

            if (UserParameters["key_info"]["Tokens"] < tokenPrice):
                raise exceptions.NotEnoughTokensException(tokenPrice, UserParameters["key_info"]["Tokens"])
            
            UserParameters["key_info"]["Tokens"] -= tokenPrice
            
            if (firstToken):
                firstTokenSeconds = time.time() - lastTokenTime

                if (modelQueue.FirstTokenSeconds is not None):
                    firstTokenSeconds = (modelQueue.FirstTokenSeconds + firstTokenSeconds) / 2

                modelQueue.FirstTokenSeconds = round(firstTokenSeconds, 3)
                firstToken = False
            else:
                if (tokensProcessingTime is None):
                    tokensProcessingTime = time.time() - lastTokenTime
                
                tokensProcessingTime = (tokensProcessingTime + (time.time() - lastTokenTime)) / 2
            
            lastTokenTime = time.time()
            yield outputToken

        yield {
            "conversation_result": conversation,
            "_queue_uid": queueUID
        }
    except Exception as ex:
        exc = ex
    finally:
        if (tokensProcessingTime is not None):
            if (modelQueue.TokensPerSecond is not None):
                tokensProcessingTime = (1 / modelQueue.TokensPerSecond + tokensProcessingTime) / 2
            
            modelQueue.TokensPerSecond = round(1 / tokensProcessingTime, 3)
        
        modelQueue.DeleteUID(queueUID)

        apiKey = keys_manager.APIKey.__from_dict__(UserParameters["key_info"])
        apiKey.SaveToFile()

        if (exc is not None):
            raise exc