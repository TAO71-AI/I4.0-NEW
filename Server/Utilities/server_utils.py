from websockets.asyncio.server import ServerConnection as WS_ServerConnection
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