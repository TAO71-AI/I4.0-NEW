INFO: int = 0
WARNING: int = 1
ERROR: int = 2
CRITICAL: int = 3

def StringToLogLevel(Level: str) -> int | None:
    """
    Convert a string (log level name) into an integer value.

    Args:
        Level (str): The log level name.
    
    Returns:
        int | None
    """
    # Lower the log level name
    logLvl = Level.lower()

    # Get and return the log level name
    if (logLvl == "info"):
        return INFO
    elif (logLvl == "warning" or logLvl == "warn"):
        return WARNING
    elif (logLvl == "error" or logLvl == "err"):
        return ERROR
    elif (logLvl == "critical" or logLvl == "crit"):
        return CRITICAL
    
    return None

def LogLevelToString(Level: int) -> str | None:
    """
    Convert an integer (log level) into a string.

    Args:
        Level (int): The log level.
    
    Returns:
        str | None
    """
    if (Level == 0):
        return "INFO"
    elif (Level == 1):
        return "WARNING"
    elif (Level == 2):
        return "ERROR"
    elif (Level == 3):
        return "CRITICAL"
    
    return None

def WriteLog(Level: int, Message: str) -> None:
    """
    Write a log into the logs file.

    Args:
        Level (int): Log level.
        Message (str): Message of the log.
    
    Returns:
        None
    """
    with open("latest.txt", "a") as f:
        f.write(f"[{LogLevelToString(Level)}] {Message}\n")

def PrintLog(Level: int, Message: str, Flush = True) -> None:
    """
    Print a log.

    Args:
        Level (int): Log level.
        Message (str): Message of the log.
        Flush (bool): Wether to flush the message or not.
    
    Returns:
        None
    """
    print(f"[{LogLevelToString(Level)}] {Message}", flush = Flush)
    WriteLog(Level, Message)