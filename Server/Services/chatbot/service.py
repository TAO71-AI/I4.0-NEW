# Import libraries
from typing import Any
from collections.abc import Generator
import base64
import json
import copy
import Services.chatbot.llama_utils as utils_llama
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
    """
    Load all the chatbot models.

    Args:
        Models (dict[str, dict[str, Any]]): All the models to load.
    
    Returns:
        None
    """
    for name, configuration in Models.items():
        LoadModel(name, configuration)

def SERVICE_OFFLOAD_MODELS(Names: list[str]) -> None:
    """
    Offload all the defined chatbot models.

    Args:
        Names (list[str]): Names of the models to offload.
    
    Returns:
        None
    """
    # Define globals
    global __models__

    # Check configuration
    __check_service_configuration__()
    
    for name in Names:
        # Make sure the model is loaded
        if (__models__[name]["_private_model"] is None):
            continue
        
        logs.WriteLog(logs.INFO, "[service_chatbot] Offloading model.")

        # Offload the model
        if (__models__[name]["_private_type"] == "lcpp"):
            if (isinstance(__models__[name]["_private_model"].chat_handler, utils_llama.CH_Llava15)):
                __models__[name]["_private_model"].chat_handler._mtmd_cpp.mtmd_free(__models__[name]["_private_model"].chat_handler.mtmd_ctx)
                __models__[name]["_private_model"].chat_handler = None
            
            __models__[name]["_private_model"].close()
        
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    """
    Inference the chatbot model.

    Args:
        Name (str): Name of the model.
        UserConfig (dict[str, Any]): Configuration of the user.
        UserParameters (dict[str, Any]): Parameters of the user ("key_info", "conversation").
    """
    __check_service_configuration__()

    conversation = UserParameters["conversation"]
    tools = []

    if ("temperature" in UserConfig and ServiceConfiguration["temperature"]["modified_by_user"]):
        temperature = UserConfig["temperature"]
    elif ("temperature" in __models__[Name]):
        temperature = __models__[Name]["temperature"]
    else:
        temperature = ServiceConfiguration["temperature"]["default"]
    
    if ("top_p" in UserConfig and ServiceConfiguration["top_p"]["modified_by_user"]):
        topP = UserConfig["top_p"]
    elif ("top_p" in __models__[Name]):
        topP = __models__[Name]["top_p"]
    else:
        topP = ServiceConfiguration["top_p"]["default"]
    
    if ("top_k" in UserConfig and ServiceConfiguration["top_k"]["modified_by_user"]):
        topK = UserConfig["top_k"]
    elif ("top_k" in __models__[Name]):
        topK = __models__[Name]["top_k"]
    else:
        topK = ServiceConfiguration["top_k"]["default"]
    
    if ("min_p" in UserConfig and ServiceConfiguration["min_p"]["modified_by_user"]):
        minP = UserConfig["min_p"]
    elif ("min_p" in __models__[Name]):
        minP = __models__[Name]["min_p"]
    else:
        minP = ServiceConfiguration["min_p"]["default"]
    
    if ("typical_p" in UserConfig and ServiceConfiguration["typical_p"]["modified_by_user"]):
        typicalP = UserConfig["typical_p"]
    elif ("typical_p" in __models__[Name]):
        typicalP = __models__[Name]["typical_p"]
    else:
        typicalP = ServiceConfiguration["typical_p"]["default"]
    
    if ("seed" in UserConfig and ServiceConfiguration["seed"]["modified_by_user"]):
        seed = UserConfig["seed"]
    elif ("seed" in __models__[Name]):
        seed = __models__[Name]["seed"]
    else:
        seed = ServiceConfiguration["seed"]["default"]
    
    if ("presence_penalty" in UserConfig and ServiceConfiguration["presence_penalty"]["modified_by_user"]):
        presencePenalty = UserConfig["presence_penalty"]
    elif ("presence_penalty" in __models__[Name]):
        presencePenalty = __models__[Name]["presence_penalty"]
    else:
        presencePenalty = ServiceConfiguration["presence_penalty"]["default"]
    
    if ("frequency_penalty" in UserConfig and ServiceConfiguration["frequency_penalty"]["modified_by_user"]):
        frequencyPenalty = UserConfig["frequency_penalty"]
    elif ("frequency_penalty" in __models__[Name]):
        frequencyPenalty = __models__[Name]["frequency_penalty"]
    else:
        frequencyPenalty = ServiceConfiguration["frequency_penalty"]["default"]
    
    if ("repeat_penalty" in UserConfig and ServiceConfiguration["repeat_penalty"]["modified_by_user"]):
        repeatPenalty = UserConfig["repeat_penalty"]
    elif ("repeat_penalty" in __models__[Name]):
        repeatPenalty = __models__[Name]["repeat_penalty"]
    else:
        repeatPenalty = ServiceConfiguration["repeat_penalty"]["default"]

    if ("tools" in UserConfig and ServiceConfiguration["tools"]["modified_by_user"]):
        tools = UserConfig["tools"]
    elif ("tools" in __models__[Name]):
        tools = __models__[Name]["tools"]
    else:
        tools = ServiceConfiguration["tools"]["default"]
    
    if ("tool_choice" in UserConfig and ServiceConfiguration["tool_choice"]["modified_by_user"]):
        toolChoice = UserConfig["tool_choice"]
    elif ("tool_choice" in __models__[Name]):
        toolChoice = __models__[Name]["tool_choice"]
    else:
        toolChoice = ServiceConfiguration["tool_choice"]["default"]
    
    if ("max_length" in UserConfig and ServiceConfiguration["max_length"]["modified_by_user"]):
        maxLength = UserConfig["max_length"]
    elif ("max_length" in __models__[Name]):
        maxLength = __models__[Name]["max_length"]
    else:
        maxLength = ServiceConfiguration["max_length"]["default"]
    
    if (maxLength > ServiceConfiguration["max_length"]["default"] and not ServiceConfiguration["max_length"]["allow_greater_than_default"]):
        maxLength = ServiceConfiguration["max_length"]["default"]
    
    if ("stop_tokens" in UserConfig):
        stopTokens = UserConfig["stop_tokens"] if (isinstance(UserConfig["stop_tokens"], list)) else [str(UserConfig["stop_tokens"])]
    
    if ("_private_extra_parameters" in __models__[Name]):
        extraParameters = __models__[Name]["_private_extra_parameters"]
    else:
        extraParameters = {}
    
    generator = InferenceModel(
        Name,
        conversation,
        {
            "temperature": temperature,
            "top_p": topP,
            "top_k": topK,
            "min_p": minP,
            "typical_p": typicalP,
            "seed": seed,
            "presence_penalty": presencePenalty,
            "frequency_penalty": frequencyPenalty,
            "repeat_penalty": repeatPenalty,
            "tools": tools,
            "tool_choice": toolChoice,
            "max_length": maxLength,
            "stop": stopTokens,
            "extra_parameters": extraParameters
        }
    )

    for token in generator:
        yield token

def InferenceModel(Name: str, Conversation: list[dict[str, str | list[dict[str, str]]]], Configuration: dict[str, Any]) -> Generator[dict[str, Any]]:
    """
    Inference the model.

    Args:
        Name (str): Name of the model.
        Conversation (list[dict[str, str | list[dict[str, str]]]]): Conversation of the model.
        Configuration (dict[str, Any]): Configuration of the model.
    """
    LoadModel(Name, __models__[Name])

    conversation = copy.deepcopy(Conversation)
    modelConversation = []
    
    for message in conversation:
        if (message["role"] == "system"):
            content = ""

            for cont in message["content"]:
                if (cont["type"] != "text"):
                    raise TypeError("Invalid content type for system prompt. Only text allowed.")
                    
                content += cont["text"]

            message["content"] = content

        if (isinstance(message["content"], list)):
            for content in message["content"]:
                if (content["type"] not in __models__[Name]["multimodal"]):
                    yield {"warnings": [f"Content type '{content['type']}' not supported by this model, this will be ignored."]}
                    continue

                if (__models__[Name]["_private_type"] == "lcpp"):
                    if (content["type"] == "image"):
                        content["image_url"] = {"url": f"data:image;base64,{content['image']}"}

                        content["type"] = "image_url"
                        content.pop("image")
                    # TODO: Add video and audio when supported

        modelConversation.append(message)

    if (__models__[Name]["_private_type"] == "lcpp"):
        model: utils_llama.Llama = __models__[Name]["_private_model"]
        response = model.create_chat_completion(
            messages = modelConversation,
            tools = Configuration["tools"],
            tool_choice = Configuration["tool_choice"],
            temperature = Configuration["temperature"],
            top_p = Configuration["top_p"],
            top_k = Configuration["top_k"],
            min_p = Configuration["min_p"],
            typical_p = Configuration["typical_p"],
            stream = True,
            seed = Configuration["seed"],
            max_tokens = Configuration["max_length"],
            presence_penalty = Configuration["presence_penalty"],
            frequency_penalty = Configuration["frequency_penalty"],
            repeat_penalty = Configuration["repeat_penalty"],
            stop = Configuration["stop"],
            **Configuration["extra_parameters"]
        )
        tools = []
        currentToolIdx = None

        if ("tool_start_token" in __models__[Name]):
            toolStartToken = __models__[Name]["tool_start_token"]
        elif ("tool_start_token" in ServiceConfiguration):
            toolStartToken = ServiceConfiguration["tool_start_token"]
        else:
            toolStartToken = "<tool_call>"
        
        if ("tool_end_token" in __models__[Name]):
            toolEndToken = __models__[Name]["tool_end_token"]
        elif ("tool_end_token" in ServiceConfiguration):
            toolEndToken = ServiceConfiguration["tool_end_token"]
        else:
            toolEndToken = "</tool_call>"
        
        logs.WriteLog(logs.INFO, "[service_chatbot] Inferencing chatbot model.")
        fullAssistantText = ""

        for token in response:
            if (
                not "choices" in token or
                len(token["choices"]) == 0 or
                not "delta" in token["choices"][0] or
                not "content" in token["choices"][0]["delta"]
            ):
                continue

            tokenText = token["choices"][0]["delta"]["content"]
            fullAssistantText += tokenText

            if (toolEndToken in tokenText and currentToolIdx is not None):
                tools[currentToolIdx] += tokenText[:tokenText.index(toolEndToken)]
                currentToolIdx = None

            if (toolStartToken in tokenText and currentToolIdx is None):
                currentToolIdx = len(tools)
                tools.append(tokenText[tokenText.index(toolStartToken) + len(toolStartToken):])
            elif (currentToolIdx is not None):
                tools[currentToolIdx] += tokenText
            
            yield {"text": tokenText}
        
        yield {"extra": {"tools": [json.loads(tool) for tool in tools]}}
        logs.WriteLog(logs.INFO, "[service_chatbot] Finished inference.")

def LoadModel(Name: str, Configuration: dict[str, Any]) -> None:
    """
    Load a chatbot model.

    Args:
        Name (str): Name of the model.
        Configuration (dict[str, Any]): Configuration of the model.
    
    Returns:
        None
    """
    # Define globals
    global __models__

    # Make sure the model is not loaded
    if (Name in __models__ and __models__[Name]["_private_model"] is not None):
        return
    
    # Check configuration
    __check_service_configuration__()
    
    logs.WriteLog(logs.INFO, "[service_chatbot] Loading model.")

    # Get the model type
    if ("_private_type" in Configuration):
        modelType = Configuration["_private_type"]
    else:
        modelType = None
    
    if (not isinstance(modelType, str) or (modelType != "hf" and modelType != "lcpp")):
        modelType = None
    
    if (modelType is None):
        raise AttributeError("[service_chatbot] Model type is not valid or not defined.")
    
    # Load the model
    if (modelType == "lcpp"):
        model = utils_llama.LoadLlamaModel(Configuration)

    __models__[Name] = Configuration | model

    testInferenceConversation = ServiceConfiguration["test_inference_conversation"]

    for message in testInferenceConversation:
        if (isinstance(message["content"], str)):
            message["content"] = [{"type": "text", "text": message["content"]}]

        for content in message["content"]:
            if (content["type"] != "text"):
                with open(content[content["type"]], "rb") as f:
                    content[content["type"]] = base64.b64encode(f.read()).decode("utf-8")

    # Test the inference
    if ("_private_test_inference" in Configuration and Configuration["_private_test_inference"]):
        logs.WriteLog(logs.INFO, "[service_chatbot] Testing inference of the model.")
        files = []

        if ("test_inference_files" in ServiceConfiguration):
            for file in ServiceConfiguration["test_inference_files"]:
                if (file["type"] != "image" and file["type"] != "video" and file["type"] != "audio"):
                    logs.WriteLog(logs.WARNING, f"[service_chatbot] Unexpected file type during inference testing. Skipping file: `{file}`.")
                    continue

                with open(file["data"], "rb") as f:
                    files.append({"type": file["type"], file["type"]: base64.b64encode(f.read()).decode("utf-8")})
        else:
            logs.WriteLog(logs.INFO, "[service_chatbot] Inference test files not specified.")

        response = SERVICE_INFERENCE(
            Name,
            ServiceConfiguration["test_inference_configuration"],
            {"conversation": testInferenceConversation}
        )
        testInferenceResponse = ""

        for token in response:
            testInferenceResponse += token["text"]
        
        logs.WriteLog(logs.INFO, f"[service_chatbot] Test inference response for model `{Name}`:\n```markdown\n{testInferenceResponse}\n```")