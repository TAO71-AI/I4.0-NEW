from . import configuration as config
from . import server_connection as server
from .Utilities import chatbot_tools
import os
import sys
import json
import base64
import traceback
import asyncio

def __main__() -> None:
    system = sys.platform
    configFile = None
    conversation = {"conv": [], "params_user": {}, "params_prompt": {
        "tools": chatbot_tools.GetDefaultTools()
    }}
    conversationFile = None

    if (
        system != "win32" and
        system != "darwin" and
        system != "linux"
    ):
        raise OSError("Unsupported OS.")
    
    if (system == "win32"):
        homePath = os.environ["LOCALAPPDATA"] + "/I4.0-Client"
    elif (system == "darwin"):
        homePath = f"{os.path.expanduser('~')}/Library/Application Support/I4.0-Client"
    elif (system == "linux"):
        homePath = f"{os.path.expanduser('~')}/.local/share/I4.0-Client"
    
    if (not os.path.exists(homePath)):
        os.mkdir(homePath)

    for arg in sys.argv:
        if (arg.startswith("--config=")):
            configFile = arg[9:]

            if (not os.path.exists(configFile) or not os.path.isfile(configFile)):
                configFile = None
        elif (arg.startswith("--conv-file=")):
            conversationFile = arg[12:]

            if (os.path.exists(conversationFile) and os.path.isfile(conversationFile)):
                with open(conversationFile, "r") as f:
                    conversation = json.loads(f.read())
            else:
                with open(conversationFile, "x") as f:
                    f.write(json.dumps(conversation, indent = 4))

    if (configFile is None):
        configFile = f"{homePath}/config.json"

        if (not os.path.exists(configFile)):
            conf = config.ClientConfiguration()
            
            setattr(conf, "CLIENT_ConType", input("Connection type ('websocket'): "))
            setattr(conf, "CLIENT_Host", input("Server to connect (Host): "))
            setattr(conf, "CLIENT_Port", int(input("Server to connect (Port): ")))
            setattr(conf, "CLIENT_Secure", bool(int(input("Server to connect (Secure) ('0', '1'): "))))
            setattr(conf, "CLIENT_ModelName", input("Model name: "))
            setattr(conf, "CLIENT_Scrape_FollowGuidelines", bool(int(input("Follow websites guidelines when scrapping? ('0', '1'): "))))

            with open(configFile, "x") as f:
                f.write(json.dumps(conf.ToDict(SavePublicKey = False), indent = 4))
            
            conf = None
    
    if (conversationFile is None):
        conversationFile = f"{homePath}/conversation.json"

        if (not os.path.exists(conversationFile)):
            with open(conversationFile, "x") as f:
                f.write(json.dumps(conversation, indent = 4))
    
    with open(configFile, "r") as f:
        conf = json.loads(f.read())
    
    with open(conversationFile, "r") as f:
        conversation = json.loads(f.read())
    
    conf = config.ClientConfiguration.FromDict(conf)
    chatbot_tools.internet.FollowScrapeGuidelines = getattr(conf, "CLIENT_Scrape_FollowGuidelines")

    print(f"Got {len(conversation['conv'])} messages from the conversation.", flush = True)
    
    async def __socket__() -> None:
        async def __send__(AllowTools: bool = True) -> None:
            await socket.Connect(getattr(conf, "CLIENT_Host"), getattr(conf, "CLIENT_Port"), getattr(conf, "CLIENT_Secure"))

            modelInfo = await socket.GetModelInfo(getattr(conf, "CLIENT_ModelName"))
            gen = socket.AdvancedSendAndReceive(
                getattr(conf, "CLIENT_ModelName"),
                None,
                conversation["conv"],
                conversation["params_prompt"],
                conversation["params_user"],
                "inference"
            )
            errors = 0
            tools = []

            async for token in gen:
                if ("conversation_result" in token):
                    conversation["conv"] = token["conversation_result"]

                if ("response" in token):
                    if ("text" in token["response"]):
                        print(token["response"]["text"], end = "", flush = True)
                    
                    if ("files" in token["response"]):
                        for file in token["response"]["files"]:
                            if (file["type"] == "image"):
                                fileExtension = "webp"
                            elif (file["type"] == "audio"):
                                fileExtension = "wav"
                            elif (file["type"] == "video"):
                                fileExtension = "webm"
                            else:
                                fileExtension = file["type"]

                            fileData = base64.b64decode(file[file["type"]])
                            fileID = 0
                            fileName = f"./file_{fileID}.{fileExtension}"

                            while (os.path.exists(fileName)):
                                fileID += 1
                                fileName = f"./file_{fileID}.{fileExtension}"
                            
                            with open(fileName, "wb") as f:
                                f.write(fileData)
                            
                            print(f"\nFile saved at '{fileName}'.", flush = True)
                    
                    if ("tools" in token["response"]):
                        tools += token["response"]["tools"]
                
                if ("warnings" in token):
                    for warning in token["warnings"]:
                        print(f"\nWARNING: {warning}", flush = True)
                
                if ("errors" in token):
                    for error in token["errors"]:
                        print(f"\nERROR: {error}", flush = True)
                    
                    errors += len(token["errors"])
            
            if (len(tools) > 0 and AllowTools and modelInfo["service"] == "chatbot"):
                toolsResponse = ""

                for tool in tools:
                    toolName = tool["name"]
                    toolArgs = tool["arguments"]

                    try:
                        toolR = chatbot_tools.ExecuteTool(toolName, toolArgs, modelInfo["ctx"])

                        if (toolR is not None):
                            toolsResponse += f"{toolR}\n"
                    except Exception as ex:
                        print(f"\nERROR: Error processing tool ({type(ex)}): {ex}", flush = True)
                        errors += 1
                
                if (len(toolsResponse) > 0):
                    print("", flush = True)

                    conversation["conv"].append(
                        {
                            "role": "tool",
                            "content": [
                                {
                                    "type": "text",
                                    "text": toolsResponse
                                }
                            ]
                        }
                    )
                    await __send__(False)

                    return
            
            print("", flush = True)

            if (errors > 0):
                confirm = input("Errors during inference. Save conversation anyway? [y/N] ").strip().lower() == "y"

                if (not confirm):
                    await socket.Close()
                    return

            with open(conversationFile, "w") as f:
                f.write(json.dumps(conversation, indent = 4))
            
            await socket.Close()
        
        socket = server.ClientSocket(
            Type = getattr(conf, "CLIENT_ConType"),
            Configuration = conf
        )

        while (True):
            try:
                mode = input("Mode ['e', 'scc', 'cc', 'pp', 'up', 'sc', 'h', 'c'*]: ").lower()

                if (mode == "e"):
                    break
                elif (mode == "sc"):
                    for msg in conversation["conv"]:
                        msgContent = ""

                        for content in msg["content"]:
                            if (content["type"] == "text"):
                                msgContent += content["text"]
                            else:
                                msgContent += "--FILE DATA--"
                        
                        print(f"Message #{conversation['conv'].index(msg)}:\nRole: {msg['role']}\nContent:\n```\n{msgContent}\n```\n", flush = True)

                    continue
                elif (mode == "h"):
                    print((
                        "'e' - Exit - Closes the client.\n"
                        "'scc' - Selective Clear Conversation - Delete conversation messages selectively.\n"
                        "'cc' - Clear Conversation - Clear the whole conversation.\n"
                        "'pp' - Prompt Parameters - Change the prompt parameters.\n"
                        "'up' - User Parameters - Change the user parameters.\n"
                        "'sc' - Show Conversation - Show the current conversation.\n"
                        "'h' - Help - Show this help message.\n"
                        "'c' - Continue - Continue with inference.\n\n"
                        "* - Default option."
                    ), flush = True)
                    continue
                elif (mode == "scc"):
                    msgID = 0

                    while (msgID < len(conversation["conv"])):
                        msgContent = []

                        for content in conversation["conv"][msgID]["content"]:
                            cont = f"        Type: {content['type']}\n        Data: "

                            if (content["type"] == "text"):
                                cont += content["text"]
                            else:
                                cont += "--FILE DATA--"
                            
                            msgContent.append(cont)
                        
                        msgContent = "\n".join(msgContent)
                        print(f"Message #{msgID + 1}:\n    Role: {conversation['conv'][msgID]['role']}\n    Content:\n{msgContent}", flush = True)

                        confirm = input("Delete this message? [y/N] ").strip().lower() == "y"

                        if (confirm):
                            conversation["conv"].remove(conversation["conv"][msgID])
                            continue

                        msgID += 1
                    
                    print("No more messages to delete.", flush = True)
                    
                    with open(conversationFile, "w") as f:
                        f.write(json.dumps(conversation, indent = 4))
                    
                    continue
                elif (mode == "cc"):
                    confirm = input("WARNING!\nThis will delete ALL OF YOUR MESSAGES.\nContinue? [y/N] ").strip().lower() == "y"

                    if (not confirm):
                        continue

                    conversation["conv"].clear()

                    with open(conversationFile, "w") as f:
                        f.write(json.dumps(conversation, indent = 4))
                    
                    continue
                elif (mode == "pp"):
                    params = {}

                    while (True):
                        name = input("Prompt Parameter name (empty = continue): ")

                        if (len(name) == 0):
                            break

                        val = input("Prompt Parameter value (json:DATA, str:TEXT, int:INTEGER, float:FLOAT, bool:BOOLEAN): ")

                        if (val.lower().startswith("json:")):
                            val = json.loads(val[5:])
                        elif (val.lower().startswith("int:")):
                            val = int(val[4:])
                        elif (val.lower().startswith("float:")):
                            val = float(val[6:])
                        elif (val.lower().startswith("bool:")):
                            val = bool(val[5:])
                        elif (not val.lower().startswith("str:")):
                            print("Invalid value type. Try again.", flush = True)
                            continue

                        params[name] = val
                    
                    conversation["params_prompt"] = params

                    with open(conversationFile, "w") as f:
                        f.write(json.dumps(conversation, indent = 4))

                    continue
                elif (mode == "up"):
                    params = {}

                    while (True):
                        name = input("User Parameter name (empty = continue): ")

                        if (len(name) == 0):
                            break

                        val = input("User Parameter value (json:DATA, str:TEXT, int:INTEGER, float:FLOAT, bool:BOOLEAN): ")

                        if (val.lower().startswith("json:")):
                            val = json.loads(val[5:])
                        elif (val.lower().startswith("int:")):
                            val = int(val[4:])
                        elif (val.lower().startswith("float:")):
                            val = float(val[6:])
                        elif (val.lower().startswith("bool:")):
                            val = bool(val[5:])
                        elif (not val.lower().startswith("str:")):
                            print("Invalid value type. Try again.", flush = True)
                            continue

                        params[name] = val
                    
                    conversation["params_user"] = params

                    with open(conversationFile, "w") as f:
                        f.write(json.dumps(conversation, indent = 4))

                    continue
                elif (len(mode) > 0 and mode != "c"):
                    print("Invalid mode. Try again.")
                    continue

                if (len(conversation["conv"]) > 0 and conversation["conv"][-1]["role"] == "user"):
                    confirm = input((
                        "The last message in the saved conversation is a user message.\n"
                        "Adding another user message to the conversation may result in unexpected behaviour.\n\n"
                        "Send current conversation? [Y/n] "
                    )).strip().lower() != "n"

                    if (confirm):
                        await __send__()
                        continue

                while (True):
                    msgRole = input(f"Message #{len(conversation['conv']) + 1} role (empty = continue): ")

                    if (len(msgRole) == 0):
                        break

                    msgContent = []

                    while (True):
                        content = {}
                        content["type"] = input(f"Message #{len(conversation['conv']) + 1} content #{len(msgContent) + 1} type (empty = continue): ")

                        if (len(content["type"]) == 0):
                            break
                        elif (content["type"] == "text"):
                            contTxt = ""

                            while (True):
                                contTxt += input("TEXT > ")

                                if (contTxt.endswith(" \\")):
                                    contTxt = contTxt[:-2] + "\n"
                                    continue
                                elif (contTxt.split("\n")[-1] == "\\"):
                                    contTxt = contTxt[:-1] + "\n"
                                    continue

                                break

                            content[content["type"]] = contTxt
                        else:
                            fp = input("FILE PATH > ")

                            if (not os.path.exists(fp)):
                                print("File does not exist. Try again.")
                                continue

                            with open(fp, "rb") as f:
                                content[content["type"]] = base64.b64encode(f.read()).decode("utf-8")
                        
                        msgContent.append(content)
                    
                    conversation["conv"].append({"role": msgRole, "content": msgContent})

                await __send__()

                with open(conversationFile, "w") as f:
                    f.write(json.dumps(conversation, indent = 4))
            except KeyboardInterrupt:
                print("", flush = True)
                continue
            except Exception as ex:
                print(f"Unexpected error (Type: {type(ex)}): {ex}", flush = True)
                confirm = input("Ignore unexpected error? [Y/n/d] ").strip().lower()

                if (confirm == "d"):
                    traceback.print_exception(ex)
                    confirm = input("Ignore unexpected error? [Y/n] ").strip().lower()
                
                if (confirm == "n"):
                    break
        
        await socket.Close()
    
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(__socket__())
    asyncio.get_event_loop().close()

if (__name__ == "__main__"):
    __main__()