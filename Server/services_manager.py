from typing import Any
from collections.abc import Iterator
from io import BytesIO
from pydub import AudioSegment
import os
import copy
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
import messages as conv
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
    "default_service_configuration.json",
    "default_config.json"
]
Configuration: dict[str, Any] = {}

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
        
        for name in SERVICES_CONFIG_FILES:
            fp = os.path.join(pathDir, name)
            logs.WriteLog(logs.INFO, f"[services_manager] Got service configuration file at `{fp}`.")

            if (os.path.exists(fp)):
                pathDefConfig = fp
                break
        
        services.append(Service(
            Name = servDir,
            LoadOnStart = False,
            ServFilePath = pathServFile,
            ReqFilePath = pathReqFile,
            ConfFilePath = pathDefConfig
        ))
    
    return services

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
        conf = copy.deepcopy(D)

        for configParamName, configParamValue in conf.items():
            if (
                configParamName.startswith("_") or
                configParamName.startswith(".") or
                configParamName.startswith("_priv_") or
                configParamName.startswith("_private_")
            ):
                conf.pop(configParamName)
                continue

            if (isinstance(configParamValue, dict)):
                conf[configParamName] = get_private_conf(configParamValue)
                continue
        
        return conf

    global ServicesModels
    return get_private_conf(ServicesModels[FindServiceForModel(ModelName)][ModelName])

def OffloadModels(Names: list[str]) -> None:
    global ServicesModules, ServicesModels
    modelsToOffload = {}

    for modelName, modelConfig in ServicesModels.items():
        if (modelName in Names):
            modelsToOffload[modelConfig["service"]] = modelName
    
    for _, service in ServicesModules.items():
        Service.RunModuleFunction(service.ServiceModule, "SERVICE_OFFLOAD_MODELS", [modelsToOffload])

def InferenceModel(
    ModelName: str,
    Prompt: dict[str, str | list[dict[str, str]] | dict[str, Any]],
    UserParameters: dict[str, Any]
) -> Iterator[dict[str, Any]]:
    global ServicesModules, ServicesModels

    if (
        "key_info" not in UserParameters or
        "conversation_name" not in UserParameters
    ):
        raise ValueError("Required user parameters not defined.")
    
    if (ModelName not in ServicesModels or ModelName not in ServicesModules):
        raise ValueError("Model name not found.")

    modelConfiguration = ServicesModels[ModelName]
    serviceName = modelConfiguration["service"]
    serviceModule = ServicesModules[serviceName]

    if ("max_simul_users" in modelConfiguration and modelConfiguration["max_simul_users"] > 0):
        maxSimulUsers = modelConfiguration["max_simul_users"]
    else:
        logs.WriteLog(logs.INFO, "[services_manager] Max simultaneously users not set in model configuration. Setting to 1.")
        maxSimulUsers = 1

    queueData = queue.GetQueueFor(ModelName)

    if (queueData["users_waiting"] >= maxSimulUsers):
        time.sleep(0.1)

    moduleHandlesConversation = Service.GetModuleVariable(serviceModule.ServiceModule, "MODULE_HANDLES_CONVERSATION")
    moduleHandlesPricing = Service.GetModuleVariable(serviceModule.ServiceModule, "MODULE_HANDLES_PRICING")

    text = Prompt["text"] if ("text" in Prompt) else ""
    files = Prompt["files"] if ("files" in Prompt) else []
    userConfig = Prompt["parameters"] if ("parameters" in Prompt) else {}
    
    # TODO: handle conversation
    if (not moduleHandlesConversation):
        conversation = conv.Conversation.CreateConversationFromDB(f"{UserParameters['key_info']['key']}_{UserParameters['conversation_name']}", True)

    if (not moduleHandlesPricing):
        if ("pricing" in modelConfiguration):
            modelPricing = modelConfiguration["pricing"]

            inferencePrice = modelPricing["inference"] if ("inference" in modelPricing) else 0
            processingTime1secPrice = modelPricing["processing_time"] if ("processing_time" in modelPricing) else 0
            text1mInputPrice = modelPricing["text_input_1m"] if ("text_input_1m" in modelPricing) else 0
            text1mOutputPrice = modelPricing["text_output_1m"] if ("text_output_1m" in modelPricing) else 0
            imagePrice = modelPricing["image"] if ("image" in modelPricing) else 0
            audioPrice = modelPricing["audio"] if ("audio" in modelPricing) else 0
            audio1secPrice = modelPricing["audio_1sec"] if ("audio_1sec" in modelPricing) else 0
            videoPrice = modelPricing["video"] if ("video" in modelPricing) else 0
            video1secPrice = modelPricing["video_1sec"] if ("video_1sec" in modelPricing) else 0
            otherFilesPrice = modelPricing["other_files"] if ("other_files" in modelPricing) else 0

            if (len(text) > 0):
                enc = tiktoken.get_encoding("o200k_base")
                encodedText = enc.encode(text)
            else:
                encodedText = []

            price = inferencePrice
            price += len(encodedText) * text1mInputPrice / 1000000.0

            for file in files:
                if ("type" not in file):
                    continue

                if (file["type"] == "image"):
                    price += imagePrice
                elif (file["type"] == "audio"):
                    price += audioPrice
                    audioBuffer = BytesIO(base64.b64decode(file["data"]))

                    audio = AudioSegment.from_file(audioBuffer)
                    durationInSeconds = len(audio) / 1000

                    price += durationInSeconds * audio1secPrice
                    audioBuffer.close()
                elif (file["type"] == "video"):
                    price += videoPrice
                    videoBuffer = BytesIO(base64.b64decode(file["data"]))

                    try:
                        reader = av.open(videoBuffer)
                        stream = next(s for s in reader.streams if (s.type == "video"))

                        fps = float(stream.average_rate) if (stream.average_rate) else 0
                        numberOfFrames = stream.frames
                        duration = float(reader.duration / av.time_base) if (reader.duration) else (numberOfFrames / fps if (fps) else 0)
                        durationInSeconds = math.floor(duration)

                        price += durationInSeconds * video1secPrice
                        videoBuffer.close()
                    except Exception as ex:
                        videoBuffer.close()
                        raise RuntimeError(f"Could not calculate pricing for video. Reason: {ex}")
                else:
                    price += otherFilesPrice
            
            if (UserParameters["key_info"]["tokens"] < price):
                raise exceptions.NotEnoughTokensException(price, UserParameters["key_info"]["tokens"])
            
            UserParameters["key_info"]["tokens"] -= price
        else:
            logs.PrintLog(logs.WARNING, "[services_manager] Pricing not in model configuration. WILL BE PROVIDED FREE OF CHARGE.")

    processingTime = time.time()
    lastTokenTime = None
    exc = None
    tokensProcessingTime = 0

    try:
        for token in Service.RunModuleFunction(serviceModule.ServiceModule, "SERVICE_INFERENCE", [
            ModelName,
            {
                "text": text,
                "files": files,
                "parameters": userConfig
            },
            UserParameters | {
                "conversation": conversation if (moduleHandlesConversation) else None
            }
        ]):
            outputToken = {
                "response": {
                    "text": token["text"] if ("text" in token) else "",
                    "files": token["files"] if ("files" in token) else []
                },
                "warnings": token["warnings"] if ("warnings" in token) else [],
                "errors": token["errors"] if ("errors" in token) else []
            }

            if (not moduleHandlesPricing):
                tokenPrice = (time.time() - processingTime) * processingTime1secPrice
                processingTime = time.time()

                if (len(outputToken["response"]["text"]) > 0):
                    tokenPrice += text1mOutputPrice / 1000000.0

                if (UserParameters["key_info"]["tokens"] < tokenPrice):
                    raise exceptions.NotEnoughTokensException(tokenPrice, UserParameters["key_info"]["tokens"])
                
                UserParameters["key_info"]["tokens"] -= tokenPrice
            
            if (lastTokenTime is None):
                queue.SetFTS(ModelName, (
                    queueData["fts"] if (queueData["fts"] is not None) else 0 +
                    (time.time() - processingTime)
                ) / 2)
            else:
                tokensProcessingTime = (tokensProcessingTime + (time.time() - lastTokenTime)) / 2
            
            lastTokenTime = time.time()
            yield outputToken
    except Exception as ex:
        exc = ex
    
    queue.SetTPS(ModelName, (
        queueData["tps"] if (queueData["tps"] is not None) else 0 +
        tokensProcessingTime
    ) / 2)

    apiKey = keys_manager.APIKey.FromDict(UserParameters["key_info"])
    apiKey.SaveInDatabase()

    if (exc is not None):
        raise exc