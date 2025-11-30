try:
    from typing import Any
    from collections.abc import Generator
    from concurrent.futures import ThreadPoolExecutor
    import os
    import sys
    import json
    import time
    import random
    import threading
    import asyncio
    import websockets

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

try:
    logs.WriteLog(logs.INFO, "[server] Loading configuration...")

    services_manager.Configuration = config.Configuration
    services_manager.keys_manager.Configuration = config.Configuration
except Exception as ex:
    logs.PrintLog(logs.CRITICAL, f"[server] Could not copy configuration in all modules! Error: {ex}")
    exit(1)

def LoadModels() -> None:
    try:
        logs.PrintLog(logs.INFO, "[server] Loading all modules...")
        services_manager.LoadModels(config.Configuration["services"])
    except Exception as ex:
        logs.PrintLog(logs.CRITICAL, f"[server] Could not load models. Error: {ex}")
        raise RuntimeError(f"Could not load models: {ex}")

def __start_websockets_server__() -> None:
    async def __start__() -> None:
        global ServerStarted

        server = await websockets.serve(
            handler = __on_ws_client_connected__,
            host = config.Configuration["server_listen"]["ws_ip"],
            port = config.Configuration["server_listen"]["ws_port"],
            max_size = config.Configuration["server_transfer_rate"]
        )
        logs.PrintLog(
            logs.INFO,
            f"[server] WebSockets server listening at `{config.Configuration['server_listen']['ws_ip']}:{config.Configuration['server_listen']['ws_port']}`."
        )
        
        try:
            while (ServerStarted):
                await asyncio.sleep(0.1)
        finally:
            server.close(True)
            await server.wait_closed()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(__start__())
    finally:
        loop.close()

async def __on_ws_client_connected__(ClientWS: Any) -> None:
    client = server_utils.Client(ClientWS, ClientWS.remote_address)
    await __on_client_connected__(client)

async def __on_client_connected__(Client: server_utils.Client) -> None:
    global TOSContent, ServerStarted

    async def send_items(Gen: Generator[dict[str, Any]]) -> None:
        for item in Gen:
            if (not ServerStarted):
                return

            if (config.Configuration["server_encryption"]["force_response_hash"] is None):
                responseHash = item["_hash"]
            else:
                responseHash = config.Configuration["server_encryption"]["force_response_hash"]
            
            responseHashParsed = encryption.ParseHash(responseHash)
            responsePublicKey = None if ("_public_key" not in item or item["_public_key"] is None) else encryption.LoadKeysFromContent(None, "", item["_public_key"])[1]
            item2 = {}

            for k, v in item.items():
                if (k.startswith("_")):
                    continue

                item2[k] = v
            
            if (
                config.Configuration["server_encryption"]["obfuscate"] and
                responseHashParsed is not None and
                responsePublicKey is not None
            ):
                item2["obfuscate"] = "a" * random.randint(5, 25)

            if (responsePublicKey is None):
                encrItem = json.dumps(item2)
            else:
                encrItem = encryption.Encrypt(
                    responseHashParsed,
                    responsePublicKey,
                    json.dumps(item2)
                )
            
            resItem = {
                "data": encrItem,
                "hash": responseHash
            }
            resItem = json.dumps(resItem)

            await Client.Send(resItem)
            await asyncio.sleep(0)

    logs.WriteLog(logs.INFO, f"[server] Connected client from {Client.GetEndPoint()}.")
    Client.TransferRate = config.Configuration["server_transfer_rate"] * 1024

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
        return

    loop = asyncio.get_event_loop()
    tasks = []
    message = None

    try:
        while (ServerStarted):
            message = await Client.Receive()

            # Process basic server commands
            if (message == "ping"):
                await Client.Send("pong")
            elif (message == "get_transfer_rate"):
                transferRate = config.Configuration["server_transfer_rate"]
                await Client.Send(str(transferRate))
            elif (message == "get_public_key"):
                _, publicBytes = encryption.SaveKeys(None, None, "", PublicKey, None)
                await Client.Send(publicBytes.decode("utf-8"))
            elif (message == "get_tos"):
                await Client.Send(TOSContent)
            elif (message == "close"):
                break
            else:
                # Process other commands
                with ThreadPoolExecutor() as executor:
                    generator = await loop.run_in_executor(executor, __process_client__, message)

                tasks.append(loop.create_task(send_items(generator)))
    except Exception as ex:
        logs.WriteLog(logs.ERROR, f"[server] Error while receiving from client ({ex}). The connection will be closed.")
    finally:
        try:
            await Client.Close()
        except Exception as ex:
            logs.WriteLog(logs.WARNING, f"[server] Could not close connection from client ({ex}). Ignoring.")
        
        for task in tasks:
            task.cancel()
        
        if (tasks):
            await asyncio.gather(*tasks, return_exceptions = True)

def __process_client__(Message: str) -> Generator[dict[str, Any]]:
    global ServerVersion

    try:
        message = json.loads(Message)
        messageContent = message["content"]
        messageHash = message["hash"]
        messagePublicKey = message["public_key"]
        clientVersion = message["version"] if ("version" in message) else -1

        if (config.Configuration["server_client_version"]["min"] is None):
            serverMinVersion = ServerVersion
        else:
            serverMinVersion = config.Configuration["server_client_version"]["min"]
        
        if (config.Configuration["server_client_version"]["max"] is None):
            serverMaxVersion = ServerVersion
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
            service = content["service"]
            key = content["key"] if ("key" in content) else ""

            # TODO
        except Exception as ex:
            yield {
                "errors": [f"Error processing message ({ex})."],
                "_hash": messageHash,
                "_public_key": messagePublicKey
            }
    except Exception as ex:
        yield {
            "errors": [f"Error decrypting message ({ex})."],
            "_hash": "none",
            "_public_key": None
        }

def StartServer() -> None:
    global PrivateKey, PublicKey, ServerStarted

    if (
        len(config.Configuration["server_encryption"]["public_key_file"].strip()) == 0 or
        len(config.Configuration["server_encryption"]["private_key_file"].strip()) == 0 or
        not os.path.exists(config.Configuration["server_encryption"]["public_key_file"]) or
        not os.path.exists(config.Configuration["server_encryption"]["private_key_file"])
    ):
        PrivateKey, PublicKey = encryption.GenerateRSAKeys()

        if (
            not os.path.exists(config.Configuration["server_encryption"]["public_key_file"]) or
            not os.path.exists(config.Configuration["server_encryption"]["private_key_file"])
        ):
            encryption.SaveKeys(
                PrivateKey,
                config.Configuration["server_encryption"]["private_key_file"],
                config.Configuration["server_encryption"]["private_key_password"],
                PublicKey,
                config.Configuration["server_encryption"]["public_key_file"]
            )
    else:
        PrivateKey, PublicKey = encryption.LoadKeysFromFile(
            config.Configuration["server_encryption"]["private_key_file"],
            config.Configuration["server_encryption"]["private_key_password"],
            config.Configuration["server_encryption"]["public_key_file"]
        )
    
    if (config.Configuration["server_transfer_rate"] < 1 or config.Configuration["server_transfer_rate"] > 8192):
        newServerTransferRate = max(1, min(config.Configuration["server_transfer_rate"], 8192))

        logs.PrintLog(logs.WARNING, f"[server] Server transfer rate is too low or too high. Adjusting to {newServerTransferRate}.")
        config.Configuration["server_transfer_rate"] = newServerTransferRate

    ServerStarted = True

    if (config.Configuration["server_listen"]["ws_enabled"]):
        wsServerThread = threading.Thread(target = __start_websockets_server__)
        wsServerThread.start()

def CloseServer() -> None:
    global CloseServerReason, ServerStarted

    if (CloseServerReason is None):
        CloseServerReason = "Unknown"

    print("Closing server.", flush = True)
    logs.WriteLog(logs.INFO, f"[server] Closing server with reason '{CloseServerReason}'.")

    ServerStarted = False

    services_manager.OffloadModels(list(config.Configuration["services"].keys()))
    #exit(0)

if (not os.path.exists(config.Configuration["server_tos_file"])):
    with open(config.Configuration["server_tos_file"], "x") as f:
        f.write("# TOS\n\nNo TOS for now.\n")

with open(config.Configuration["server_tos_file"], "r") as f:
    TOSContent = f.read()

if (not os.path.exists(config.Configuration["server_temp_dir"])):
    os.mkdir(config.Configuration["server_temp_dir"])

PrivateKey: Any | None = None
PublicKey: Any | None = None
CloseServerReason: str | None = None
ServerStarted: bool = False
ServerVersion: int = 170000

if (__name__ == "__main__"):
    if (os.path.exists("./latest.txt")):
        with open("./latest.txt", "w") as f:
            f.write("")

    LoadModels()

    # TODO: Thread for model offloading
    
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
                infMsgs = []

                while (True):
                    msgRole = input(f"MESSAGE {len(infMsgs) + 1} ROLE (user, assistant, custom, [EMPTY]) >$ ").strip().lower()
                    msgCRole = None

                    if (msgRole == "user"):
                        msgRole = services_manager.conv.ROLE_USER
                    elif (msgRole == "assistant"):
                        msgRole = services_manager.conv.ROLE_ASSISTANT
                    elif (msgRole == "custom"):
                        msgRole = services_manager.conv.ROLE_CUSTOM
                        msgCRole = input(">> CUSTOM ROLE NAME >$ ")
                    elif (len(msgRole) == 0):
                        break
                    else:
                        print(">> Invalid message role. Ignoring.", flush = True)
                        continue

                    msgText = input(f"MESSAGE {len(infMsgs) + 1} TEXT CONTENT (string) >$ ")
                    msgFiles = []

                    while (True):
                        msgFilePath = input(f"MESSAGE {len(infMsgs) + 1} FILE {len(msgFiles) + 1} PATH (string, [EMPTY]) >$ ").strip()

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
                            msgFiles.append({"type": msgFileType, "data": services_manager.base64.b64encode(f.read()).decode("utf-8")})

                    infMsgs.append(services_manager.conv.Message(msgRole, msgText, msgFiles, msgCRole))
                
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

                infConv = services_manager.conv.Conversation("SERVER_inf", infMsgs)
                infConv.DeleteFromDB()

                infKey = services_manager.keys_manager.APIKey(9999, False, None, ["127.0.0.1"], [], [])
                
                infGenFiles = []
                infGenWarnings = []
                infGenErrors = []

                print("\n\n---\n\nText:\n", end = "", flush = True)

                try:
                    infGen = services_manager.InferenceModel(
                        infModelName,
                        {} | infPromptParams,
                        {
                            "conversation_name": "SERVER_inf",
                            "key_info": infKey.ToDict()
                        } | infUserParams
                    )

                    for infToken in infGen:
                        print(infToken["text"] if ("text" in infToken) else "", end = "", flush = True)
                        
                        infGenFiles += infToken["files"] if ("files" in infToken) else []
                        infGenWarnings += infToken["warnings"] if ("warnings" in infToken) else []
                        infGenErrors += infToken["errors"] if ("errors" in infToken) else []
                    
                    for file in infGenFiles:
                        fileID = 1
                        filePath = f"{config.Configuration['server_temp_dir']}/it_inference_file_{file['type']}-{fileID}"

                        while (os.path.exists(filePath)):
                            fileID += 1
                            filePath = f"{config.Configuration['server_temp_dir']}/it_inference_file_{file['type']}-{fileID}"
                        
                        fileData = file["data"]
                        file["data"] = "UNABLE TO CREATE FILE"
                        
                        with open(filePath, "wb") as f:
                            f.write(services_manager.base64.b64decode(fileData))
                        
                        file["data"] = filePath
                except Exception as ex:
                    infGenErrors.append(f"[INFERENCE ERROR] {ex}")

                    import traceback
                    traceback.print_exception(ex)
                
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
            elif (len(prompt.strip()) > 0):
                print("[server] (interactive mode) Command not found.", flush = True)
        except KeyboardInterrupt:
            if (CloseServerReason is None):
                CloseServerReason = "Keyboard interrupt"

            break
    
    print("", flush = True)
    CloseServer()