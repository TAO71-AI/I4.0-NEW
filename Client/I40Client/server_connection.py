from typing import Any, Literal
from collections.abc import AsyncGenerator
from websockets import connect as WS_Connect
from websockets.protocol import State as WS_State
from . import configuration
from . import encryption
import json
import base64
import asyncio

VERSION: int = 170000
TRANSFER_RATE = 8192 * 1024

class ClientSocket():
    def __init__(
        self,
        Type: Literal["websocket"],
        Configuration: configuration.ClientConfiguration
    ) -> None:
        self.__socket__ = None
        self.__socket_type__ = Type  # TODO: More socket types in the future!
        self.__configuration__ = Configuration
        self.__server_public_key_str__ = None
        self.__server_public_key__ = None

        if (Configuration.Encryption_PublicKey is None or Configuration.Encryption_PrivateKey is None):
            self.__private_key__, self.__public_key__ = encryption.GenerateRSAKeys(Size = Configuration.Encryption_RSASize)
        
        _, self.__public_key_str__ = encryption.SaveKeys(None, None, "", self.__public_key__, None)
        self.__public_key_str__ = self.__public_key_str__.decode("utf-8")
    
    def IsConnected(self) -> bool:
        if (self.__socket__ is None):
            return False
        
        if (self.__socket_type__ == "websocket"):
            return self.__socket__.state == WS_State.OPEN
        
        return False

    async def Connect(self, Host: str, Port: int, Secure: bool = False) -> None:
        if (self.__socket_type__ == "websocket"):
            uri = ("wss" if (Secure) else "ws") + f"://{Host}:{Port}"
            self.__socket__ = await WS_Connect(
                uri = uri,
                max_size = TRANSFER_RATE
            )
        
            while (self.__socket__.state == WS_State.CONNECTING):
                await asyncio.sleep(0.1)
        
        await self.__set_server_public_key__()

    async def Close(self) -> None:
        if (self.__socket__ is None):
            return
        
        if (self.__socket_type__ == "websocket"):
            try:
                await self.Send("close")
                await self.__socket__.close()
            except:
                pass
        
        self.__socket__ = None
    
    async def __set_server_public_key__(self) -> None:
        self.__server_public_key_str__ = await self.SendAndReceive("get_public_key")
        _, self.__server_public_key__ = encryption.LoadKeysFromContent(None, "", base64.b64decode(self.__server_public_key_str__))

    async def __send__(self, Data: str) -> None:
        if (not self.IsConnected()):
            raise ConnectionError("Socket not connected.")

        if (self.__socket_type__ == "websocket"):
            await self.__socket__.send(Data)
    
    async def __recv__(self) -> str:
        if (not self.IsConnected()):
            raise ConnectionError("Socket not connected.")
        
        if (self.__socket_type__ == "websocket"):
            recv = await self.__socket__.recv(decode = True)
        
        return recv
    
    async def Send(self, Data: str) -> None:
        chunks = [Data[i:i + TRANSFER_RATE] for i in range(0, len(Data), TRANSFER_RATE)]

        for chunk in chunks:
            await self.__send__(chunk)
        
        await self.__send__("--END--")
    
    async def Receive(self) -> str:
        data = ""

        while (True):
            chunk = await self.__recv__()

            if (chunk == "--END--"):
                break
            
            chunk = chunk[:TRANSFER_RATE]
            data += chunk
        
        return data

    async def SendAndReceive(self, Data: str) -> str:
        await self.Send(Data)
        return await self.Receive()

    async def AdvancedSendAndReceive(
        self,
        ModelName: str,
        Key: str | None = None,
        PromptConversation: list[dict[str, str | dict[str, str | bytes]]] = [],
        PromptParameters: dict[str, Any] = {},
        UserParameters: dict[str, Any] = {},
        Service: str = "inference"
    ) -> AsyncGenerator[dict[str, Any]]:
        if (self.__server_public_key__ is None):
            await self.__set_server_public_key__()

        h = encryption.ParseHash(self.__configuration__.Encryption_Hash)
        data = {
            "hash": self.__configuration__.Encryption_Hash,
            "public_key": self.__public_key_str__,
            "version": VERSION,
            "content": {
                "model_name": ModelName,
                "service": Service,
                "key": self.__configuration__.Service_DefaultAPIKey if (Key is None) else Key,
                "prompt": {
                    "conversation": PromptConversation,
                    "parameters": PromptParameters
                },
                "user_parameters": UserParameters
            }
        }
        data["content"] = encryption.Encrypt(h, self.__server_public_key__, json.dumps(data["content"]))
        await self.Send(json.dumps(data))

        while (True):
            recvData = await self.Receive()
            recvData = json.loads(recvData)
            recvData = encryption.Decrypt(
                encryption.ParseHash(recvData["hash"]),
                self.__private_key__,
                recvData["data"],
                self.__configuration__.Encryption_Threads
            )
            token = json.loads(recvData)

            yield token

            if ("ended" in token and token["ended"]):
                break
    
    async def GetAvailableModels(self) -> list[str]:
        models = None
        gen = self.AdvancedSendAndReceive("", Service = "get_available_models")

        async for token in gen:
            if ("models" in token):
                models = token["models"]
            
            if ("errors" in token and len(token["errors"]) > 0):
                break
        
        if (models is None):
            raise RuntimeError("Could not get models.")
        
        return models
    
    async def GetModelInfo(self, ModelName: str) -> dict[str, Any]:
        modelInfo = None
        gen = self.AdvancedSendAndReceive(ModelName, Service = "get_model_info")

        async for token in gen:
            if ("config" in token):
                modelInfo = token["config"]
            
            if ("errors" in token and len(token["errors"]) > 0):
                break
        
        if (modelInfo is None):
            raise RuntimeError("Could not get model information.")
        
        return modelInfo
    
    async def GetQueueData(self, ModelName: str) -> dict[str, int | float]:
        queueData = None
        gen = self.AdvancedSendAndReceive(ModelName, Service = "get_queue_data")

        async for token in gen:
            if ("queue" in token):
                queueData = token["queue"]
            
            if ("errors" in token and len(token["errors"]) > 0):
                break
        
        if (queueData is None):
            raise RuntimeError("Could not get queue data.")
        
        return queueData
    
    async def CreateAPIKey(
        self,
        Tokens: int = 0,
        ResetDaily: bool = False,
        ExpireDate: dict[str, int] | None = None,
        AllowedIPs: list[str] | None = None,
        PrioritizeModels: list[str] = [],
        Groups: list[str] = []
    ) -> str:
        key = None
        gen = self.AdvancedSendAndReceive("", PromptParameters = {
            "tokens": Tokens,
            "reset_daily": ResetDaily,
            "expire_date": ExpireDate,
            "allowed_ips": AllowedIPs,
            "prioritize_models": PrioritizeModels,
            "groups": Groups
        }, Service = "create_api_key")

        async for token in gen:
            if ("key" in token):
                key = token["key"]
            
            if ("errors" in token and len(token["errors"]) > 0):
                break

        if (key is None):
            raise RuntimeError("Could not create new API key.")
        
        return key
    
    async def DeleteAPIKey(self, Key: str) -> None:
        gen = self.AdvancedSendAndReceive("", PromptParameters = {
            "key": Key
        }, Service = "delete_api_key")

        async for token in gen:
            if ("errors" in token and len(token["errors"]) > 0):
                raise RuntimeError("Could not delete API key.")
       
    async def GetKeyData(self, Key: str) -> dict[str, Any] | None:
        key = False
        gen = self.AdvancedSendAndReceive("", PromptParameters = {
            "key": Key
        }, Service = "get_key_data")

        async for token in gen:
            if ("key" in token):
                key = token["key"]
            
            if ("errors" in token and len(token["errors"]) > 0):
                break

        if (key == False):
            raise RuntimeError("Could not fetch key data.")
        
        return key