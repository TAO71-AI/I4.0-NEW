class NotEnoughTokensException(Exception):
    def __init__(self, Required: float | None = None, Tokens: float | None = None) -> None:
        message = "Not enough tokens."

        if (Required is not None and Tokens is not None):
            message += f" {Required} tokens required; {Tokens} current tokens."
        elif (Required is not None and Tokens is None):
            message += f" {Required} tokens required."

        super().__init__(message)

class InstallationError(Exception):
    def __init__(self, Message: str | None = None) -> None:
        super().__init__("Installation error" + (f": {Message}" if (Message is not None) else "."))

class ConnectionTypeInvalid(Exception):
    def __init__(self) -> None:
        super().__init__("The connection type is invalid.")

class ConnectionClosedError(Exception):
    def __init__(self) -> None:
        super().__init__("The connection was closed.")

class FilterException(Exception):
    def __init__(self):
        super().__init__("Your message does not comply with the server's Terms of Service.")