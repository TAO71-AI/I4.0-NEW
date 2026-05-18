import logging
from typing import Any, Self
import os
import random
import datetime
import json
import time

Configuration: dict[str, Any] = {}
__cached_keys__: dict[str, str] = {}
__busy__: list[str] = []

def __get_current_date_dictionary__() -> dict[str, int]:
    date = datetime.datetime.now()
    return {
        "day": date.day,
        "month": date.month,
        "year": date.year,
        "hour": date.hour,
        "minute": date.minute
    }

def __ensure_dirs__() -> None:
    if (not os.path.exists(Configuration["server_data"]["keys_dir"] + "/")):
        os.mkdir(Configuration["server_data"]["keys_dir"])
    
    if (not os.path.exists(Configuration["server_data"]["keys_dir"] + "/keys.json")):
        with open(Configuration["server_data"]["keys_dir"] + "/keys.json", "x") as f:
            f.write("{}")

def __generate_key_filename__() -> str:
    __ensure_dirs__()

    dirContent = os.listdir(Configuration["server_data"]["keys_dir"])
    name = f"key_{random.randint(0, 2 ** 31 - 1)}.json"

    while (name in dirContent):
        name = f"key_{random.randint(0, 2 ** 31 - 1)}.json"
    
    return name

def Init() -> None:
    global __cached_keys__
    __ensure_dirs__()

    with open(Configuration["server_data"]["keys_dir"] + "/keys.json", "r") as f:
        __cached_keys__ = json.loads(f.read())

    foundKeys = os.listdir(Configuration["server_data"]["keys_dir"])

    for key in foundKeys:
        if (key == "keys.json"):
            continue

        APIKey.LoadFromFile(key[:-5])

def Close() -> None:
    __ensure_dirs__()

    with open(Configuration["server_data"]["keys_dir"] + "/keys.json", "w") as f:
        f.write(json.dumps(__cached_keys__, indent = 4))

class APIKey():
    VERSION = 2

    def __init__(
        self,
        Tokens: int,
        ResetDaily: bool = False,
        ExpireDate: dict[str, int] | datetime.datetime | None = None,
        AllowedIPs: list[str] | None = None,
        PrioritizeModels: list[str] = [],
        Groups: list[str] | None = None
    ):
        if (not isinstance(Configuration["server_api"]["min_length"], int) or Configuration["server_api"]["min_length"] < 16):
            raise ValueError("API key min length must be an integer of at least 16.")
        
        if (Configuration["server_api"]["min_length"] < 16):
            logging.warning("[keys_manager] Min length < 16. This could cause security problems. Setting to 16.")
            Configuration["server_api"]["min_length"] = 16
        
        if (Configuration["server_api"]["max_length"] > 4096):
            logging.warning("[keys_manager] Max length is too long (> 4096). Trying to continue.")
        
        if (Configuration["server_api"]["max_length"] is None or Configuration["server_api"]["max_length"] < 0):
            Configuration["server_api"]["max_length"] = Configuration["server_api"]["min_length"]
        
        if (Configuration["server_api"]["min_length"] > Configuration["server_api"]["max_length"]):
            logging.warning(f"[keys_manager] Min length ({Configuration['server_api']['min_length']}) > max length ({Configuration['server_api']['max_length']}). Setting to {Configuration['server_api']['max_length']}.")
            Configuration["server_api"]["min_length"] = Configuration["server_api"]["max_length"]
        
        minLength = int(Configuration["server_api"]["min_length"])
        maxLength = int(Configuration["server_api"]["max_length"])
        length = minLength if (minLength == maxLength) else random.randint(minLength, maxLength)

        date = datetime.datetime.now()
        chars = "abcdefghijplnmopqrstuvwxyz"
        chars += chars.upper()
        chars += "0123456789!@#$%&()=[]?-_.:,;<>*+/{}\\"

        chars = list(chars)
        random.shuffle(chars)
        chars = "".join(chars)

        self.__version__ = self.VERSION
        self.Key = "".join([chars[random.randint(0, len(chars) - 1)] for _ in range(length)])
        self.Tokens = Tokens
        self.CreationDate = __get_current_date_dictionary__()
        self.UpdateDate = self.CreationDate.copy()
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
    
    def __save_to_file__(self) -> None:
        __ensure_dirs__()
            
        if (self.Key not in __cached_keys__):
            __cached_keys__[self.Key] = __generate_key_filename__()

        with open(f"{Configuration['server_data']['keys_dir']}/{__cached_keys__[self.Key]}", "w" if (self.KeyFileExists(self.Key)) else "x") as f:
            f.write(json.dumps(self.__dict__))
    
    def SaveToFile(self) -> None:
        self.__wait__(self.Key)
        __busy__.append(self.Key)

        try:
            self.__save_to_file__()
        finally:
            __busy__.remove(self.Key)
    
    def RemoveFile(self) -> None:
        self.__wait__(self.Key)
        __busy__.append(self.Key)

        try:
            __ensure_dirs__()

            if (self.KeyFileExists(self.Key)):
                os.remove(f"{Configuration['server_data']['keys_dir']}/{__cached_keys__[self.Key]}")
                __cached_keys__.pop(self.Key)
        finally:
            __busy__.remove(self.Key)

    @staticmethod
    def __wait__(Key: str) -> None:
        while (Key in __busy__):
            time.sleep(0.1)
    
    @staticmethod
    def KeyFileExists(Key: str) -> bool:
        __ensure_dirs__()

        if (Key not in __cached_keys__):
            __cached_keys__[Key] = __generate_key_filename__()

        return os.path.exists(f"{Configuration['server_data']['keys_dir']}/{__cached_keys__[Key]}")
    
    @classmethod
    def LoadFromFile(cls, Key: str) -> Self | None:
        cls.__wait__(Key)
        __busy__.append(Key)
        
        try:
            __ensure_dirs__()

            if (os.path.exists(Configuration["server_data"]["keys_dir"] + f"/{Key}.json")):
                with open(Configuration["server_data"]["keys_dir"] + f"/{Key}.json", "r") as f:
                    cls.__from_dict__(json.loads(f.read()))  # Generate API version 2 files

            if (Key in __cached_keys__ and os.path.exists(cls.KeyFileExists(Key))):
                with open(f"{Configuration['server_data']['keys_dir']}/{__cached_keys__[Key]}", "r") as f:
                    instance = cls.__from_dict__(json.loads(f.read()))
            else:
                instance = None
        finally:
            __busy__.remove(Key)
        
        return instance

    @classmethod
    def __from_dict__(cls, Dictionary: dict[str, Any]) -> Self:
        instance = cls.__new__(cls)
        __ensure_dirs__()

        for k, v in Dictionary.items():
            setattr(instance, k, v)
        
        if (instance.__version__ < 1):
            setattr(instance, "UpdateDate", instance.CreationDate.copy())
        
        if (instance.__version__ < 2):
            logging.info(f"[keys_manager] Trying to convert API key (version {instance.__version__}) to new version ({cls.VERSION}).")

            if (instance.Key not in __cached_keys__):
                __cached_keys__[instance.Key] = __generate_key_filename__()
            
            os.rename(Configuration["server_data"]["keys_dir"] + f"/{instance.Key}.json", Configuration["server_data"]["keys_dir"] + f"/{__cached_keys__[instance.Key]}")

        if (instance.__version__ != cls.VERSION):
            logging.warning("[keys_manager] API key version is older or newer than the server version. This might cause errors.")

            instance.__version__ = cls.VERSION
            instance.__save_to_file__()
        
        if (
            instance.DailyReset["reset"] and
            (datetime.datetime.now() - datetime.datetime(
                year = instance.UpdateDate["year"],
                month = instance.UpdateDate["month"],
                day = instance.UpdateDate["day"],
                hour = instance.UpdateDate["hour"],
                minute = instance.UpdateDate["minute"]
            )).total_seconds() >= 86400
        ):
            instance.Tokens = instance.DailyReset["tokens"]
            instance.UpdateDate = __get_current_date_dictionary__()
        
        return instance