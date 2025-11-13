from typing import Any, Self
import random
import copy
import datetime
import database_client as db
import Utilities.logs as logs

Configuration: dict[str, Any] = {}

class APIKey():
    VERSION = 0

    def __init__(
        self: Self,
        Tokens: int,
        ResetDaily: bool = False,
        ExpireDate: dict[str, int] | datetime.datetime | None = None,
        AllowedIPs: list[str] | None = None,
        PrioritizeModels: list[str] = [],
        Groups: list[str] | None = None
    ):
        logs.WriteLog(logs.INFO, "[keys_manager] Creating API key.")

        if (not isinstance(Configuration["server_api"]["min_length"]) or Configuration["server_api"]["min_length"] < 16):
            raise ValueError("API key min length must be 16.")
        
        minLength = Configuration["server_api"]["min_length"]
        maxLength = Configuration["server_api"]["max_length"]

        if (maxLength is None):
            maxLength = minLength
        
        if (minLength == maxLength):
            length = minLength
        else:
            length = random.randint(minLength, maxLength)

        date = datetime.datetime.now()
        chars = "abcdefghijplnmopqrstuvwxyz"
        chars += chars.upper()
        chars += "0123456789!@#$%&/()=[]?-_.:,;<>*+"

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
    
    def IsAdmin(self: Self) -> None:
        for group in self.Groups:
            if (group in Configuration["server_api"]["admin_groups"]):
                return True
        
        return False
    
    def SaveInDatabase(self: Self) -> None:
        pass  # TODO

    @staticmethod
    def CreateFromDatabase(Key: str) -> Self:
        pass  # TODO

    @staticmethod
    def GetAllFromDatabase() -> list[Self]:
        pass  # TODO
    
    @classmethod
    def FromDict(cls: Self, Dictionary: dict[str, Any]) -> Self:
        instance = cls.__new__(cls)

        for k, v in Dictionary.items():
            setattr(instance, k, v)
        
        if (instance.__version__ != cls.VERSION):
            logs.PrintLog(logs.WARNING, "[keys_manager] API key version is older or newer than the server version. This might cause errors.")
        
        return instance
    
    def ToDict(self: Self) -> dict[str, Any]:
        return copy.deepcopy(self.__dict__)