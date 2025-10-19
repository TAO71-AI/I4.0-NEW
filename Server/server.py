try:
    from typing import Any, Iterator
    from concurrent.futures import ThreadPoolExecutor
    import asyncio
    import websockets

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
        f"WebSockets server listening at `{config.Configuration['server_listen']['ws_ip']}:{config.Configuration['server_listen']['ws_port']}`."
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

    loop = asyncio.get_event_loop()
    fullMessage = ""

    try:
        while (True):
            message = await Client.Receive()

            if (message == "ping"):
                continue
            elif (message.endswith("--END--")):
                fullMessage += message[:message.rfind("--END--")]

                with ThreadPoolExecutor() as executor:
                    iterator = await loop.run_in_executor(executor, __process_client__, fullMessage)

                asyncio.create_task(send_items(iterator))
            elif (message == "close"):
                await Client.Close()
                break
            else:
                fullMessage += message
    except Exception as ex:
        logs.WriteLog(logs.ERROR, f"[server] Error while receiving from client ({ex}). The connection will be closed.")

        try:
            Client.Close()
        except Exception as ex:
            logs.WriteLog(logs.WARNING, f"[server] Could not close connection from client ({ex}). Ignoring.")

def __process_client__(Message: str) -> Iterator[str]:
    pass  # TODO

def StartServer() -> None:
    if (config.Configuration["server_listen"]["ws_enabled"]):
        asyncio.run(__start_websockets_server__)

if (__name__ == "__main__"):
    LoadModels()
    StartServer()