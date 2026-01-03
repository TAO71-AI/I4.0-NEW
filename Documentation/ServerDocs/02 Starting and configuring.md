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
|server_automatic_blacklist:text_filter_service:model_name|string|Name of the model that will be used for the automatic moderation. NOTE: This model will be provided FREE OF CHARGE when using the automatic moderation, even if the model is not free to use.|
|server_automatic_blacklist:text_filter_service:keyword|string|Not safe keyword to search in the text response of the service.|
|server_automatic_blacklist:text_filter_service:threshold|float|Threshold until the *server_automatic_blacklist:text_filter_service:keyword* keyword is considered unsafe. Range from 0 to 1.|
|server_automatic_blacklist:text_filter_service:action|string|Action taken by the automatic moderation when the filter detecting unsafe content. `ban` bans the API key (if valid) or the IP address (if the API key is not valid). `warn` sends a warning to the user, but continues with the inference. `raise` throws an error and stops the inference.|
|server_automatic_blacklist:text_filter_service:extra_service_params|dictionary (string, value)|Extra parameters when inferencing the service.|
|server_automatic_blacklist:image_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for images. Requires the `image_classification` module.|
|server_automatic_blacklist:audio_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for audios. Doesn't work for now, since there is no compatible classificators in HuggingFace.|
|server_automatic_blacklist:video_filter_service:*|-|Same as *server_automatic_blacklist:text_filter_service:\[name\]*, but for videos. Doesn't work for now, since there is no compatible classificators in HuggingFace.|
|server_encryption:allowed_hashes:hashes|list (string)|All of the allowed hashes in the server. `none` is no encryption, no security. `sha224` is a weak hash, almost no security. `sha256` is a decent hash, good security. `sha384` is a very secure hash, extremely good security. `sha512` is the most secure hash, maximum security.|
|server_encryption:allowed_hashes:warnings|dictonary (string, list (string))|Warnings that will be sent to the user when using a specific hash.|
|server_encryption:force_response_hash|string, null|Forces the server to use a hash for the responses. `null` will return the response in the same hash the user is using.|
|server_encryption:decryption_threads|integer|Threads that the server will use when decrypting, more threads will require more power but will take less time. `-1` uses all the threads of the CPU.|
|server_encryption:obfuscate|bool|Adds a random length string to the response to patch a vulnerability. [See more here](https://arxiv.org/pdf/2511.03675).|
|server_client_version:min|integer, null|Minimum version of the client API that the server accepts. `null` means the same version as the server.|
|server_client_version:max|integer, null|Maximum version of the client API that the server accepts. `null` means the same version as the server.|
|server_client_version:accept_unknown|bool|Accept clients with an unknown or not specificated version.|
|server_data:tos_file|string|Path to the TOS file. Will be created if it doesn't exist. Requires at least **read** (4) permissions.|
|server_data:temp_dir|string|Path to the temporal files directory. Will be created if it doesn't exist. Requires **read, write, and execute** (7) permissions.|
|server_data:keys_dir|string|Path to the API keys directory. Will be created if it doesn't exist. Requires **read, write, and execute** (7) permissions.|
|server_listen|list (dictionary (string, any))|Sockets that will listen for clients. `type` (string; `websockets`) is the type of socket. `host` (string) is the IP address where the server will listen, **0.0.0.0** will listen in all addresses, **127.0.0.1** listen only in the server machine, etc. `port` (integer) is the port where the server will listen, this port can't be repeated in any socket (even if it's of another type). Multiple instances of the same type can be created.|

See the `config_server.yaml` configuration file for more details (when created).

## Services/Modules configuration

See the `config_[module name].yaml` configuration file for details or documentation (when created).
