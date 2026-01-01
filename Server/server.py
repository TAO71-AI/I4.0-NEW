try:
    from typing import Any
    from collections.abc import Generator
    import os
    import sys
    import json
    import time
    import random
    import asyncio
    import threading

    import encryption
    import services_manager
    import Utilities.logs as logs
    import Utilities.server_utils as server_utils
    import Configuration.config as config
except Exception as ex:
    import traceback

    print(f"Could not load server modules. Error: {ex}\nPlease make sure all of the requirements are installed.", flush = True)
    traceback.print_exception(ex)

    exit(1)

def LoadModels() -> None:
    try:
        logs.PrintLog(logs.INFO, "[server] Loading all modules...")
        services_manager.LoadModels(config.Configuration["services"])
    except Exception as ex:
        logs.PrintLog(logs.CRITICAL, f"[server] Could not load models. Error: {ex}")
        raise RuntimeError(f"Could not load models: {ex}")

async def __unhandled_connection__(Client: server_utils.Client) -> None:
    if (
        (
            config.Configuration["server_whitelist"]["enabled"] and
            Client.GetEndPoint()[0] not in config.Configuration["server_whitelist"]["ip_whitelist"]
        ) or
        (
            config.Configuration["server_blacklist"]["enabled"] and
            Client.GetEndPoint()[0] in config.Configuration["server_blacklist"]["ip_blacklist"]
        )
    ):
        await Client.Send("Access denied.")
        await Client.Close()

async def __unhandled_received_message__(Client: server_utils.Client, Message: str) -> None:
    global TOSContent

    clientPublicKey = None
    clientPublicKeyStr = None
    
    try:
        # Process basic server commands
        if (Message == "get_public_key"):
            _, publicBytes = encryption.SaveKeys(None, None, "", PublicKey, None)
            await Client.Send(publicBytes.decode("utf-8"))
        elif (Message == "get_tos"):
            await Client.Send(TOSContent)
        else:
            # Process other commands
            async def __send_to_client__(Token: dict[str, Any]) -> None:
                nonlocal clientPublicKey, clientPublicKeyStr, modelName, queueUID, keyInstance

                tokenPublicParams = {k: v for k, v in Token.items() if (not k.startswith("_"))}
                tokenPrivateParams = {k: v for k, v in Token.items() if (k.startswith("_"))}

                if ("_model" in tokenPrivateParams):
                    modelName = tokenPrivateParams["_model"]
                
                if (queueUID is None and "_queue_uid" in tokenPrivateParams):
                    queueUID = tokenPrivateParams["_queue_uid"]
                
                if (keyInstance is None and "_key_instance" in tokenPrivateParams):
                    keyInstance = tokenPrivateParams["_key_instance"]
                
                if (config.Configuration["server_encryption"]["force_response_hash"] is None):
                    responseHash = tokenPrivateParams["_hash"]
                else:
                    responseHash = config.Configuration["server_encryption"]["force_response_hash"]
                
                if (tokenPrivateParams["_public_key"] != clientPublicKeyStr):
                    clientPublicKeyStr = tokenPrivateParams["_public_key"]
                    clientPublicKey = encryption.LoadKeysFromContent(None, "", services_manager.base64.b64decode(clientPublicKeyStr))[1]
                
                responseHashParsed = encryption.ParseHash(responseHash)

                if (
                    config.Configuration["server_encryption"]["obfuscate"] and
                    responseHashParsed is not None and
                    clientPublicKey is not None
                ):
                    chars = "abcdefghijplnmopqrstuvwxyz"
                    chars += chars.upper()
                    chars += "0123456789!@#$%&/()=[]?-_.:,;<>*+"

                    chars = list(chars)
                    random.shuffle(chars)
                    chars = "".join(chars)

                    tokenPublicParams["obfuscate"] = "".join([chars[random.randint(0, len(chars) - 1)] for _ in range(random.randint(5, 25))])
                
                if (clientPublicKey is None):
                    encrItem = json.dumps(tokenPublicParams)
                else:
                    encrItem = encryption.Encrypt(
                        responseHashParsed,
                        clientPublicKey,
                        json.dumps(tokenPublicParams)
                    )
                
                resItem = {
                    "data": encrItem,
                    "hash": responseHash
                }
                resItem = json.dumps(resItem)

                try:
                    await Client.Send(resItem)
                except services_manager.exceptions.ConnectionClosedError as ex:
                    if (modelName is not None):
                        modelQueue = services_manager.queue.GetQueueForModel(modelName)

                        if (modelQueue is not None and queueUID is not None):
                            modelQueue.DeleteUID(queueUID)
                    
                    raise ex
                except Exception as ex:
                    logs.WriteLog(logs.ERROR, f"[server] Error sending to client: {ex}")

            def __run_in_thread__() -> None:
                nonlocal keyInstance

                gen = __process_client__(Message)
                loop = asyncio.new_event_loop()

                for token in gen:
                    try:
                        loop.run_until_complete(__send_to_client__(token))
                    except:
                        if (keyInstance is not None):
                            keyInstance.SaveToFile()

                        break
                
                loop.close()
            
            modelName = None
            queueUID = None
            keyInstance = None

            th = threading.Thread(target = __run_in_thread__)
            th.start()
    except Exception as ex:
        logs.WriteLog(logs.ERROR, f"[server] Error while receiving from client ({ex}). The connection will be closed.")
        await Client.Close()

def __process_client__(Message: str) -> Generator[dict[str, Any]]:
    global SERVER_VERSION

    try:
        message = json.loads(Message)
        messageContent = message["content"]
        messageHash = message["hash"]
        messagePublicKey = message["public_key"]
        clientVersion = message["version"] if ("version" in message) else -1

        if (config.Configuration["server_client_version"]["min"] is None):
            serverMinVersion = SERVER_VERSION
        else:
            serverMinVersion = config.Configuration["server_client_version"]["min"]
        
        if (config.Configuration["server_client_version"]["max"] is None):
            serverMaxVersion = SERVER_VERSION
        else:
            serverMaxVersion = config.Configuration["server_client_version"]["max"]

        if (
            (
                clientVersion != -1 and
                (
                    clientVersion < serverMinVersion or
                    clientVersion > serverMaxVersion
                )
            ) or
            (
                clientVersion == -1 and
                not config.Configuration["server_client_version"]["accept_unknown"]
            )
        ):
            raise NotImplementedError("Client version not accepted.")

        if (messageHash not in config.Configuration["server_encryption"]["allowed_hashes"]["hashes"]):
            raise ValueError(f"Invalid hash. Valid hashes are {config.Configuration['server_encryption']['allowed_hashes']['hashes']}")
        
        if (messageHash in config.Configuration["server_encryption"]["allowed_hashes"]["warnings"]):
            yield {
                "warnings": config.Configuration["server_encryption"]["allowed_hashes"]["warnings"][messageHash],
                "_hash": messageHash,
                "_public_key": messagePublicKey
            }

        messageHashParsed = encryption.ParseHash(messageHash)
        messageContent = encryption.Decrypt(
            messageHashParsed,
            PrivateKey,
            messageContent,
            config.Configuration["server_encryption"]["decryption_threads"]
        )

        try:
            content = json.loads(messageContent)
            modelName = content["model_name"]
            service = content["service"] if ("service" in content) else "inference"
            key = content["key"] if ("key" in content) else "nokey"
            prompt = content["prompt"] if ("prompt" in content) else {}
            userParams = content["user_parameters"] if ("user_parameters" in content) else {}

            time.sleep(0.1)  # Wait 100ms to avoid brute force attacks for the API keys
            keyInstance = services_manager.keys_manager.APIKey.LoadFromFile(key)

            if (keyInstance is None):
                keyInstance = services_manager.keys_manager.APIKey(
                    Tokens = 0,
                    ResetDaily = False,
                    ExpireDate = None,
                    AllowedIPs = None,
                    PrioritizeModels = [],
                    Groups = []
                )
                keyInstance.Key = "nokey"
            
            if (service == "inference"):
                gen = services_manager.InferenceModel(
                    ModelName = modelName,
                    Prompt = prompt,
                    UserParameters = userParams | {
                        "key_info": keyInstance.__dict__
                    }
                )
                
                for token in gen:
                    yield token | {
                        "_model": modelName,
                        "_hash": messageHash,
                        "_public_key": messagePublicKey,
                        "_key_instance": keyInstance
                    }
            elif (service == "get_queue_data"):
                queueData = services_manager.queue.GetQueueForModel(modelName)

                if (queueData is None):
                    queueData = {
                        "waiting_users": 0,
                        "processing_users": 0,
                        "tps": None,
                        "fts": None
                    }
                else:
                    queueData = {
                        "waiting_users": len(queueData.__waiting_uids__),
                        "processing_users": len(queueData.__processing_uids__),
                        "tps": queueData.TokensPerSecond,
                        "fts": queueData.FirstTokenSeconds
                    }

                yield {
                    "queue": queueData,
                    "_hash": messageHash,
                    "_public_key": messagePublicKey
                }
            elif (service == "get_model_info"):
                modelInfo = services_manager.GetModelConfiguration(modelName)

                yield {
                    "config": modelInfo,
                    "_hash": messageHash,
                    "_public_key": messagePublicKey
                }
            elif (service == "get_available_models"):
                names = []

                for _, modelInfo in services_manager.ServicesModels.items():
                    names += list(modelInfo.keys())
                
                yield {
                    "models": names,
                    "_hash": messageHash,
                    "_public_key": messagePublicKey
                }
            else:
                raise ValueError("Invalid service.")
            
            yield {
                "ended": True,
                "_hash": messageHash,
                "_public_key": messagePublicKey
            }
        except Exception as ex:
            yield {
                "ended": True,
                "errors": [f"Error processing message ({ex})."],
                "_hash": messageHash,
                "_public_key": messagePublicKey
            }
    except Exception as ex:
        yield {
            "ended": True,
            "errors": [f"Error decrypting message ({ex})."],
            "_hash": "none",
            "_public_key": None
        }

def StartServer() -> None:
    global PrivateKey, PublicKey, Servers
    
    if (PrivateKey is None or PublicKey is None):
        PrivateKey, PublicKey = encryption.GenerateRSAKeys()
    
    if (config.Configuration["server_transfer_rate"] < 1 or config.Configuration["server_transfer_rate"] > 8192):
        newServerTransferRate = max(1, min(config.Configuration["server_transfer_rate"], 8192))

        logs.PrintLog(logs.WARNING, f"[server] Server transfer rate is too low or too high. Adjusting to {newServerTransferRate}.")
        config.Configuration["server_transfer_rate"] = newServerTransferRate
    
    for server in config.Configuration["server_listen"]:
        try:
            if (
                "type" not in server or
                "host" not in server or
                "port" not in server
            ):
                raise KeyError("Required parameters for server not found.")
            
            if (server["type"] == "websockets"):
                server = server_utils.WebSocketsServer(
                    ListenIP = server["host"],
                    ListenPort = server["port"],
                    TransferRate = config.Configuration["server_transfer_rate"],
                    ConnectedCallback = __unhandled_connection__,
                    DisconenctedCallback = None,
                    ReceiveCallback = __unhandled_received_message__,
                    NewThread = True,
                    IgnoreBasicCommands = False
                )
                asyncio.get_event_loop().run_until_complete(server.Start())

                Servers.append(server)
            else:
                # TODO: More servers in the future!
                raise TypeError("Invalid server type.")
        except Exception as ex:
            logs.PrintLog(logs.CRITICAL, f"[server] Could not start server {len(Servers)}; ignoring this server. Error: {ex}")
            continue
    
    logs.PrintLog(logs.INFO, "[server] All servers started!")

def CloseServer() -> None:
    global CloseServerReason, Servers

    if (CloseServerReason is None):
        CloseServerReason = "Unknown"
    
    for server in Servers:
        asyncio.get_event_loop().run_until_complete(server.Stop())

    print("Closing server.", flush = True)
    logs.WriteLog(logs.INFO, f"[server] Closing server with reason '{CloseServerReason}'.")

    services_manager.OffloadModels(list(config.Configuration["services"].keys()))

config.ReadConfiguration(None, True, True)

try:
    logs.WriteLog(logs.INFO, "[server] Loading configuration...")

    services_manager.Configuration = config.Configuration
    services_manager.keys_manager.Configuration = config.Configuration
except Exception as ex:
    logs.PrintLog(logs.CRITICAL, f"[server] Could not copy configuration in all modules! Error: {ex}")
    exit(1)

if (not os.path.exists(config.Configuration["server_data"]["tos_file"])):
    with open(config.Configuration["server_data"]["tos_file"], "x") as f:
        f.write("# TOS\n\nNo TOS for now.\n")

with open(config.Configuration["server_data"]["tos_file"], "r") as f:
    TOSContent = f.read()

if (not os.path.exists(config.Configuration["server_data"]["temp_dir"])):
    os.mkdir(config.Configuration["server_data"]["temp_dir"])

SERVER_VERSION: int = 170000
Servers: list[Any] = []
PrivateKey: Any | None = None
PublicKey: Any | None = None
CloseServerReason: str | None = None

if (__name__ == "__main__"):
    LoadModels()

    # TODO: Thread for model offloading
    
    asyncio.set_event_loop(asyncio.new_event_loop())
    StartServer()

    interactiveMode = sys.argv.count("--interactive") > 0 or sys.argv.count("-it") > 0

    while (True):
        try:
            if (not interactiveMode):
                time.sleep(0.1)
                continue

            prompt = input(">$ ")
            logs.WriteLog(logs.INFO, f"[server] (interactive mode) Wrote prompt '{prompt}'.")

            if (prompt == "inference"):
                infModelName = input("MODEL NAME >$ ")
                msgSystem = input(f"MESSAGE SYSTEM CONTENT (string) >$ ")
                msgText = input(f"MESSAGE TEXT CONTENT (string) >$ ")
                msgFiles = []

                while (True):
                    msgFilePath = input(f"MESSAGE FILE {len(msgFiles) + 1} PATH (string, [EMPTY]) >$ ").strip()

                    if (len(msgFilePath) == 0):
                        break

                    if (not os.path.exists(msgFilePath)):
                        print(">> File doesn't exists. Ignoring.", flush = True)
                        continue

                    if (
                        msgFilePath.lower().endswith(".png") or
                        msgFilePath.lower().endswith(".jpg") or
                        msgFilePath.lower().endswith(".jpeg") or
                        msgFilePath.lower().endswith(".webp") or
                        msgFilePath.lower().endswith(".gif")
                    ):
                        msgFileType = "image"
                    elif (
                        msgFilePath.lower().endswith(".mp3") or
                        msgFilePath.lower().endswith(".flac") or
                        msgFilePath.lower().endswith(".wav")
                    ):
                        msgFileType = "audio"
                    elif (
                        msgFilePath.lower().endswith(".mp4") or
                        msgFilePath.lower().endswith(".avi") or
                        msgFilePath.lower().endswith(".mkv") or
                        msgFilePath.lower().endswith(".webm")
                    ):
                        msgFileType = "video"
                    else:
                        msgFileType = input(">> Unable to get file type. Please specify file type (string) >$ ")
                        
                    with open(msgFilePath, "rb") as f:
                        msgFiles.append({"type": msgFileType, msgFileType: services_manager.base64.b64encode(f.read()).decode("utf-8")})
                
                infPromptParams = {}

                while (True):
                    paramName = input("PROMPT PARAMETER NAME (string, [EMPTY]) >$ ").strip()
                    
                    if (len(paramName) == 0):
                        break

                    paramValue = input(">> VALUE (int:NUMBER, float:NUMBER, string:TEXT, json:JSON, null) >$ ").strip()

                    try:
                        if (paramValue.lower().startswith("int:")):
                            paramValue = int(paramValue[4:])
                        elif (paramValue.lower().startswith("float:")):
                            paramValue = float(paramValue[6:])
                        elif (paramValue.lower().startswith("string:")):
                            paramValue = paramValue[7:]
                        elif (paramValue.lower().startswith("json:")):
                            paramValue = json.loads(paramValue[5:])
                        elif (paramValue.lower() == "null"):
                            paramValue = None
                        else:
                            raise TypeError("Invalid parameter type.")
                    except Exception as ex:
                        print(f">> Unable to create parameter ({ex}). Ignoring.", flush = True)
                        continue

                    infPromptParams[paramName] = paramValue
                
                infUserParams = {}

                while (True):
                    paramName = input("USER PARAMETER NAME (string, [EMPTY]) >$ ").strip()
                    
                    if (len(paramName) == 0):
                        break

                    paramValue = input(">> VALUE (int:NUMBER, float:NUMBER, string:TEXT, json:JSON, null) >$ ").strip()

                    try:
                        if (paramValue.lower().startswith("int:")):
                            paramValue = int(paramValue[4:])
                        elif (paramValue.lower().startswith("float:")):
                            paramValue = float(paramValue[6:])
                        elif (paramValue.lower().startswith("string:")):
                            paramValue = paramValue[7:]
                        elif (paramValue.lower().startswith("json:")):
                            paramValue = json.loads(paramValue[5:])
                        elif (paramValue.lower() == "null"):
                            paramValue = None
                        else:
                            raise TypeError("Invalid parameter type.")
                    except Exception as ex:
                        print(f">> Unable to create parameter ({ex}). Ignoring.", flush = True)
                        continue

                    infUserParams[paramName] = paramValue

                infKey = services_manager.keys_manager.APIKey(
                    Tokens = 99999,
                    ResetDaily = False,
                    ExpireDate = None,
                    AllowedIPs = ["127.0.0.1"],
                    PrioritizeModels = [infModelName],
                    Groups = None
                )
                
                infGenFiles = []
                infGenWarnings = []
                infGenErrors = []

                print("\n\n---\n\nText:\n", end = "", flush = True)

                try:
                    infGen = services_manager.InferenceModel(
                        infModelName,
                        {"parameters": infPromptParams, "conversation": [
                            {"role": "system", "content": [{"type": "text", "text": msgSystem}]},
                            {"role": "user", "content": msgFiles + [{"type": "text", "text": msgText}]}
                        ]},
                        infUserParams | {
                            "key_info": infKey.__dict__
                        }
                    )

                    for infToken in infGen:
                        print(infToken["response"]["text"], end = "", flush = True)
                        
                        infGenFiles += infToken["response"]["files"]
                        infGenWarnings += infToken["warnings"]
                        infGenErrors += infToken["errors"]
                    
                    for file in infGenFiles:
                        fileID = 1
                        filePath = f"{config.Configuration['server_data']['temp_dir']}/it_inference_file_{file['type']}-{fileID}"

                        while (os.path.exists(filePath)):
                            fileID += 1
                            filePath = f"{config.Configuration['server_data']['temp_dir']}/it_inference_file_{file['type']}-{fileID}"
                        
                        fileData = file[file["type"]]
                        file[file["type"]] = "UNABLE TO CREATE FILE"
                        
                        with open(filePath, "wb") as f:
                            f.write(services_manager.base64.b64decode(fileData))
                        
                        file[file["type"]] = filePath
                except Exception as ex:
                    infGenErrors.append(f"[INFERENCE ERROR] {ex}")
                
                infKey.RemoveFile()
                print(f"\n\n---\n\nFiles: {infGenFiles}\nWarnings: {infGenWarnings}\nErrors: {infGenErrors}", flush = True)
            elif (prompt == "exit" or prompt == "close"):
                raise KeyboardInterrupt()
            elif (prompt == "noninteractive" or prompt == "nit"):
                logs.PrintLog(logs.INFO, "[server] (interactive mode) Closed interactive mode. Changing to default mode.")
                interactiveMode = False
            elif (prompt == "clear"):
                ec = os.system("clear")

                if (ec != 0):
                    logs.PrintLog(logs.ERROR, f"[server] (interactive mode) Could not clear terminal. Exit code {ec}.")
            elif (prompt.startswith("createkey ") or prompt.startswith("crk ")):
                args = (prompt[10:] if (prompt.startswith("createkey")) else prompt[4:]).split(";")
                tokens = 0
                resetDaily = False
                expireDate = None
                allowedIPs = None
                prioritizeModels = []
                groups = None

                try:
                    for arg in args:
                        arg = arg.strip()

                        if (arg.startswith("tokens=")):
                            tokens = float(arg[7:])
                        elif (arg == "resetdaily"):
                            resetDaily = True
                        elif (arg.startswith("expiredate=")):
                            expireDate = json.loads(arg[11:])
                        elif (arg.startswith("allowedips=")):
                            allowedIPs = json.loads(arg[11:])
                        elif (arg.startswith("prioritizemodels=")):
                            prioritizeModels = json.loads(arg[17:])
                        elif (arg.startswith("groups=")):
                            groups = json.loads(arg[7:])
                        else:
                            raise AttributeError(f"Invalid argument '{arg}'.")
                except Exception as ex:
                    print(f"Could not create key, error: {ex}\nTry again.", flush = True)
                    continue

                createdKey = services_manager.keys_manager.APIKey(
                    Tokens = tokens,
                    ResetDaily = resetDaily,
                    ExpireDate = expireDate,
                    AllowedIPs = allowedIPs,
                    PrioritizeModels = prioritizeModels,
                    Groups = groups
                )
                createdKey.SaveToFile()

                print(f"Key created! Key: {createdKey.Key}", flush = True)
            elif (prompt == "help"):
                helpMsg = (
                    f"\033[34mI4.0\033[0m Server (version \033[35m{SERVER_VERSION}\033[0m)\n"
                    "\033[32mCommands:\033[0m\n"
                    "- \033[31minference\033[0m: Tests the inference.\n"
                    "- \033[31mexit\033[0m (alias: \033[31mclose\033[0m): Closes the server.\n"
                    "- \033[31mnoninteractire\033[0m (alias: \033[31mnit\033[0m): Changes from interactive terminal to regular terminal.\n"
                    "- \033[31mcreatekey \033[34m[tokens=FLOAT];[resetdaily];[expiredate=DICT];[allowedips=LIST];[prioritizemodels=LIST];[groups=LIST]\033[0m (alias: \033[31mcrk\033[0m): Creates an API key and prints it.\n"
                    "- \033[31mclear\033[0m: Clears the screen.\n"
                    "- \033[31mhelp\033[0m: Prints this help message.\n\n"
                    "\033[32mSignals:\033[0m\n"
                    "- \033[31mSIGINT\033[0m (alias: \033[31mCtrl+C\033[0m): Closes the server. Works in regular terminal."
                )
                print(helpMsg, flush = True)
            elif (len(prompt.strip()) > 0):
                print("[server] (interactive mode) Command not found.", flush = True)
        except KeyboardInterrupt:
            if (CloseServerReason is None):
                CloseServerReason = "Keyboard interrupt"

            break
        except Exception as ex:
            logs.PrintLog(logs.ERROR, f"[server] Error in the server loop: {ex}")
    
    print("", flush = True)
    CloseServer()