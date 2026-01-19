# Configuration

This is the default configuration for the client. Keep in mind that this configuration is only for the base client API, clients might add or remove parameters.

|Parameter name|Type(s)|Default value|Description|
|--------------|-------|-------------|-----------|
|Encryption_PublicKey|any, null|null|Public key for encryption. Will be generated automatically if not set.|
|Encryption_PrivateKey|any, null|null|Private key for encryption. Will be generated automatically if not set.|
|Encryption_PrivateKeyPassword|string|changeme|Password for the private key.|
|Encryption_Threads|integer|1|Number of threads to use for decryption. More threads equals more speed.|
|Encryption_RSASize|integer|4096|Length of the keys. Higher values means more secure, but will require more power.|
|Encryption_Hash|string|sha512|Hash to use for encryption/decryption. Valid options are: `none` (no encryption), `sha224` (not secure), `sha256`, `sha384`, `sha512`. It is recommended to use at least **sha256**. Higher hash values means more secure, but will require more power.|
|Service_DefaultAPIKey|string|nokey|Default API key to use.|
