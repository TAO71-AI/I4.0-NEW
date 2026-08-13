class_name I40_ClientConfiguration extends Object

# Encryption configuration
var Encryption_PublicKey: PackedByteArray = []
var Encryption_PrivateKey: PackedByteArray = []
var Encryption_PrivateKeyPassword: String = "changeme"
var Encryption_Threads: int = 1
var Encryption_RSASize: int = 4096
var Encryption_Hash: String = "sha512"

# Service configuration
var Service_DefaultAPIKey: String = "nokey"

# Other configuration
var PingInterval: float = 20

func ToDict(SavePublicKey: bool = false) -> Dictionary:
	var d = {}
	
	for prop in get_property_list():
		if (prop.name in ["script", "I4.0_ClientConfiguration.gd", "instance"]):
			continue
		
		if (!SavePublicKey && prop.name in ["Encryption_PublicKey", "Encryption_PrivateKey"]):
			d[prop.name] = []
			continue
		
		d[prop.name] = get(prop.name)
	
	return d

static func FromDict(D: Dictionary) -> I40_ClientConfiguration:
	var instance = I40_ClientConfiguration.new()
	
	for k in D.keys():
		instance.set(k, D[k])
	
	return instance
