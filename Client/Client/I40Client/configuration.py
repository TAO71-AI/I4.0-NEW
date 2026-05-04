from typing import Any, Self

class ClientConfiguration():
    def __init__(self) -> None:
        # Encryption configuration
        self.Encryption_PublicKey: Any | None = None
        self.Encryption_PrivateKey: Any | None = None
        self.Encryption_PrivateKeyPassword: str = "changeme"
        self.Encryption_Threads: int = 1
        self.Encryption_RSASize: int = 4096
        self.Encryption_Hash: str = "sha512"

        # Service configuration
        self.Service_DefaultAPIKey: str = "nokey"

        # Other configuration
        self.PingInterval: float = 2

    def ToDict(self, SavePublicKey: bool = False) -> dict[str, Any]:
        d = self.__dict__.copy()

        if (not SavePublicKey):
            d["Encryption_PublicKey"] = None
            d["Encryption_PrivateKey"] = None
        
        return d
    
    @classmethod
    def FromDict(cls, Dict = dict[str, Any]) -> Self:
        instance = cls.__new__(cls)

        for k, v in Dict.items():
            setattr(instance, k, v)
        
        return instance