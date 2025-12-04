from collections.abc import Awaitable, Callable
from websockets.asyncio.server import ServerConnection as WS_ServerConnection
from websockets.protocol import State as WS_State
import threading
import websockets
import asyncio
import exceptions
import Utilities.logs as logs

class Client():
    DEFAULT_TRANSFER_RATE = 8192

    def __init__(
        self,
        Socket: WS_ServerConnection,
        EndPoint: tuple[str, int]
    ) -> None:
        self.__socket__ = Socket
        self.__endpoint__ = EndPoint
        self.TransferRate = self.DEFAULT_TRANSFER_RATE

        self.__validate_connection_type__()
        logs.WriteLog(logs.INFO, "[server_utils] Connection created.")
    
    def __validate_connection_type__(self) -> None:
        if (
            not isinstance(self.__socket__, WS_ServerConnection)
        ):
            raise exceptions.ConnectionTypeInvalid()
    
    async def __send__(self, Message: str) -> None:
        if (isinstance(self.__socket__, WS_ServerConnection)):
            await self.__socket__.send(Message)
    
    async def __receive__(self) -> str:
        if (isinstance(self.__socket__, WS_ServerConnection)):
            received = await self.__socket__.recv(True)
        
        return received

    async def Receive(self) -> str:
        self.__validate_connection_type__()
        message = ""

        while (True):
            result = await self.__receive__()

            if (result == "--END--"):
                break
            elif (len(result.strip()) == 0):
                await self.Close()

            message += result
        
        return message

    async def Send(self, Message: str) -> None:
        self.__validate_connection_type__()
        chunks = [Message[i:i + self.TransferRate] for i in range(0, len(Message), self.TransferRate)]

        for chunk in chunks:
            await self.__send__(chunk)
        
        await self.__send__("--END--")

    async def Close(self) -> None:
        if (isinstance(self.__socket__, WS_ServerConnection)):
            await self.__socket__.close()
        
        self.__socket__ = None
        self.__endpoint__ = None

        logs.WriteLog(logs.INFO, "[server_utils] Connection closed.")
    
    def GetEndPoint(self) -> tuple[str, int]:
        return self.__endpoint__
    
    def IsConnected(self) -> None:
        return self.__socket__ is not None and self.__socket__.state == WS_State.OPEN

class WebSocketsServer():
    def __init__(
        self,
        ListenIP: str,
        ListenPort: int,
        TransferRate: int,
        ConnectedCallback: Callable[[Client], Awaitable[None]] | None = None,
        DisconenctedCallback: Callable[[Client], Awaitable[None]] | None = None,
        ReceiveCallback: Callable[[Client, str], Awaitable[None]] | None = None,
        NewThread: bool = True,
        IgnoreBasicCommands: bool = False
    ) -> None:
        self.ConnectedCallback = ConnectedCallback
        self.DisconnectedCallback = DisconenctedCallback
        self.ReceiveCallback = ReceiveCallback
        self.IgnoreBasicCommands = IgnoreBasicCommands
        self.__new_thread__ = NewThread
        self.__endpoint__ = (ListenIP, ListenPort)
        self.__transfer_rate__ = TransferRate
        self.__socket__ = None
        self.__started__ = False

        logs.WriteLog(logs.INFO, "[server_utils] New WebSockets server created.")

    def IsStarted(self) -> bool:
        return self.__started__

    async def __on_client_connected__(self, Socket: WS_ServerConnection) -> None:
        c = Client(Socket, Socket.remote_address)
        c.TransferRate = self.__transfer_rate__ * 1024

        try:
            if (self.ConnectedCallback is not None):
                await self.ConnectedCallback(c)

            while (self.__started__ and c.IsConnected()):
                msg = await c.Receive()

                if (not self.IgnoreBasicCommands):
                    if (msg == "ping"):
                        await c.Send("pong")
                        continue
                    elif (msg == "get_transfer_rate"):
                        await c.Send(str(self.__transfer_rate__))
                        continue
                    elif (msg == "close" or len(msg) == 0):
                        break
                
                if (self.ReceiveCallback is not None):
                    await self.ReceiveCallback(c, msg)
        except Exception as ex:
            logs.WriteLog(logs.ERROR, f"[server_utils] Error while receiving from client ({ex}). The connection will be closed.")
        finally:
            try:
                await c.Close()
                
                if (self.DisconnectedCallback is not None):
                    await self.DisconnectedCallback(c)
            except Exception as ex:
                logs.WriteLog(logs.WARNING, f"[server_utils] Could not close connection from client ({ex}). Ignoring.")
    
    async def __start_server__(self) -> None:
        if (self.IsStarted()):
            logs.WriteLog(logs.INFO, "[server_utils] Server already started! Restarting.")
            self.__stop__()

        try:
            self.__socket__ = await websockets.serve(
                handler = self.__on_client_connected__,
                host = self.__endpoint__[0],
                port = self.__endpoint__[1],
                max_size = self.__transfer_rate__ * 1024 + 1
            )
            self.__started__ = True
            
            logs.PrintLog(logs.INFO, f"[server_utils] (websockets) Server listening at `{self.__endpoint__[0]}:{self.__endpoint__[1]}`.")
            
            try:
                while (self.IsStarted()):
                    await asyncio.sleep(0.1)
            finally:
                await self.Stop()
        except Exception as ex:
            logs.PrintLog(logs.ERROR, f"[server_utils] Could not start WebSockets server at `{self.__endpoint__[0]}:{self.__endpoint__[1]}`: {ex}")
    
    def __start_server_new_thread__(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.__start_server__())
        loop.close()

    async def Start(self) -> None:
        if (self.__new_thread__):
            thread = threading.Thread(target = self.__start_server_new_thread__, args = ())
            thread.start()
        else:
            await self.__start_server__()

    async def __stop__(self) -> None:
        if (not self.IsStarted()):
            return
        
        try:
            if (self.__socket__ is not None):
                self.__socket__.close(True)
                await self.__socket__.wait_closed()
        except Exception as ex:
            logs.PrintLog(logs.ERROR, f"[server_utils] Could not fully close WebSockets server: {ex}")
        
        self.__started__ = False
    
    async def Stop(self) -> None:
        if (not self.IsStarted()):
            return

        self.__started__ = False