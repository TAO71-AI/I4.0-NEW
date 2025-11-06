try:
    from typing import Any, Iterator
    from concurrent.futures import ThreadPoolExecutor
    import os
    import sys
    import json
    import time
    import asyncio
    import websockets

    import encryption
    import services_manager
    import Utilities.logs as logs
    import Utilities.server_utils as server_utils
    import Configuration.config as config
except Exception as ex:
    print(f"Could not load server modules. Error: {ex}\nPlease make sure all of the requirements are installed.", flush = True)
    exit(1)

try:
    logs.WriteLog(logs.INFO, "[server] Loading configuration...")

    services_manager.Configuration = config.Configuration
except Exception as ex:
    logs.PrintLog(logs.CRITICAL, f"[server] Could not copy configuration in all modules! Error: {ex}")
    exit(1)

def LoadModels() -> None:
    try:
        logs.PrintLog(logs.INFO, "[server] Loading all modules...")
        services_manager.LoadModels(config.Configuration["services"])
    except Exception as ex:
        logs.PrintLog(logs.ERROR, f"[server] Could not load models. Error: {ex}")
        raise RuntimeError(f"Could not load models: {ex}")

async def __start_websockets_server__() -> None:
    server = await websockets.serve(
        __on_ws_client_connected__,
        config.Configuration["server_listen"]["ws_ip"],
        config.Configuration["server_listen"]["ws_port"]
    )

    logs.PrintLog(
        logs.INFO,
        f"[server] WebSockets server listening at `{config.Configuration['server_listen']['ws_ip']}:{config.Configuration['server_listen']['ws_port']}`."
    )
    await server.wait_closed()

async def __on_ws_client_connected__(ClientWS: Any) -> None:
    client = server_utils.Client(ClientWS, ClientWS.remote_address)
    await __on_client_connected__(client)

async def __on_client_connected__(Client: server_utils.Client) -> None:
    async def send_items(Iterator: Iterator[str]) -> None:
        for item in Iterator:
            await Client.Send(item)
            await asyncio.sleep(0)

    logs.WriteLog(logs.INFO, f"[server] Connected client from {Client.GetEndPoint()}.")
    Client.TransferRate = config.Configuration["server_transfer_rate"] * 1024

    loop = asyncio.get_event_loop()

    try:
        while (True):
            message = await Client.Receive()

            if (message == "ping"):
                continue
            elif (message == "get_transfer_rate"):
                transferRate = config.Configuration["server_transfer_rate"]
                await Client.Send(str(transferRate))
            elif (message == "get_public_key"):
                _, publicBytes = encryption.SaveKeys(None, None, "", PublicKey, None)
                await Client.Send(publicBytes.decode("utf-8"))
            elif (message == "close"):
                await Client.Close()
                break
            else:
                with ThreadPoolExecutor() as executor:
                    iterator = await loop.run_in_executor(executor, __process_client__, message)

                asyncio.create_task(send_items(iterator))
    except Exception as ex:
        logs.WriteLog(logs.ERROR, f"[server] Error while receiving from client ({ex}). The connection will be closed.")

        try:
            await Client.Close()
        except Exception as ex:
            logs.WriteLog(logs.WARNING, f"[server] Could not close connection from client ({ex}). Ignoring.")

def __process_client__(Message: str) -> Iterator[str]:
    try:
        message = json.loads(Message)
        content = message["content"]
        clientHash = message["hash"]
        clientHash = encryption.ParseHash(clientHash)

        content = encryption.Decrypt(
            clientHash,
            PrivateKey,
            content,
            config.Configuration["server_encryption"]["decryption_threads"]
        )
    except Exception as ex:
        yield json.dumps({
            "errors": [f"Error decrypting message ({ex})."],
            "hash": None
        })
        return
    
    pass  # TODO

def StartServer() -> None:
    global PrivateKey, PublicKey

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
        PrivateKey, PublicKey = encryption.LoadKeys(
            config.Configuration["server_encryption"]["private_key_file"],
            config.Configuration["server_encryption"]["private_key_password"],
            config.Configuration["server_encryption"]["public_key_file"]
        )
    
    if (config.Configuration["server_transfer_rate"] < 1 or config.Configuration["server_transfer_rate"] > 8192):
        newServerTransferRate = max(1, min(config.Configuration["server_transfer_rate"], 8192))

        logs.PrintLog(logs.WARNING, f"[server] Server transfer rate is too low or too high. Adjusting to {newServerTransferRate}.")
        config.Configuration["server_transfer_rate"] = newServerTransferRate

    if (config.Configuration["server_listen"]["ws_enabled"]):
        asyncio.run(__start_websockets_server__())

def CloseServer() -> None:
    logs.PrintLog(logs.INFO, "[server] Closing server.")
    services_manager.OffloadModels(list(config.Configuration["services"].keys()))
    
    exit(0)

if (__name__ == "__main__"):
    if (os.path.exists("./latest.txt")):
        with open("./latest.txt", "w") as f:
            f.write("")

    PrivateKey = None
    PublicKey = None

    LoadModels()
    
    try:
        StartServer()
    except KeyboardInterrupt:
        CloseServer()

    interactiveMode = sys.argv.count("--interactive") > 0 or sys.argv.count("-it") > 0

    while (True):
        if (interactiveMode):
            prompt = input(">$ ")
        else:
            time.sleep(0.1)