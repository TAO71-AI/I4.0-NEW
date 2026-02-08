# Changelog

Using DD-MM-YYYY format.

Keep in mind that these are only the more relevant changes.

---

## 8-2-2026 (commit `v17.2.1`)

### Server changes

- (chatbot module) Fixed a small bug with LoRA.

---

## 8-2-2026 (commit `v17.2.0`)

### Server changes

- (chatbot module) Implemented LoRA.
- The server now stores a list with all the clients connected and closes all of the clients connections when closing.
- Updated encryption script to allow multi-thread encryption.
- Fixed a bug that made all of the models free-to-use.
- Fixed a bug regarding model pricing for input.
- Updated configuration.

### Client changes

- Updated encryption script.

### Other changes

- Updated server documentation.

---

## 7-2-2026 (commit `v17.1.1`)

### Server changes

- (chatbot module) Fixed bugs.

---

## 5-2-2026 (commit `v17.1.0`)

### Server changes

- Fixed bugs.
- Added `BASE_FLASH_ATTN_MAX_JOBS` environment variable to the requirements installation.
- (chatbot module) Removed unnecesary configuration.
- (chatbot module) Replaced chatbot `test_inference_files` and `test_inference_text` parameters with `test_inference_conversation` and `test_inference_configuration`.
- (chatbot module) Removed reasoning, since it will be provided by the client.
- (chatbot module) Added a `stop_tokens` parameter. This will stop the inference when any of the tokens in the list are generated.
- (musicgen module) Added a warning log when loading a HeartMuLa model.
- Implemented a new module: **stt** (*Speech To Text*).
  - If you are using the Qwen3-ASR with ForcedAligner, keep in mind that it has not been fully tested yet.

### Client changes

- (Basic CLI Client) Updated tools detection when using a chatbot.
- (Basic CLI Client) Added a message when receiving the `extra` parameter in the tokens response.

### Other changes

- Updated server documentation.

---

## 1-2-2026 (commit `v17.0.0`)

### Other changes

- Open-Sourced the I4.0 v17.0.0 code! Future versions will also be Open-Source.
- Updated license.

---

## 30-1-2026 (commit `v17.0.0-a17`)

### Server changes

- Moved the HuggingFace model to a different script in the `imgclass` module.
- Created `musicgen` module, for music generation. Supports only **HeartMuLa** for now.
- Created `tts` module, Text-To-Speech. Supports only **Qwen3-TTS** for now.
- Moved the PyTorch utilities file to `Utilities/model_utils.py`. It also has more utilities now.
- Updated requirements.
- Added a new service to the server: `get_support`. Clients can now get the contact info of the support.
- The services manager can now save the assistant response.

### Client changes

- Implemented new service: `get_support`.

### Other changes

- Updated server documentation.
- Updated gitignore.

---

## 19-1-2026 (commit `v17.0.0-a16`)

### Server changes

- (`chatbot` module) Fixed a bug that made multimodal models not offload correctly, which kept consuming memory.
- Updated configuration.
- Implemented a ban system.
- Allowed the usage of SSL certificates in the WebSockets server.
- Updated requirements to automatically detect your GPU and install the recommended torch wheel for your hardware.
- Fixed a small bug that didn't stopped generation when a user disconnects. This caused queues to bug and never end, and also consumed more tokens of the API key.
- Added more services: `ban`, `pardon`. Only works for API keys that are in an admin group.
- Added a new parameter for models: `enable_filter` (enabled if not specified). This parameter controls wether the model filters input messages or not.
- Fixed a small bug in the queue system that could cause repetitive UIDs.

### Client changes

- Added kwargs for some functions.
- Implemented the new server commands.

### Other changes

- Updated server documentation.
- Created new client documentation.

---

## 8-1-2026 (commit `v17.0.0-a15`)

### Other changes

- Updated `README.md`.

---

## 8-1-2026 (commit `v17.0.0-a14`)

### Server changes

- New server commands: `create_api_key`, `delete_api_key`, and `get_key_data`. All three require admin-level authorization to be executed.
- Created `Utilities/torch_utils.py` script for generic PyTorch utilities that will be used by different modules.

### Client changes

- Removed the `setup.py` script, now everything will be in the `pyproject.toml` file.
- Added a new command to the basic CLI client; `cls`, clears the screen.
- Implemented the new server commands in the client API.

---

## 4-1-2026 (commit `v17.0.0-a13`)

### Server changes

- Added more PIP requirements.
- Fixed a bug when offloading.
- Fixed bugs when loading more than one module.
- Other minor bug fixes.
- Created a new module: `imgclass` (Image Classification).

### Other changes

- Updated server documentation.

---

## 4-1-2026 (commit `v17.0.0-a12`)

### Other changes

- Updated documentation to add the missing environment variable for requirements.

---

## 4-1-2026 (commit `v17.0.0-a11`)

### Server changes

- Added new requirements environment variables.
- Server now installs PyTorch.

### Other changes

- Updated documentation.

---

## 3-1-2026 (commit `v17.0.0-a10`)

### Server changes

- Removed transfer rate.
- Implemented model offloading.
- Fixed bugs.

### Client changes

- Added new parameter to the `search_text` chatbot tool.
- Changed HTML=>Markdown conversion to use an external library.
- Added **Grokipedia** to the internet scrapper.
- Removed transfer rate.

### Other changes

- Updated documentation.
- Started creating client documentation.
- Updated `README.md`.

---

## 1-1-2026 (commit `v17.0.0-a9`)

### Server changes

- Added a new function to the queue script.

### Other changes

- Added more server documentation.

---

## 31-12-2025 (commit `v17.0.0-a8`)

### Server changes

- Fixed a small bug when handling exceptions.

### Client changes

- Better **HTML=>Markdown** parser.
- Added the hability to also scrape media (images, gif, and videos) from Reddit posts (will be implemented soon for other websites).
- Fixed some bugs.

---

## 30-12-2025 (commit `v17.0.0-a7`)

### Server changes

- (chatbot module) Added some experimental parameters to the requirements, for future testing (will be removed if doesn't work).
- Fixed a small bug that didn't saved the API key when the client disconnects mid-inference.
- Removed some parameters in the configuration.

### Client changes

- (client CLI) Made the client disconnect for each inference.

### Other changes

- Started creating server documentation.

---

## 29-12-2025 (commit `v17.0.0-a6`)

### Server changes

- Model pricing is now calculated in another function rather than in the function for inference.
- Added a `createkey` command to the server terminal (only works in the interactive mode).
- Fixed a small bug that could cause a crash to the server.

### Client changes

- Removed the API configuration in the client CLI.

---

## 28-12-2025 (commit `v17.0.0-a5`)

### Server changes

- (`chatbot` module) Removed `extra_tools`, tools will be processed at the client side.
- (`chatbot` module) Removed **tools.py** script.

### Client changes

- Created a test client CLI script.
- Fixed a small bug that made the client not receive the full server response due to an incorrect transfer rate.
- Added more services to the client API.

### Other changes

- Added titles to the HTML to Markdown parser.
- Added scrapping for [wikidot.com wikis](https://www.wikidot.com/) and [fandom.com wikis](https://www.fandom.com/).
- Moved the **format_conversion.py**, **internet.py**, and **tools.py** scripts to the client's utilities.

---

## 24-12-2025 (commit `v17.0.0-a4`)

### Server changes

- (`chatbot` module) Yield a warning when the content type is not supported by the model.
- Fixed a huge bug that froze the server when trying to process more than one client at the same time.
- Fixed a small bug that searched for all the services in the disk for each inference.
- Rewritten queue script.

### Client changes

- Started creating the client scripts.

### Other changes

- Updated `README.md`:
  - Added more key features.
  - Created requirements for the client API.
  - Removed the database server from the requirements.

---

## 20-12-2025 (commit `v17.0.0-a3`)

### Server changes

- Removed database server.
- Changed the max allowed API key length from **1024** to **128**.
- Removed all the stored encryption keys, they will only generate during runtime.
- Removed predefined system prompts, since they will be managed by the user for each inference.
- Changed the default max length in the chatbot default service configuration from **99999** to **999999**.
- Removed conversation system. Conversations will be given by the client for each inference.
- Removed some chatbot tools that were for memory management. That would be processed by the client.
- Changed log system. Now it saves the time, multiple files, and has environment variables.
- Fixed some bugs in the server utilities.
- Added a function to the encryption script that gets the hash of a content, probably for future updates.
- Added a new exception type; `ConnectionClosedError`.
- The API keys manager script now handles the file saving/loading for API keys.
- Added and changed some parameters for the clients.
- The server now waits 100ms before processing every inference or service that uses or requires an API key. This is done to avoid brute-force attacks.
- Changed pricing:
  - Text inputs/outputs are charged for every 1000000 tokens.
  - Image inputs/outputs are charged for every 1024 pixels. For example, if the price per image is 1 token, an image with the resolution 1024x1024 will take 1 token. Another image with the resolution 2048x2048 will take 4 tokens. Another image with the resolution 1024x2048 will take 2 tokens.
  - Audio inputs/outputs are charged for each second.
  - Video inputs/outputs are charged the same as images; every 1024 pixels, but also are charged for each second, like audios.
  - Other inputs/outputs are charged for each megabyte, and prices for different data types can be configured.
  - Prices are rounded to 5 decimal digits.
- Fixed some issues related to the queue.

---

## 4-12-2025 (commit `v17.0.0-a2`)

### Server changes

- Fixed a small bug that closed the server with a warning.

---

## 4-12-2025 (commit `v17.0.0-a1`)

### Server changes

- Created `CHANGELOG.md`. Changes will be written here instead of the commit from now on.
- Splitted the **server configuration** and **database server configuration** in multiple files.
- Created `IsConnected` function in the client.
- Moved the server code to the **server_utils** file.
- Created `IsServiceInstalled` function in the services manager.
- (chatbot module) Started the creation of the **auto** reasoning mode.
