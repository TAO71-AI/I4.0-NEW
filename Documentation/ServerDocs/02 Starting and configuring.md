# Starting the server

To start the server you just need to run the `server.py` script. Make sure your working directory is `[I4.0 directory]/Server`.

## Files and directories

When running the server, it will create some files and directories.

|Name|Type|Content|
|----|----|-------|
|API_Keys|Directory|API keys.|
|Logs|Directory|Logs of the server.|
|Temp|Directory|Temporal files.|
|config_server.yaml|File|Configuration of the server.|
|config_\[module\].yaml|File|Global configuration of a module. This file will be created for each module.|
|TOS.md|File|Terms Of Service to use the server.|

# Closing the server

To close the server you can send a **SIGINT** signal.

# Configuration

## Server configuration

|Parameter name|Type(s)|Description|
|--------------|-------|-----------|
|services|dictionary (string: dictionary (string, any))|Models available. Example: `{"model name": {"param name": value}}`. Keep in mind that the model name must not be repeated in the configuration.|
|server_api:min_length|integer|Minimum length of the API keys. Minimum value is 64.|
|server_api:max_length|integer, null|Maximum length of the API keys. This value must not be less than *server_api:min_length*. When set to `null`, this will be the same as *server_api:min_length*.|
|server_api:default_groups|list (string)|Default groups of all the API keys.|
|server_api:admin_groups|list (string)|Groups considered as admins of the server. All the API keys in these groups will be able to execute special commands in the server (such as creating more API keys, etc.).|
|server_whitelist:enabled|bool|Enables the whitelist of the server. When enabled, only the IPs from *server_whitelist:ip_whitelist* and keys from *server_whitelist:key_whitelist* will be able to connect to the server.|
|server_whitelist:ip_whitelist|list (string)|List of allowed IP addresses.|
|server_whitelist:key_whitelist|list (string)|List of allowed API keys.|
|server_blacklist:enabled|bool|Enables the blacklist of the server. When enabled, the IPs from *server_blacklist:ip_blacklist* and keys from *server_blacklist:key_blacklist* will not be able to connect to the server.|
|server_blacklist:ip_blacklist|list (string)|List of banned IP addresses.|
|server_blacklist:key_blacklist|list (string)|List of banned API keys.|
|server_automatic_blacklist:enabled|bool|Enables the automatic moderation of the server. NOTE: This required the *server_blacklist:enabled* parameter to be enabled.|
|server_automatic_blacklist:text_filter_service:enabled|bool|Enables the usage of a text filter for automatic server moderation. NOTE: This requires the `text_classification` module.|
|server_automatic_blacklist:text_filter_service:model_name|string|Name of the model that will be used for the automatic moderation. Models with the `redirect_to` parameter doesn't work. NOTE: This model will be provided FREE OF CHARGE when using the automatic moderation, even if the model is not free to use.|
|server_automatic_blacklist:text_filter_service:keyword|string|Not safe keyword to search in the text response of the service.|
|server_automatic_blacklist:text_filter_service:threshold|float|Threshold until the *server_automatic_blacklist:text_filter_service:keyword* keyword is considered unsafe. Range from 0 to 1.|
|server_automatic_blacklist:text_filter_service:prompt_parameters|dictionary (string, value)|Prompt parameters for the service.|
|server_automatic_blacklist:text_filter_service:user_parameters|dictionary (string, value)|User parameters for the service.|
|server_automatic_blacklist:image_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for images. Requires the `image_classification` module.|
|server_automatic_blacklist:audio_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for audios. Doesn't work for now, since there is no compatible classificators in HuggingFace.|
|server_automatic_blacklist:video_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for videos. Doesn't work for now, since there is no compatible classificators in HuggingFace.|
|server_encryption:allowed_hashes:hashes|list (string)|All of the allowed hashes in the server. `none` is no encryption, no security. `sha224` is a weak hash, almost no security. `sha256` is a decent hash, good security. `sha384` is a very secure hash, extremely good security. `sha512` is the most secure hash, maximum security.|
|server_encryption:allowed_hashes:warnings|dictonary (string, list (string))|Warnings that will be sent to the user when using a specific hash.|
|server_encryption:force_response_hash|string, null|Forces the server to use a hash for the responses. `null` will return the response in the same hash the user is using.|
|server_encryption:encryption_threads|integer|Threads that the server will use when encrypting and decrypting, more threads will require more power but will take less time. `-1` uses all the threads of the CPU.|
|server_encryption:obfuscate|bool|Adds a random length string to the response to patch a vulnerability. [See more here](https://arxiv.org/pdf/2511.03675).|
|server_client_version:min|integer, null|Minimum version of the client API that the server accepts. `null` means the same version as the server.|
|server_client_version:max|integer, null|Maximum version of the client API that the server accepts. `null` means the same version as the server.|
|server_client_version:accept_unknown|bool|Accept clients with an unknown or not specificated version.|
|server_data:tos_file|string|Path to the TOS file. Will be created if it doesn't exist. Requires at least **read** (4) permissions.|
|server_data:temp_dir|string|Path to the temporal files directory. Will be created if it doesn't exist. Requires **read, write, and execute** (7) permissions.|
|server_data:keys_dir|string|Path to the API keys directory. Will be created if it doesn't exist. Requires **read, write, and execute** (7) permissions.|
|server_data:banned_file|string|Path to the file where the banned IPs and API keys will be stored. Will be created if it doesn't exist. Requires **read, write, and execute** (7) permissions.|
|server_data:support_file|string|Path to the file where the support contact information will be stored. It is recommended that this file's JSON syntax looks similar to `[{"name": "my name", "email": "support@mydomain.com", "phone_number": "+1 234567890"}]`. Will be created if it doesn't exist. Requires at least **read** (4) permissions.|
|server_listen|list (dictionary (string, any))|Sockets that will listen for clients. `type` (string; `websockets`) is the type of socket. `host` (string) is the IP address where the server will listen, **0.0.0.0** will listen in all addresses, **127.0.0.1** listen only in the server machine, etc. `port` (integer) is the port where the server will listen, this port can't be repeated in any socket (even if it's of another type). Multiple instances of the same type can be created.|

See the `config_server.yaml` configuration file for more details (when created).

## Services/Modules configuration

See the `config_[module name].yaml` configuration file for details or documentation (when created).

## Global model parameters

These parameters are global and works in all of the services.

|Parameter name|Type(s)|Required|Default value|Description|
|--------------|-------|--------|-------------|-----------|
|service|string|true|-|The module name that the model uses.|
|max_simul_users|integer|false|1|The number of concurrent users that the model can handle at the same time. WARNING: This parameter may be deprecated soon!|
|price **(alias: *pricing*)**|dictionary (string: float)|false|...|Pricing for the model.|
|price:text_input|float|false|0|Price for input text (provided by the user). Measured for each million tokens. Example: value of **5** will charge **5** API tokens for each million embedding tokens.|
|price:image_input|float|false|0|Price for input image (provided by the user). Measured for each 1024x1024 pixels. Example: value of **5** with a **1024x1024** resolution image will charge **5** API tokens.|
|price:audio_input|float|false|0|Price for input audio (provided by the user). Measured for each 1 second. Example: value of **5** with a 1 second audio will charge **5** API tokens.|
|price:video_input_s|float|false|0|Price for input video (provided by the user). Measured for each 1 second. Example: value of **5** with a 1 second video will charge **5** API tokens.|
|price:video_input_r|float|false|0|Price for input video (provided by the user). Measured for each 1024x1024 pixels. Example: value of **5** with a **1024x1024** resolution video will charge **5** API tokens.|
|price:other_input|float, dictionary (string, float)|false|0|Price for unknown type data (provided by the user). Measured for each 1048576 bytes. Example: value of **5** with **1048576** bytes data will charge **5** API tokens. When using a dictionary, a *"global"* parameter must be included with the general price, as well as the price for other data types. Example of the dictionary: `{"global": 5, "pdf": 2.5}`.|
|price:text_output|float|false|0|Same as `price:text_input`, but for output/assistant-generated text.|
|price:image_output|float|false|0|Same as `price:image_input`, but for output/assistant-generated images.|
|price:audio_output|float|false|0|Same as `price:audio_input`, but for output/assistant-generated audios.|
|price:video_output_s|float|false|0|Same as `price:video_input_s`, but for output/assistant-generated videos.|
|price:video_output_r|float|false|0|Same as `price:video_input_r`, but for output/assistant-generated videos.|
|price:other_output|float, dictionary (string, float)|false|0|Same as `price:other_input`, but for output/assistant-generated unknown data types.|
|enable_filter|bool, list (string)|false|true|Enables the filters. These filters check for unwanted data in the conversation and can ban the user if it finds unwanted data. If the type is bool, all filters will be checked. If the type is a list, only the specified data types will be checked. All valid data types are: `text`, `image`, `audio`, `video`.|
|redirect_to|string|false|-|Sets an alias for the model, redirecting the user to the specified server and model. Uses the following template: `TYPE:IS WSS:SERVER HOST:SERVER PORT:MODEL NAME`. Example: `ws:0:main.tao71.org:8060:chatbot-latest-best`. Keep in mind that **SERVER HOST** is where the client will connect, IPs like `127.0.0.1` will connect the client to it's localhost, not the server's localhost.|
