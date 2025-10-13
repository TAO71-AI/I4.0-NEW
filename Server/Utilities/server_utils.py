from websockets.asyncio.server import ServerConnection as WS_ServerConnection
import exceptions
import Utilities.logs as logs

class Client():
    def __init__(
        self,
        Socket: WS_ServerConnection,
        EndPoint: tuple[str, int]
    ) -> None:
        self.__socket__ = Socket
        self.__endpoint__ = EndPoint

        self.__validate_connection_type__()
        logs.WriteLog(logs.INFO, "[server_utils] Connection created.")
    
    def __validate_connection_type__(self) -> None:
        if (
            not isinstance(self.__socket__, WS_ServerConnection)
        ):
            raise exceptions.ConnectionTypeInvalid()

    async def Receive(self) -> str:
        self.__validate_connection_type__()

        if (isinstance(self.__socket__, WS_ServerConnection)):
            result = await self.__socket__.recv()
        
        logs.WriteLog(logs.INFO, "[server_utils] Received a message from a client.")
        return result

    async def Send(self, Message: str) -> None:
        if (isinstance(self.__socket__, WS_ServerConnection)):
            await self.__socket__.send(Message)

    async def Close(self) -> None:
        if (isinstance(self.__socket__, WS_ServerConnection)):
            await self.__socket__.close()
        
        self.__socket__ = None
        self.__endpoint__ = None

        logs.WriteLog(logs.INFO, "[server_utils] Connection closed.")
    
    def GetEndPoint(self) -> tuple[str, int]:
        return self.__endpoint__