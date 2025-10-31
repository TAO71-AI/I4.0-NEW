from typing import Literal

__queue__: dict[str, dict[str, float | int | None]] = {}

def GetQueueFor(Name: str) -> dict[str, float | int | None]:
    if (Name not in __queue__):
        __queue__[Name] = {}
    
    if ("users_waiting" not in __queue__[Name]):
        __queue__[Name]["users_waiting"] = 0
    
    if ("tps" not in __queue__[Name]):
        __queue__[Name]["tps"] = None
    
    if ("fts" not in __queue__[Name]):
        __queue__[Name]["fts"] = None
    
    return __queue__[Name]

def SetTPS(Name: str, TPS: float | None) -> None:
    GetQueueFor(Name)
    __queue__[Name]["tps"] = TPS

def SetFTS(Name: str, FTS: float | None) -> None:
    GetQueueFor(Name)
    __queue__[Name]["fts"] = FTS

def SetUsersWaiting(Name: str, Option: Literal["increment", "decrement"] = "increment", Value: int = 1) -> None:
    if (Value <= 0):
        return

    GetQueueFor(Name)
    __queue__[Name]["users_waiting"] += Value if (Option == "increment") else -Value