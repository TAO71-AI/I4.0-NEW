# Import libraries
from typing import Any
from collections.abc import Generator
import base64
import json
import copy
import Services.chatbot.llama_utils as utils_llama
import Services.chatbot.tools as cb_tools
import Utilities.logs as logs
import Utilities.internet as internet
import services_manager as servmgr

__models__: dict[str, dict[str, Any]] = {}
ServiceConfiguration: dict[str, Any] | None = None
ServerConfiguration: dict[str, Any] | None = None

def __check_service_configuration__() -> None:
    if (ServiceConfiguration is None):
        raise ValueError("Service configuration is not defined.")
    
    if (ServiceConfiguration is None):
        raise ValueError("Server configuration is not defined.")
    
    internet.Configuration = ServerConfiguration

def SERVICE_LOAD_MODELS(Models: dict[str, dict[str, Any]]) -> None:
    """
    Load all the chatbot models.

    Args:
        Models (dict[str, dict[str, Any]]): All the models to load.
    
    Returns:
        None
    """
    __check_service_configuration__()

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
            __models__[name]["_private_model"].close()
        
        __models__[name]["_private_model"] = None

def SERVICE_INFERENCE(Name: str, UserConfig: dict[str, Any], UserParameters: dict[str, Any]) -> Generator[dict[str, Any]]:
    """
    Inference the chatbot model.

    Args:
        Name (str): Name of the model.
        UserConfig (dict[str, Any]): Configuration of the user.
        UserParameters (dict[str, Any]): Parameters of the user ("key_info", "conversation_name", "conversation").
    """
    __check_service_configuration__()

    conversation = UserParameters["conversation"]
    tools = []
    extraTools = []
    extraSystemPrompt = {"model": None, "service": None}

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
        userTools = UserConfig["tools"]
    elif ("tools" in __models__[Name]):
        userTools = __models__[Name]["tools"]
    else:
        userTools = ServiceConfiguration["tools"]["default"]
    
    if (isinstance(userTools, str)):
        userTools = userTools.split(" ")

    for tool in cb_tools.GetDefaultTools():
        if (tool["function"]["name"] in userTools or "{all}" in userTools):
            tools.append(tool)

    if ("extra_tools" in UserConfig and ServiceConfiguration["extra_tools"]["modified_by_user"]):
        eTools = UserConfig["extra_tools"]
    elif ("extra_tools" in __models__[Name]):
        eTools = __models__[Name]["extra_tools"]
    else:
        eTools = ServiceConfiguration["extra_tools"]["default"]
    
    for tool in eTools:
        extraTools.append(tool)
    
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
    
    if ("extra_system_prompt" in __models__[Name]):
        extraSystemPrompt["model"] = __models__[Name]["extra_system_prompt"]
    
    if (
        ServiceConfiguration["extra_system_prompt"]["default"] is not None and
        len(ServiceConfiguration["extra_system_prompt"]["default"].strip()) != 0
    ):
        extraSystemPrompt["service"] = ServiceConfiguration["extra_system_prompt"]["default"]
    
    if ("_private_extra_parameters" in __models__[Name]):
        extraParameters = __models__[Name]["_private_extra_parameters"]
    else:
        extraParameters = {}
    
    if ("reasoning" in UserConfig):
        reasoningLevel = UserConfig["reasoning"]
    else:
        reasoningLevel = __models__[Name]["reasoning"]["default_mode"]

    if (reasoningLevel == "reasoning"):
        reasoningLevel = __models__[Name]["reasoning"]["default_reasoning_level"]
    elif (reasoningLevel == "nonreasoning"):
        reasoningLevel = __models__[Name]["reasoning"]["non_reasoning_level"]
    elif (reasoningLevel == "auto"):
        if (servmgr.IsServiceInstalled("text_classification")):
            pass  # TODO: Get auto level
        else:
            logs.WriteLog(
                logs.WARNING,
                "[service_chatbot] Optional `text_classification` service not installed, but trying to use automatic reasoning level. Changing to `reasoning`."
            )
            reasoningLevel = __models__[Name]["reasoning"]["default_reasoning_level"]
    elif (reasoningLevel in __models__[Name]["reasoning"]["levels"]):
        pass  # TODO
    else:
        raise ValueError("Invalid reasoning mode or level.")
    
    if (
        "parameters" in __models__[Name]["reasoning"] and
        reasoningLevel in __models__[Name]["reasoning"]["parameters"]
    ):
        extraParameters |= __models__[Name]["reasoning"]["parameters"][reasoningLevel]
    
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
            "extra_tools": extraTools,
            "tool_choice": toolChoice,
            "max_length": maxLength,
            "extra_system_prompt": extraSystemPrompt,
            "extra_parameters": extraParameters,
            "reasoning": reasoningLevel
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
    __check_service_configuration__()
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

            if (Configuration["extra_system_prompt"]["service"] is not None):
                content = Configuration["extra_system_prompt"]["service"] + "\n" + content
            
            if (Configuration["extra_system_prompt"]["model"] is not None):
                content = Configuration["extra_system_prompt"]["model"] + "\n" + content

            if ("reasoning" in Configuration and Configuration["reasoning"] in __models__[Name]["reasoning"]["system_prompt"]["levels"]):
                if (__models__[Name]["reasoning"]["system_prompt"]["position"] == "start"):
                    content = __models__[Name]["reasoning"]["system_prompt"]["levels"][Configuration["reasoning"]] + __models__[Name]["reasoning"]["system_prompt"]["separator"] + content
                else:
                    content += __models__[Name]["reasoning"]["system_prompt"]["separator"] + __models__[Name]["reasoning"]["system_prompt"]["levels"][Configuration["reasoning"]]

            message["content"] = content
        elif (message["role"] == "user" and conversation.index(message) == len(conversation) - 1):
            if ("reasoning" in Configuration and Configuration["reasoning"] in __models__[Name]["reasoning"]["user_prompt"]["levels"]):
                contentTextIdx = None

                for content in message["content"]:
                    if (content["type"] == "text"):
                        contentTextIdx = content["content"].index(content)

                        if (__models__[Name]["reasoning"]["user_prompt"]["position"] == "start"):
                            break
                
                if (contentTextIdx is None):
                    contentTextIdx = len(message["content"])
                    message["content"].append({"type": "text", "text": ""})

                if (__models__[Name]["reasoning"]["user_prompt"]["position"] == "start"):
                    message["content"][contentTextIdx]["text"] = __models__[Name]["reasoning"]["user_prompt"]["levels"][Configuration["reasoning"]] + __models__[Name]["reasoning"]["user_prompt"]["separator"] + message["content"][contentTextIdx]["text"]
                else:
                    message["content"][contentTextIdx]["text"] += __models__[Name]["reasoning"]["user_prompt"]["separator"] + __models__[Name]["reasoning"]["user_prompt"]["levels"][Configuration["reasoning"]]

        if (isinstance(message["content"], list)):
            for content in message["content"]:
                if (content["type"] not in __models__[Name]["multimodal"]):
                    yield {"warnings": [f"Content type '{content['type']}' not supported by this model."]}
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
            tools = Configuration["tools"] + Configuration["extra_tools"],
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
        
        logs.WriteLog(logs.INFO, "[service_chatbot] Finished inference. Saving conversation and checking tools.")
        conversation.append({"role": "assistant", "content": [{"type": "text", "text": fullAssistantText}]})
        
        for tool in tools:
            tool = tool.strip()
            toolExists = False

            try:
                tool = json.loads(tool)

                for bTool in Configuration["tools"]:
                    if (tool["name"] != bTool["function"]["name"]):
                        continue

                    toolExists = True

                    if (tool["name"] == "scrape_website"):
                        yield {"text": "\n"}

                        urls = tool["arguments"]["urls"]
                        prompt = tool["arguments"]["prompt"]
                        inputText = "# Internet results\n\n"

                        logs.WriteLog(logs.INFO, f"[service_chatbot] Scrapping URLs: {urls}")

                        for url in urls:
                            urlInfo = internet.GetURLInfo(url)
                            inputText += f"## {url}\n\n"

                            if (urlInfo["website"] == "reddit.com"):
                                if ("/comments/" in url):
                                    postData = internet.Scrape_Reddit_Post(url, None)

                                    inputText += f"Type: Reddit (post)\n\n"
                                    inputText += f"Title: {postData['title']}\n\n"
                                    inputText += f"Content:\n```markdown\n{postData['content']}\n```"
                                else:
                                    subPosts = internet.Scrape_Reddit_Subreddit(url, False, False, None, None)

                                    inputText += f"Type: Reddit (subreddit)\n\n"
                                    inputText += f"Posts:\n```json\n{json.dumps(subPosts, indent = 2)}\n```"
                            elif (urlInfo["website"] == "wikipedia.com"):
                                wikiData = internet.Scrape_Wikipedia(url)

                                inputText += f"Type: Wikipedia\n\n"
                                inputText += f"Title: {wikiData['title']}\n\n"
                                inputText += f"Content:\n```markdown\n{wikiData['content']}\n```"
                            else:
                                baseURL = internet.GetBaseURL(url)
                                websiteContent = str(internet.Scrape_Base(url).find_all())
                                websiteContent = internet.format_conversion.HTML_To_Markdown(websiteContent, baseURL)

                                inputText += f"Type: Not recognized\n\n"
                                inputText += f"Content:\n```markdown\n{websiteContent}\n```"
                                    
                            inputText += "\n\n"
                            
                        trimResponseLength = __models__[Name]["ctx"] - len(prompt) - 1

                        if (trimResponseLength <= 0):
                            raise ValueError("Could not trim response because the max length is less or equals to 0.")

                        inputText = inputText.strip()
                        inputText = inputText[:trimResponseLength]

                        conversation.append({"role": "tool", "content": [{"type": "text", "text": inputText}]})
                        conversation.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

                        inf = InferenceModel(Name, conversation, Configuration | {
                            "tools": [],
                            "extra_tools": []
                        })
                        responseText = ""

                        for token in inf:
                            responseText += token["text"]
                            yield token
                    elif (tool["name"] == "search_text"):
                        pass  # TODO
                
                if (not toolExists):
                    yield {"text": json.dumps(tool), "warnings": ["Unknown tool"]}
            except Exception as ex:
                logs.WriteLog(logs.ERROR, f"[service_chatbot] Error processing tool: {ex}")
                yield {"errors": [f"Error processing tool: {ex}"]}
        
        logs.WriteLog(logs.INFO, "[service_chatbot] Finished inference. All tools processed.")

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

        response = InferenceModel(
            Name,
            [{"role": "user", "content": files + [{"type": "text", "text": ServiceConfiguration["test_inference_prompt"]}]}],
            {
                "temperature": 0,
                "top_p": 0.95,
                "top_k": 40,
                "min_p": 0.05,
                "typical_p": 1,
                "seed": None,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "repeat_penalty": 1,
                "tools": [],
                "extra_tools": [],
                "tool_choice": "none",
                "max_length": ServiceConfiguration["test_inference_max_length"],
                "predefined_system_prompt": {
                    "personality": False,
                    "birthday": False,
                    "current_time": False,
                    "current_date": False,
                    "service_extra_system_prompt": False,
                    "model_extra_system_prompt": False,
                    "user_extra_system_prompt": False
                }
            }
        )
        testInferenceResponse = ""

        for token in response:
            testInferenceResponse += token["text"]
        
        logs.WriteLog(logs.INFO, f"[service_chatbot] Test inference response for model `{Name}`:\n```markdown\n{testInferenceResponse}\n```")