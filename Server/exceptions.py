class NotEnoughTokensException(BaseException):
    def __init__(self, Required: float | None = None, Tokens: float | None = None) -> None:
        message = "Not enough tokens."

        if (Required is not None and Tokens is not None):
            message += f" {Required} tokens required; {Tokens} current tokens."
        elif (Required is not None and Tokens is None):
            message += f" {Required} tokens required."

        super().__init__(message)

class InstallationError(BaseException):
    def __init__(self, Message: str | None = None) -> None:
        super().__init__("Installation error" + (f": {Message}" if (Message is not None) else "."))

class ScrapeGuidelinesError(BaseException):
    def __init__(self) -> None:
        super().__init__("Scrapping not allowed here. Please disable `internet > follow_scrape_guidelines` if you see this error often.")

class ConnectionTypeInvalid(BaseException):
    def __init__(self) -> None:
        super().__init__("The connection type is invalid.")

class ConnectionClosedError(BaseException):
    def __init__(self) -> None:
        super().__init__("The connection was closed.")