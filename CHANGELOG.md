# Changelog

Using DD-MM-YYYY format.

## 4-12-2025 (commit `v17.0.0-a1`)

### Server changes

- Created `CHANGELOG.md`. Changes will be written here instead of the commit from now on.
- Splitted the **server configuration** and **database server configuration** in multiple files.
- Created `IsConnected` function in the client.
- Moved the server code to the **server_utils** file.
- Created `IsServiceInstalled` function in the services manager.
- (chatbot module) Started the creation of the **auto** reasoning mode.

## 4-12-2025 (commit `v17.0.0-a2`)

### Server changes

- Fixed a small bug that closed the server with a warning.
