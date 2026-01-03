# About modules

Modules are scripts that adds more services to the main server. All modules can be disabled and enabled whenever you want.

Keep in mind that when enabling or disabling a module a server restart will be required to apply the changes.

# How to add or enable a module

First, create or download a module. Then, move or copy the directory of the module to the `Server/Services/` directory.

> [!IMPORTANT]
> If you download a module from internet, make sure it's safe, since the server will execute ALL OF THE CODE inside the directory.

All modules in the `Server/Services/` directory are enabled.

# How to remove or disable a module

By just deleting or moving the directory of the module inside the `Server/Services/` directory the module will be disabled.

# Module files

|File name|Alternatives|Required|Description|
|---------|------------|--------|-----------|
|service.py|serv.py|true|Main script of the module. This will be executed by the server. All of the server-accessible variables and functions must be in this script.|
|requirements.py|requirements.txt|false|List of requirements for the module. Recommended to use a Python script because it will have more control over the installation of dependencies.|
|default_service_configuration.yaml|default_config.yaml|false|Global configuration of the module.|

> [!NOTE]
> It is important to see the official modules' files to see examples.

# Required module functions and variables

All of these functions and variables must be in the main module script. These are functions and variables that the server uses.

## Required module functions

|Name|Arguments|Returns|Description|
|----|---------|-------|-----------|
|SERVICE_LOAD_MODELS|Models (dict\[str, dict\[str, Any\]\])|None|Will load all of the models that are in the *Models* argument. The *Models* argument will follow this example: `{"model name": {...model configuration...}}`.|
|SERVICE_OFFLOAD_MODELS|Models (list\[str\])|None|Will offload all of the models that are in the *Models* argument. The *Models* argument will only contain the name of the models to offload.|
|SERVICE_INFERENCE|Name (str), UserConfig (dict\[str, Any\]), UserParameters (dict\[str, Any\])|Generator\[dict\[str, Any\]\]|Will inference a model. The *Name* argument will be the name of the model to inference. The *UserConfig* argument will contain the configuration made by the user for the model. The *UserParameters* argument will contain parameters and information of the user (example: conversation, API key, and more).|

## Required module variables

There are no required module variables at the moment.
