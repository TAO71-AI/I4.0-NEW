from typing import Any, Self
import os
import random
import datetime
import json
import Utilities.logs as logs

Configuration: dict[str, Any] = {}
__busy__: list[str] = []

class APIKey():
    VERSION = 0

    def __init__(
        self,
        Tokens: int,
        ResetDaily: bool = False,
        ExpireDate: dict[str, int] | datetime.datetime | None = None,
        AllowedIPs: list[str] | None = None,
        PrioritizeModels: list[str] = [],
        Groups: list[str] | None = None
    ):
        logs.WriteLog(logs.INFO, "[keys_manager] Creating API key.")

        if (not isinstance(Configuration["server_api"]["min_length"], int) or Configuration["server_api"]["min_length"] < 16):
            raise ValueError("API key min length must be an integer of at least 16.")
        
        minLength = Configuration["server_api"]["min_length"]
        maxLength = Configuration["server_api"]["max_length"]

        if (minLength < 16):
            logs.WriteLog(logs.WARNING, "[keys_manager] Min length < 16. Setting to 16.")
            minLength = 16

        if (maxLength is None):
            maxLength = minLength

        if (maxLength > 128):
            logs.WriteLog(logs.WARNING, "[keys_manager] Max length > 128. This could cause troubles. Setting to 128.")
            maxLength = 128
        
        if (minLength > maxLength):
            logs.WriteLog(logs.WARNING, f"[keys_manager] Min length ({minLength}) > max length ({maxLength}). Setting to {maxLength}.")
            minLength = maxLength
        
        if (minLength == maxLength):
            length = minLength
        else:
            length = random.randint(minLength, maxLength)

        date = datetime.datetime.now()
        chars = "abcdefghijplnmopqrstuvwxyz"
        chars += chars.upper()
        chars += "0123456789!@#$%&()=[]?-_.:,;<>*+"

        chars = list(chars)
        random.shuffle(chars)
        chars = "".join(chars)

        self.__version__ = self.VERSION
        self.Key = "".join([chars[random.randint(0, len(chars) - 1)] for _ in range(length)])
        self.Tokens = Tokens
        self.CreationDate = {
            "day": date.day,
            "month": date.month,
            "year": date.year,
            "hour": date.hour,
            "minute": date.minute
        }
        self.ExpireDate = {
            "day": ExpireDate.day,
            "month": ExpireDate.month,
            "year": ExpireDate.year,
            "hour": ExpireDate.hour,
            "minute": ExpireDate.minute
        } if (isinstance(ExpireDate, datetime.datetime)) else {
            "day": ExpireDate["day"] if ("day" in ExpireDate) else date.day,
            "month": ExpireDate["month"] if ("month" in ExpireDate) else date.month,
            "year": ExpireDate["year"] if ("year" in ExpireDate) else date.year,
            "hour": ExpireDate["hour"] if ("hour" in ExpireDate) else date.hour,
            "minute": ExpireDate["minute"] if ("minute" in ExpireDate) else date.minute
        } if (isinstance(ExpireDate, dict)) else None
        self.DailyReset = {
            "reset": ResetDaily,
            "tokens": Tokens
        }
        self.AllowedIPs = AllowedIPs
        self.PrioritizeModels = PrioritizeModels
        self.Groups = Configuration["server_api"]["default_groups"] if (Groups is None) else Groups
    
    def IsAdmin(self) -> None:
        for group in self.Groups:
            if (group in Configuration["server_api"]["admin_groups"]):
                return True
        
        return False
    
    def SaveToFile(self) -> None:
        self.__wait__(self.Key)
        __busy__.append(self.Key)

        try:
            if (not os.path.exists(f"{Configuration['server_data']['keys_dir']}/")):
                os.mkdir(f"{Configuration['server_data']['keys_dir']}/")
            
            fileName = self.Key

            with open(f"{Configuration['server_data']['keys_dir']}/{fileName}.json", "w" if (self.KeyFileExists(self.Key)) else "x") as f:
                f.write(json.dumps(self.__dict__))
        finally:
            __busy__.remove(self.Key)
    
    def RemoveFile(self) -> None:
        self.__wait__(self.Key)
        __busy__.append(self.Key)

        try:
            if (self.KeyFileExists(self.Key)):
                os.remove(f"{Configuration['server_data']['keys_dir']}/{self.Key}.json")
        finally:
            __busy__.remove(self.Key)

    @staticmethod
    def __wait__(Key: str) -> None:
        while (Key in __busy__):
            raise Exception("ª")
    
    @staticmethod
    def KeyFileExists(Key: str) -> bool:
        return os.path.exists(f"{Configuration['server_data']['keys_dir']}/{Key}.json")
    
    @classmethod
    def LoadFromFile(cls, Key: str) -> Self | None:
        cls.__wait__(Key)
        __busy__.append(Key)
        
        try:
            if (os.path.exists(f"{Configuration['server_data']['keys_dir']}/{Key}.json")):
                with open(f"{Configuration['server_data']['keys_dir']}/{Key}.json", "r") as f:
                    instance = cls.__from_dict__(json.loads(f.read()))
            else:
                instance = None
        finally:
            __busy__.remove(Key)
        
        return instance

    @classmethod
    def __from_dict__(cls, Dictionary: dict[str, Any]) -> Self:
        instance = cls.__new__(cls)

        for k, v in Dictionary.items():
            setattr(instance, k, v)
        
        if (instance.__version__ != cls.VERSION):
            logs.PrintLog(logs.WARNING, "[keys_manager] API key version is older or newer than the server version. This might cause errors.")
        
        return instance