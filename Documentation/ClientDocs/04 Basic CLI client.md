# Basic CLI client

The client API includes a basic CLI client.

You can start this CLI client by using the command `I40C` in your terminal. Keep in mind that this CLI client have only been tested in **Arch Linux**, but it is expected to work fine in other GNU/Linux distributions and OSs like Windows.

## Files and directories

This CLI client will create some files and directories in your system.

|Name|Path (Windows)|Path (MacOS)|Path (GNU/Linux)|Content|
|----|--------------|------------|----------------|-------|
|config.json|(LOCAL APP DATA)/I4.0-Client|(HOME DIR)/Library/Application Support/I4.0-Client|(HOME DIR)/.local/share/I4.0-Client|Configuration of the client.|
|conversation.json|(LOCAL APP DATA)/I4.0-Client|(HOME DIR)/Library/Application Support/I4.0-Client|(HOME DIR)/.local/share/I4.0-Client|Conversation and other related parameters.|

## Arguments

These arguments must be provided after the `I40C` command, separated by spaces.

|Name|Required|What it does|
|----|--------|------------|
|--config=CONFIG_FILE|No|Sets a custom configuration file. **DO NOT USE THIS ARGUMENT UNLESS YOU KNOW WHAT YOU ARE DOING**.|
|--conv-file=CONVERSATION_FILE|No|Sets a custom conversation file. **DO NOT USE THIS ARGUMENT UNLESS YOU KNOW WHAT YOU ARE DOING**.|

## Usage

When you open the CLI client for the first time, you'll need to set some parameters:
- Connection type: The way that the API will connect to the server (only available option right now is `websocket`).
- Host: IP or domain of the server.
- Port: Port for the server, default port for servers is 8060.
- Secure: Wether to use a secure connection to connect to the server. NOTE: Even if you use an unsecure connection, the messages will still be sent encrypted by default. ONLY WORKS FOR `websocket` CONNECTION TYPE.
- Model name: Name of the model to use for inference.
- Follow scrape guidelines: Wether to follow the scrape guidelines of the websites when using internet. NOTE: If enabled, some websites might stop working.

When you open the CLI client, you will see a message similar to `Mode ['e', 'scc', 'cc', 'pp', 'up', 'sc', 'cls', 'h', 'c'*]:`. Then, you must select a mode:
- `e`: *Exit* the basic CLI client.
- `scc`: *Selective Clear Conversation*, choose and delete conversation messages instead of the whole conversation.
- `cc`: *Clear Conversation*, clears the whole conversation.
- `pp`: Set the *Prompt Parameters* that will be used. **Not recommended unless you know what you're doing**.
- `up`: Set the *User Parameters* that will be used. **Not recommended unless you know what you're doing**.
- `sc`: *Show Conversation*.
- `cls`: *Clear* the terminal screen.
- `h`: Print *Help* message. See this for more information.
- `c`: *Continue*.
- Asterisk: Default option.

After selecting the **c** option, you will see a message similar to `Message #X role:`. Every model is different, but usually the roles vary between **user** and **assistant**, where *user* is your input prompt for the model and *assistant* is the AI response. Leave this parameter empty to continue with the processing.

After specifying a role, you'll see a message similar to `Message #X content #Y type:`. Some content types are **image**, **audio**, **video**, and **text**. Every service or model might require different content types. Leave this parameter empty to continue to the next message.

When selecting **text** as content type you need to write a text. For multiple lines end the current line with ` \`, this must be done for each line.

When selecting any other content type that is not **text** you need to write the path to a file.

After setting all of the messages, a petition will be sent to the server and processing will begin. Make sure the final message's role is set to **user**, otherwise processing with some models might fail.

After processing ends without errors, the assistant's message will be saved automatically in the conversation.

> [!NOTE]
> The text response of the model will be printed in the terminal.
> 
> The files response of the model will be stored in the current work directory:
> - Images will be stored in the **.webp** extension.
> - Audios will be stored in the **.wav** extension.
> - Videos will be stored in the **.webm** extension.
> - Any other unrecognized file type will be stored without a file extension.
