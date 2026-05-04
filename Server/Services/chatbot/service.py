# Import libraries
import logging
from typing import Any
from collections.abc import Generator
import base64
import json
import copy
import re
import xml.etree.ElementTree as XML_ElementTree
import Services.chatbot.llama_utils as utils_llama

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
        
        logging.info("[service_chatbot] Offloading model.")

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

    temperature = UserConfig["temperature"] if ("temperature" in UserConfig and ServiceConfiguration["temperature"]["modified_by_user"]) else __models__[Name]["temperature"] if ("temperature" in __models__[Name]) else ServiceConfiguration["temperature"]["default"]
    topP = UserConfig["top_p"] if ("top_p" in UserConfig and ServiceConfiguration["top_p"]["modified_by_user"]) else __models__[Name]["top_p"] if ("top_p" in __models__[Name]) else ServiceConfiguration["top_p"]["default"]
    topK = UserConfig["top_k"] if ("top_k" in UserConfig and ServiceConfiguration["top_k"]["modified_by_user"]) else __models__[Name]["top_k"] if ("top_k" in __models__[Name]) else ServiceConfiguration["top_k"]["default"]
    topNSigma = UserConfig["top_n_sigma"] if ("top_n_sigma" in UserConfig and ServiceConfiguration["top_n_sigma"]["modified_by_user"]) else __models__[Name]["top_n_sigma"] if ("top_n_sigma" in __models__[Name]) else ServiceConfiguration["top_n_sigma"]["default"]
    minP = UserConfig["min_p"] if ("min_p" in UserConfig and ServiceConfiguration["min_p"]["modified_by_user"]) else __models__[Name]["min_p"] if ("min_p" in __models__[Name]) else ServiceConfiguration["min_p"]["default"]
    typicalP = UserConfig["typical_p"] if ("typical_p" in UserConfig and ServiceConfiguration["typical_p"]["modified_by_user"]) else __models__[Name]["typical_p"] if ("typical_p" in __models__[Name]) else ServiceConfiguration["typical_p"]["default"]
    seed = UserConfig["seed"] if ("seed" in UserConfig and ServiceConfiguration["seed"]["modified_by_user"]) else __models__[Name]["seed"] if ("seed" in __models__[Name]) else ServiceConfiguration["seed"]["default"]
    presencePenalty = UserConfig["presence_penalty"] if ("presence_penalty" in UserConfig and ServiceConfiguration["presence_penalty"]["modified_by_user"]) else __models__[Name]["presence_penalty"] if ("presence_penalty" in __models__[Name]) else ServiceConfiguration["presence_penalty"]["default"]
    frequencyPenalty = UserConfig["frequency_penalty"] if ("frequency_penalty" in UserConfig and ServiceConfiguration["frequency_penalty"]["modified_by_user"]) else __models__[Name]["frequency_penalty"] if ("frequency_penalty" in __models__[Name]) else ServiceConfiguration["frequency_penalty"]["default"]
    repeatPenalty = UserConfig["repeat_penalty"] if ("repeat_penalty" in UserConfig and ServiceConfiguration["repeat_penalty"]["modified_by_user"]) else __models__[Name]["repeat_penalty"] if ("repeat_penalty" in __models__[Name]) else ServiceConfiguration["repeat_penalty"]["default"]
    penaltyLastN = UserConfig["penalty_last_n"] if ("penalty_last_n" in UserConfig and ServiceConfiguration["penalty_last_n"]["modified_by_user"]) else __models__[Name]["penalty_last_n"] if ("penalty_last_n" in __models__[Name]) else ServiceConfiguration["penalty_last_n"]["default"]
    tools = UserConfig["tools"] if ("tools" in UserConfig and ServiceConfiguration["tools"]["modified_by_user"]) else []
    toolChoice = UserConfig["tool_choice"] if ("tool_choice" in UserConfig and ServiceConfiguration["tool_choice"]["modified_by_user"]) else "auto" if (len(tools) > 0) else "none"
    maxLength = UserConfig["max_length"] if ("max_length" in UserConfig and ServiceConfiguration["max_length"]["modified_by_user"]) else __models__[Name]["max_length"] if ("max_length" in __models__[Name]) else ServiceConfiguration["max_length"]["default"]
    stopTokens = UserConfig["stop_tokens"] if ("stop_tokens" in UserConfig) else UserConfig["stop"] if ("stop" in UserConfig) else []
    stopTokens = [str(s) for s in stopTokens] if (isinstance(stopTokens, list)) else [str(stopTokens)]
    extraParameters = __models__[Name]["_private_extra_parameters"] if ("_private_extra_parameters" in __models__[Name]) else {}
    
    if (maxLength > ServiceConfiguration["max_length"]["default"] and not ServiceConfiguration["max_length"]["allow_greater_than_default"]):
        maxLength = ServiceConfiguration["max_length"]["default"]
    
    extraModelCTParams = {}
    extraHandlerCTParams = {}

    if ("extra_chat_template_parameters" in ServiceConfiguration):
        for pn, pv in ServiceConfiguration["extra_chat_template_parameters"]["parameters"].items():
            if (pv["type"] == "base" or pv["type"] == "model"):
                extraModelCTParams[pn] = pv["value"]
            elif (pv["type"] == "mmproj" or pv["type"] == "handler"):
                extraHandlerCTParams[pn] = pv["value"]
            else:
                raise ValueError("Invalid extra parameter type.")
        
    if ("extra_chat_template_parameters" in __models__[Name]):
        for pn, pv in __models__[Name]["extra_chat_template_parameters"].items():
            if (pv["type"] == "base" or pv["type"] == "model"):
                extraModelCTParams[pn] = pv["value"]
            elif (pv["type"] == "mmproj" or pv["type"] == "handler"):
                extraHandlerCTParams[pn] = pv["value"]
            else:
                raise ValueError("Invalid extra parameter type.")
    
    if ("template_parameters" in UserConfig and ServiceConfiguration["extra_chat_template_parameters"]["modified_by_user"]):
        for pn, pv in UserConfig["template_parameters"].items():
            if (
                ((pv["type"] == "base" or pv["type"] == "model") and pn not in extraModelCTParams) or
                ((pv["type"] == "mmproj" or pv["type"] == "handler") and pn not in extraHandlerCTParams)
            ):
                yield {"warnings": [f"Tried to pass an invalid parameter ({pn}). Parameter ignored."]}
                continue
            
            if (pv["type"] == "base" or pv["type"] == "model"):
                extraModelCTParams[pn] = pv["value"]
            elif (pv["type"] == "mmproj" or pv["type"] == "handler"):
                extraHandlerCTParams[pn] = pv["value"]
            else:
                yield {"warnings": [f"Invalid parameter type for {pn}. Parameter ignored."]}
                continue

    startsThinking = "starts_thinking" in __models__[Name]["reasoning"] and __models__[Name]["reasoning"]["starts_thinking"]
    generatesStartToken = "generates_start_token" in __models__[Name]["reasoning"] and __models__[Name]["reasoning"]["generates_start_token"]

    if ("reasoning_mode" in UserConfig and "reasoning" in __models__[Name] and "levels" in __models__[Name]["reasoning"] and UserConfig["reasoning_mode"] in __models__[Name]["reasoning"]["levels"]):
        if ("_private_model_params" in __models__[Name]["reasoning"] and UserConfig["reasoning_mode"] in __models__[Name]["reasoning"]["_private_model_params"]):
            for pn, pv in __models__[Name]["reasoning"]["_private_model_params"][UserConfig["reasoning_mode"]].items():
                if (pn == "starts_thinking"):
                    startsThinking = pv
                elif (pn == "generates_start_token"):
                    generatesStartToken = pv
                else:
                    extraParameters[pn] = pv
        
        if ("_private_model_template" in __models__[Name]["reasoning"] and UserConfig["reasoning_mode"] in __models__[Name]["reasoning"]["_private_model_template"]):
            for pn, pv in __models__[Name]["reasoning"]["_private_model_template"][UserConfig["reasoning_mode"]].items():
                if (pv["type"] == "base" or pv["type"] == "model"):
                    extraModelCTParams[pn] = pv["value"]
                elif (pv["type"] == "mmproj" or pv["type"] == "handler"):
                    extraHandlerCTParams[pn] = pv["value"]
                else:
                    raise ValueError("Invalid extra parameter type.")
        
        if ("model_params" in __models__[Name]["reasoning"] and UserConfig["reasoning_mode"] in __models__[Name]["reasoning"]["model_params"]):
            for pn, pv in __models__[Name]["reasoning"]["model_params"][UserConfig["reasoning_mode"]].items():
                if (pn == "starts_thinking"):
                    startsThinking = pv
                elif (pn == "generates_start_token"):
                    generatesStartToken = pv
                else:
                    extraParameters[pn] = pv
        
        if ("model_template" in __models__[Name]["reasoning"] and UserConfig["reasoning_mode"] in __models__[Name]["reasoning"]["model_template"]):
            for pn, pv in __models__[Name]["reasoning"]["model_template"][UserConfig["reasoning_mode"]].items():
                if (pv["type"] == "base" or pv["type"] == "model"):
                    extraModelCTParams[pn] = pv["value"]
                elif (pv["type"] == "mmproj" or pv["type"] == "handler"):
                    extraHandlerCTParams[pn] = pv["value"]
                else:
                    raise ValueError("Invalid extra parameter type.")
    
    continueGeneration = UserConfig["continue_generation"] if ("continue_generation" in UserConfig) else None

    if (continueGeneration is None):
        continueGeneration = conversation[-1]["role"] == "assistant"
    
    generator = InferenceModel(
        Name,
        conversation,
        {
            "temperature": temperature,
            "top_p": topP,
            "top_k": topK,
            "top_n_sigma": topNSigma,
            "min_p": minP,
            "typical_p": typicalP,
            "seed": seed,
            "presence_penalty": presencePenalty,
            "frequency_penalty": frequencyPenalty,
            "repeat_penalty": repeatPenalty,
            "penalty_last_n": penaltyLastN,
            "tools": tools,
            "tool_choice": toolChoice,
            "max_length": maxLength,
            "stop": stopTokens,
            "extra_parameters": extraParameters,
            "extra_template_parameters_model": extraModelCTParams,
            "extra_template_parameters_handler": extraHandlerCTParams,
            "reasoning_starts_thinking": startsThinking,
            "reasoning_generates_start_token": generatesStartToken,
            "continue_generation": continueGeneration
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
            txt = None

            for content in message["content"]:
                if (content["type"] not in __models__[Name]["multimodal"]):
                    yield {"warnings": [f"Content type '{content['type']}' not supported by this model, this will be ignored."]}
                    continue
                elif (len(__models__[Name]["multimodal"]) == 1 and __models__[Name]["multimodal"][0] == "text"):
                    if (txt is None):
                        txt = content["text"]
                    else:
                        txt += content["text"]

                if (__models__[Name]["_private_type"] == "lcpp"):
                    if (content["type"] == "image"):
                        content["image_url"] = {"url": f"data:image;base64,{content['image']}"}

                        content["type"] = "image_url"
                        content.pop("image")
                    elif (content["type"] == "audio"):
                        content["audio_url"] = {"url": f"data:audio;base64,{content['audio']}"}

                        content["type"] = "audio_url"
                        content.pop("audio")
                    # TODO: Add video when supported
            
            if (txt is not None):
                message["content"] = txt

        modelConversation.append(message)
    
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

    fullAssistantText = ""
    firstToken = True
    isThinking = Configuration["reasoning_starts_thinking"]
    reasoningStartToken = __models__[Name]["reasoning"]["start_token"] if ("reasoning" in __models__[Name] and "start_token" in __models__[Name]["reasoning"]) else None
    reasoningEndToken = __models__[Name]["reasoning"]["end_token"] if ("reasoning" in __models__[Name] and "end_token" in __models__[Name]["reasoning"]) else None

    if (reasoningStartToken is None):
        reasoningStartToken = ServiceConfiguration["reasoning_start_token"]
    
    if (reasoningEndToken is None):
        reasoningEndToken = ServiceConfiguration["reasoning_end_token"]

    if (__models__[Name]["_private_type"] == "lcpp"):
        model: utils_llama.Llama = __models__[Name]["_private_model"]
        prevModelChatTemplateArgs = None
        prevChatHandlerTemplateArgs = None

        for pn, pv in Configuration["extra_template_parameters_model"].items():
            pass  # TODO

        if (model.chat_handler is not None):
            prevChatHandlerTemplateArgs = copy.deepcopy(model.chat_handler.extra_template_arguments)

            for pn, pv in Configuration["extra_template_parameters_handler"].items():
                model.chat_handler.extra_template_arguments[pn] = pv

        response = model.create_chat_completion(
            messages = modelConversation,
            tools = Configuration["tools"],
            tool_choice = Configuration["tool_choice"],
            temperature = Configuration["temperature"],
            top_p = Configuration["top_p"],
            top_k = Configuration["top_k"],
            top_n_sigma = Configuration["top_n_sigma"],
            min_p = Configuration["min_p"],
            typical_p = Configuration["typical_p"],
            stream = True,
            seed = Configuration["seed"],
            max_tokens = Configuration["max_length"],
            present_penalty = Configuration["presence_penalty"],
            frequency_penalty = Configuration["frequency_penalty"],
            repeat_penalty = Configuration["repeat_penalty"],
            penalty_last_n = Configuration["penalty_last_n"],
            stop = Configuration["stop"],
            assistant_prefill = Configuration["continue_generation"],
            **Configuration["extra_parameters"]
        )

        try:
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
                
                if (firstToken and isThinking and not Configuration["reasoning_generates_start_token"]):
                    yield {"text": reasoningStartToken, "extra": {"thinking": isThinking}}

                if (not isThinking and fullAssistantText.strip().endswith(reasoningStartToken)):
                    isThinking = True

                firstToken = False
                yield {"text": tokenText, "extra": {"thinking": isThinking}}

                if (isThinking and fullAssistantText.strip().endswith(reasoningEndToken)):
                    isThinking = False
            
            parsedTools = []
            toolsType = __models__[Name]["tool_parse_type"] if ("tool_parse_type" in __models__[Name]) else None

            if (toolsType is None):
                if (isinstance(model.chat_handler, utils_llama.CH_Qwen35)):
                    toolsType = "xml-1"
                else:
                    toolsType = "json-1"
            
            if (toolsType in ["json", "json-1"]):
                parsedTools = [json.loads(tool) for tool in tools]
            elif (toolsType in ["xml", "xml-1"]):
                for tool in tools:
                    fixedXML = re.sub(r"<([a-zA-Z0-9_]+)=([a-zA-Z0-9_]+)>", lambda m: f"<{m.group(1)} name=\"{m.group(2)}\">", tool)
                    root = XML_ElementTree.fromstring(fixedXML)
                    children = {}

                    for child in root:
                        for inputTool in Configuration["tools"]:
                            if (inputTool["function"]["name"] != root.attrib["name"]):
                                continue

                            try:
                                childValue = json.loads(child.text)
                            except json.JSONDecodeError:
                                childValue = str(child.text)
                            
                            children[child.attrib["name"]] = childValue

                    parsedTools.append({"name": root.attrib["name"], "arguments": children})
                    root.clear()
            else:
                raise ValueError("Invalid tools parser.")
            
            yield {"extra": {"tools": parsedTools}}
        finally:
            if (prevModelChatTemplateArgs is not None):
                pass  # TODO
                
            if (prevChatHandlerTemplateArgs is not None):
                model.chat_handler.extra_template_arguments = prevChatHandlerTemplateArgs
            
            if ("_private_delete_kv_cache" not in __models__[Name] or __models__[Name]["_private_delete_kv_cache"]):
                utils_llama.ClearLlamaCache(model)

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
    
    logging.info("[service_chatbot] Loading model.")

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
        logging.info("[service_chatbot] Testing inference of the model.")
        files = []

        if ("test_inference_files" in ServiceConfiguration):
            for file in ServiceConfiguration["test_inference_files"]:
                if (file["type"] != "image" and file["type"] != "video" and file["type"] != "audio"):
                    logging.warning(f"[service_chatbot] Unexpected file type during inference testing. Skipping file: `{file}`.")
                    continue

                with open(file["data"], "rb") as f:
                    files.append({"type": file["type"], file["type"]: base64.b64encode(f.read()).decode("utf-8")})
        else:
            logging.info("[service_chatbot] Inference test files not specified.")

        response = SERVICE_INFERENCE(
            Name,
            ServiceConfiguration["test_inference_configuration"],
            {"conversation": testInferenceConversation}
        )
        testInferenceResponse = ""

        for token in response:
            if ("text" in token):
                testInferenceResponse += token["text"]
        
        logging.info(f"[service_chatbot] Test inference response for model `{Name}`:\n```markdown\n{testInferenceResponse}\n```")