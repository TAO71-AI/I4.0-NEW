# Import libraries
from typing import Any
import yaml
import os
import shutil
import Utilities.logs as logs

DEFAULT_SERVER_CONFIGURATION_FILE: str = "./Configuration/default_configuration_server.yaml"
SERVER_CONFIGURATION_FILE: str = "./config_server.yaml"
Configuration: dict[str, Any] | None = None

def ReadConfiguration(ConfigurationFile: str | None = None, Create: bool = True, SetDefault: bool = False) -> dict[str, Any]:
    """
    Read the configuration file.

    Args:
        ConfigurationFile (str): Configuration file to read. Must be a YAML file.
        Create (bool): Create the file if doesn't exist.

    Returns:
        dict[str, Any]
    """
    global Configuration

    if (ConfigurationFile is None):
        ConfigurationFile = SERVER_CONFIGURATION_FILE

    # Read default configuration
    if (ConfigurationFile != DEFAULT_SERVER_CONFIGURATION_FILE):
        logs.WriteLog(logs.INFO, f"[config] Reading default configuration file `{ConfigurationFile}`.")
        defaultConf = ReadConfiguration(DEFAULT_SERVER_CONFIGURATION_FILE, False)
    else:
        defaultConf = None

    # Make sure the configuration file exists
    if (not os.path.exists(ConfigurationFile)):
        if (Create):
            defaultConfigFile = DEFAULT_SERVER_CONFIGURATION_FILE

            logs.PrintLog(logs.INFO, f"[config] Writting configuration file `{defaultConfigFile}` => `{ConfigurationFile}`.")
            shutil.copy(defaultConfigFile, ConfigurationFile)

            return ReadConfiguration(ConfigurationFile, False)
        else:
            raise FileNotFoundError(f"`{ConfigurationFile}` doesn't exists!")
    
    # Read the file
    logs.WriteLog(logs.INFO, f"[config] Reading configuration file `{ConfigurationFile}`.")
    conf = {}

    with open(ConfigurationFile, "r", encoding = "utf-8") as configFile:
        conf = yaml.safe_load(configFile)
    
    # Make sure all parameters exist
    if (defaultConf is not None):
        for paramKey, paramValue in defaultConf.items():
            if (paramKey not in conf):
                conf[paramKey] = paramValue
    
    if (SetDefault):
        Configuration = conf
    
    return conf