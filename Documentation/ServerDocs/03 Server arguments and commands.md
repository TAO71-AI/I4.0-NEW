# Arguments

|Name|Alias|Type(s)|Description|
|----|-----|-------|-----------|
|--interactive|-it|-|Activates an interactive terminal in the server. Allows command execution.|

# Commands

> [!NOTE]
> These commands are only available in the interactive mode.

|Name|Alias|Arguments|Description|
|----|-----|-------|-----------|
|inference|-|-|Inference a model from the server terminal. This will create a temporal API key for the server and will have priority in the queue.|
|exit|close|-|Closes the server. Alternative to sending a **SIGINT** signal.|
|noninteractive|nit|-|Closes the interactive terminal and changes to the default terminal. This will disable command execution.|
|clear|-|-|Executes the OS command `clear`. This just clears the console.|
|createkey|crk|\[tokens=FLOAT\] \[resetdaily\] \[expiredate=DICTIONARY\] \[allowedips=ARRAY\] \[prioritizemodels=ARRAY\] \[groups=ARRAY\]|Creates an API key. Arguments: `tokens` sets the tokens for the key. `resetdaily` resets the key tokens every day. `expiredate` sets the expiration date for the key, this will deactivate the key in the specified date and hour; example: `{"day": 5, "month": 0, "year": 2028, "hour": 0, "minute": 30}`. `allowedips` sets the only IPs that can use the API key, example: `["127.0.0.1"]`. `prioritizemodels` sets the models where the key will have queue priority, example: `["example_model"]`. `groups` sets the groups of the API key, example: `["test_group"]`.|
|help|-|-|Prints a help message with all of the commands. See this for more details.|
