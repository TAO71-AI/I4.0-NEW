from typing import Self
import base64
import copy
import Utilities.logs as logs

ROLE_USER: int = 0
ROLE_ASSISTANT: int = 1
ROLE_CUSTOM: int = 2

class Message():
    def __init__(self, Role: int, Text: str | None = None, Files: list[dict[str, str | bytes]] | None = None, CustomRole: str | None = None) -> None:
        """
        Create a message.

        Args:
            Role (int): Role of the message.
            Text (str | None): Text of the message. Empty if None.
            Files (list[str, str | bytes] | None): Files of the message. Empty if None.
            CustomRole (str | None): Custom role. Used if the role is set to ROLE_CUSTOM.
        
        Returns:
            None
        """
        logs.WriteLog(logs.INFO, "[messages] Message created.")

        self.__role__ = Role
        self.__text__ = Text if (Text is not None) else ""
        self.__files__ = Files if (Files is not None) else []
        self.__custom_role__ = CustomRole

    def EditMessage(self, Text: str | None = None, Files: list[dict[str, str | bytes]] | None = None) -> None:
        """
        Edit a message.

        Args:
            Text (str | None): New text of the message. Don't edit if None.
            Files (list[dict[str, str | bytes]] | None): New files of the message. Don't edit if None.

        Returns:
            None
        """
        logs.WriteLog(logs.INFO, "[messages] Message edited.")

        self.__text__ = Text if (Text is not None) else self.__text__
        self.__files__ = Files if (Files is not None) else self.__files__
    
    def GetFiles(self) -> list[dict[str, str]]:
        """
        Get the files of the message. Data converted to base64.

        Returns:
            list[dict[str, str]]
        """
        logs.WriteLog(logs.INFO, "[messages] Getting files of a message.")
        files = []

        for file in self.__files__:
            if (isinstance(file["data"], bytes)):
                fileData = base64.b64encode(file["data"]).decode("utf-8")
            else:
                fileData = file["data"]
            
            files.append({"type": file["type"], "data": fileData})
        
        return files
    
    def GetText(self) -> str:
        """
        Get the text of the message.

        Returns:
            str
        """
        logs.WriteLog(logs.INFO, "[messages] Getting text of a message.")
        return self.__text__

    def GetRole(self) -> int | str | None:
        """
        Get the role of the message.

        Returns:
            int
        """
        logs.WriteLog(logs.INFO, "[messages] Getting role of a message.")
        return self.__role__ if (self.__role__ != ROLE_CUSTOM) else self.__custom_role__
    
    def GetMessageContent(self) -> dict[str, str | list[dict[str, str]]]:
        """
        Get the content of the message.
        Example:
        ```json
        "role": "user | assistant | system | custom",
        "content": [
            {"type": "image", "image": "base64 image data"},
            {"type": "audio", "audio": "base64 audio data"},
            {"type": "video", "video": "base64 video data"},
            ...
            {"type": "text", "text": "message text"}
        ]
        ```

        If the message role is ROLE_CUSTOM the role will be the one specified.
        If no custom role is specified, it will be "other" by default.

        Returns:
            dict[str, str | list[dict[str, str]]]
        """
        logs.WriteLog(logs.INFO, "[messages] Getting content of a message.")
        msg = {"content": []}

        if (self.__role__ == ROLE_USER):
            msg["role"] = "user"
        elif (self.__role__ == ROLE_ASSISTANT):
            msg["role"] = "assistant"
        elif (self.__role__ == ROLE_CUSTOM):
            msg["role"] = self.__custom_role__ if (self.__custom_role__ is not None) else "other"
        else:
            raise AttributeError("[messages] Invalid message role.")

        for file in self.__files__:
            if ("type" not in file or "data" not in file):
                raise AttributeError("[messages] Invalid file.")
            
            if (isinstance(file["data"], bytes)):
                fileData = base64.b64encode(file["data"]).decode("utf-8")
            else:
                fileData = file["data"]
            
            msg["content"].append({"type": file["type"], file["type"]: fileData})
        
        msg["content"].append({"type": "text", "text": self.__text__})
        return msg

class Conversation():
    def __init__(self, Name: str, Messages: list[Message] | None = None, CustomRole: str | None = None) -> None:
        """
        Create a conversation.

        Args:
            Name (str): Name of the conversation.
            Messages (list[Message] | None): Messages of the conversation. Empty if None.
            CustomRole (str | None): Custom role. Used if any of the messages' role is set to ROLE_CUSTOM.
        
        Returns:
            None
        """
        logs.WriteLog(logs.INFO, "[messages] Conversation created.")

        self.__name__ = Name
        self.__messages__ = Messages if (Messages is not None) else []
        self.__custom_role__ = CustomRole
    
    def AppendMessage(self, Msg: Message) -> None:
        """
        Add a message to the conversation.

        Args:
            Msg (Message): Message to add.
        
        Returns:
            None
        """
        logs.WriteLog(logs.INFO, "[messages] Added a message to the conversation.")

        if (self.__custom_role__ is not None and Msg.__custom_role__ is None):
            Msg.__custom_role__ = self.__custom_role__

        self.__messages__.append(Msg)
    
    def RemoveMessage(self, Msg: Message | int) -> None:
        """
        Remove a message from the conversation.

        Args:
            Msg (Message | int): Message or index of the message to remove.
        
        Returns:
            None
        """
        logs.WriteLog(logs.INFO, "[messages] Removed a message from the conversation.")

        if (isinstance(Msg, int)):
            self.__messages__.remove(self.__messages__.index(Msg))
        else:
            self.__messages__.remove(Msg)

    def GetConversation(self, ReturnAsMessage: bool = False) -> list[dict[str, str | list[dict[str, str]]] | Message]:
        """
        Get the conversation.

        Args:
            ReturnAsMessage (bool): Return a list of the Message class.
        
        Returns:
            list[dict[str, str | list[dict[str, str]]] | Message]
        """
        logs.WriteLog(logs.INFO, f"[messages] Getting conversation{' as message' if (ReturnAsMessage) else ''}.")

        for msg in self.__messages__:
            if (self.__custom_role__ is not None and msg.__custom_role__ is None):
                msg.__custom_role__ = self.__custom_role__

        if (ReturnAsMessage):
            return copy.deepcopy(self.__messages__)
        
        return [msg.GetMessageContent() for msg in self.__messages__]
    
    def __create_in_db__(self) -> None:
        """
        Create the conversation in the database.
        The conversation must not exist in the database.

        **NOTE: This function should only be called by this class.**

        Returns:
            None
        """
        pass  # TODO

    def __update_in_db__(self) -> None:
        """
        Update the conversation in the database.
        The conversation must exist in the database.

        **NOTE: This function should only be called by this class.**

        Returns:
            None
        """
        pass  # TODO
    
    def UploadToDB(self) -> None:
        """
        Upload the conversation to the database.

        Returns:
            None
        """
        pass  # TODO

    def DownloadFromDB(self) -> None:
        """
        Download the conversation from the database.

        Returns:
            None
        """
        if (not self.ExistsInDB()):
            raise FileNotFoundError("Conversation doesn't exist in database. Unable to download.")

        pass  # TODO

    def DeleteFromDB(self) -> None:
        if (not self.ExistsInDB()):
            return
        
        pass  # TODO

    def ExistsInDB(self) -> bool:
        """
        Checks if the conversation exists in the database.

        Returns:
            bool
        """
        return False  # TODO

    @staticmethod
    def CreateConversationFromDB(Name: str, CreateIfNotExists: bool = False) -> Self:
        """
        Create a conversation by downloading it from the database.

        Args:
            Name (str): Name of the conversation in the server.
            CreateIfNotExists (bool): Create the conversation if it doesn't exists in the database.
        
        Returns:
            Conversation
        """
        conv = Conversation(Name, None)
        
        try:
            conv.DownloadFromDB()
        except FileNotFoundError as ex:
            if (not CreateIfNotExists):
                raise ex

        return conv