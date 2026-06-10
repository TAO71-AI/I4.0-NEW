# About modules

Modules are scripts that adds more services to the main server. All modules can be disabled and enabled whenever you want.

Keep in mind that when enabling or disabling a module a server restart will be required to apply the changes.

# How to add or enable a module

First, create or download a module. Then, move or copy the directory of the module to the `Server/EnabledModules/` directory.

> [!IMPORTANT]
> If you download a module from internet, make sure it's safe, since the server will execute ALL OF THE CODE inside the directory.

All modules in the `Server/EnabledModules/` directory are enabled.

For more information, go to the `Server/EnabledModules/README.md` file.

# How to remove or disable a module

By just deleting or moving the directory of the module inside the `Server/EnabledModules/` directory the module will be disabled.

It is recommended that the module is moved to the `Server/DisabledModules/` directory.

For more information, go to the `Server/DisabledModules/README.md` file.

# Module files

|File name|Alternatives|Required|Description|
|---------|------------|--------|-----------|
|service.py|serv.py|true|Main script of the module. This will be executed by the server. All of the server-accessible variables and functions must be in this script.|
|requirements.py|requirements.txt|false|List of requirements for the module. Recommended to use a Python script because it will have more control over the installation of dependencies.|
|default_service_configuration.yaml|default_config.yaml|false|Global configuration of the module.|
|README.md|-|false|Readme document. Often used for additional module documentation.|
|LICENSE.md|-|false|License for the module. If not specified, default license is the same as this repository.|

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

|Name|Type|Description|
|----|----|-----------|
|ServiceConfiguration|dictionary (string, Any), null|Global configuration of the service. Will be provided by the server.|
|ServerConfiguration|dictionary (string, Any), null|Global configuration of the server. Will be provided by the server.|
|SERVER_VERSION_MIN|int|Minimum recommended server version.|
|SERVER_VERSION_MAX|int|Maximum recommended server version.|
