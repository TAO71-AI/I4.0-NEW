# Import libraries
from typing import Any
import yaml
import os
import shutil
import Utilities.logs as logs

DEFAULT_CONFIGURATION_FILE: str = "./Configuration/default_configuration.yaml"
CONFIGURATION_FILE: str = "./config.yaml"
Configuration: dict[str, Any] | None = None

def ReadConfiguration(ConfigurationFile: str = CONFIGURATION_FILE, Create: bool = True) -> dict[str, Any]:
    """
    Read the configuration file.

    Args:
        ConfigurationFile (str): Configuration file to read. Must be a YAML file.
        Create (bool): Create the file if doesn't exist.

    Returns:
        dict[str, Any]
    """
    # Read default configuration
    if (ConfigurationFile != DEFAULT_CONFIGURATION_FILE):
        logs.WriteLog(logs.INFO, "[config] Reading default configuration file.")
        defaultConf = ReadConfiguration(DEFAULT_CONFIGURATION_FILE, False)
    else:
        defaultConf = None

    # Make sure the configuration file exists
    if (not os.path.exists(ConfigurationFile)):
        if (Create):
            logs.PrintLog(logs.INFO, "[config] Writting configuration file.")
            shutil.copy(DEFAULT_CONFIGURATION_FILE, ConfigurationFile)

            return ReadConfiguration(ConfigurationFile, False)
        else:
            raise FileNotFoundError(f"`{ConfigurationFile}` doesn't exists!")
    
    # Read the file
    conf = {}

    with open(ConfigurationFile, "r", encoding = "utf-8") as configFile:
        conf = yaml.safe_load(configFile)
    
    # Make sure all parameters exist
    if (defaultConf is not None):
        for paramKey, paramValue in defaultConf.items():
            if (paramKey not in conf):
                conf[paramKey] = paramValue
    
    return conf

# Read the configuration
logs.WriteLog(logs.INFO, "[config] Reading configuration file.")
Configuration = ReadConfiguration(CONFIGURATION_FILE, True)