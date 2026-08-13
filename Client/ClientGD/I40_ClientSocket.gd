class_name I40_ClientSocket extends Node

const VERSION = 200300
const TRANSFER_RATE = 8192 * 1024

signal AdvancedSendAndReceive_OnToken(Token: Dictionary)

var _EncryptionScript: CSharpScript

var _Type: String
var _Configuration: Object

var _Socket: PacketPeer
var _CurrentConnection: Array = [null, null, null, null]
var _Processing: bool = false
var _Cache: String = ""

var _ServerPublicKey: PackedByteArray
var _PublicKeyStr: String
var _PublicKey: PackedByteArray
var _PrivateKey: PackedByteArray

func Init(EncryptionScript: CSharpScript, Type: String, Configuration: Object) -> void:
	if (!is_inside_tree()):
		push_error("I4.0 client node MUST be in the scene tree.")
	
	_EncryptionScript = EncryptionScript
	_Type = Type
	_Configuration = Configuration
	
	if (_Configuration.Encryption_PublicKey.size() == 0 || _Configuration.Encryption_PrivateKey.size() == 0):
		var keys = _EncryptionScript.GenerateRSAKeys(_Configuration.Encryption_RSASize)
		
		_PrivateKey = keys[0]
		_PublicKey = keys[1]
	else:
		_PrivateKey = _Configuration.Encryption_PrivateKey
		_PublicKey = _Configuration.Encryption_PublicKey
	
	_PublicKeyStr = Marshalls.utf8_to_base64(_PublicKey.get_string_from_utf8())

func IsConnected() -> bool:
	if (_Socket == null):
		return false
	
	if (_Type == "websocket"):
		return _Socket.get_ready_state() == WebSocketPeer.STATE_OPEN
	
	return false

func Connect(Host: String, Port: int, Secure: bool = false) -> void:
	Close()
	
	if (_Type == "websocket"):
		var uri = ("wss" if (Secure) else "ws") + "://" + Host + ":" + str(Port)
		
		_Socket = WebSocketPeer.new()
		_Socket.connect_to_url(uri, null)
		
		while (_Socket.get_ready_state() == WebSocketPeer.STATE_CONNECTING):
			await get_tree().create_timer(0.1).timeout
			_UpdateSocket()
		
		await get_tree().create_timer(0.1).timeout
	
	_CurrentConnection = [_Type, Host, Port, Secure]
	_SetServerPublicKey()

func Close() -> void:
	if (_Socket == null):
		return
	
	if (_Type == "websocket"):
		Send("close")
		_Socket.close()
	
	_Socket = null
	_Processing = false

func _SetServerPublicKey() -> void:
	_ServerPublicKey = Marshalls.base64_to_utf8(SendAndReceive("get_public_key")).to_utf8_buffer()

func _Send(Data: String) -> void:
	if (!IsConnected()):
		push_error("Socket not connected.")
		return
	
	_Socket.put_packet(Data.to_utf8_buffer())
	_UpdateSocket()

func _Receive() -> String:
	if (!IsConnected()):
		push_error("Socket not connected.")
		return ""
	
	var data = ""
	
	while (_Socket.get_available_packet_count() == 0):
		_UpdateSocket()
	
	while (_Socket.get_available_packet_count() > 0):
		var packet = _Socket.get_packet()
		data += packet.get_string_from_utf8()
		
		_UpdateSocket()
	
	return data

func _UpdateSocket() -> void:
	if (_Socket.has_method("poll")):
		_Socket.poll()

func Send(Data: String) -> void:
	while (_Processing):
		_UpdateSocket()
	
	_Processing = true
	
	for i in range(0, Data.length(), TRANSFER_RATE):
		_Send(Data.substr(i, i + TRANSFER_RATE))
	
	_Send("--END--")

func Receive() -> String:
	var data = _Cache
	
	if (!data.is_empty()):
		if ("--END--" in data):
			_Cache = data.substr(data.find("--END--") + 7, -1)
			data = data.substr(0, data.find("--END--"))
		else:
			_Cache = ""
		
		return data
	
	while (true):
		var chunk = _Receive()
		
		if ("--END--" in chunk):
			data += chunk.substr(0, chunk.find("--END--"))
			_Cache = chunk.substr(chunk.find("--END--") + 7, -1)
			
			break
		
		chunk = chunk.substr(0, TRANSFER_RATE)
		data += chunk
	
	_Processing = false
	return data

func SendAndReceive(Data: String) -> String:
	Send(Data)
	return Receive()

func AdvancedSendAndReceive(
	ModelName: String,
	APIKey: String = "",
	PromptConversation: Array = [],
	PromptParameters: Dictionary = {},
	UserParameters: Dictionary = {},
	Service: String = "inference",
	OnReceivedToken: Callable = func(_token): pass
) -> void:
	var data = {
		"hash": _Configuration.Encryption_Hash,
		"public_key": _PublicKeyStr,
		"version": VERSION,
		"content": {
			"model_name": ModelName,
			"service": Service,
			"key": _Configuration.Service_DefaultAPIKey if (APIKey.is_empty()) else APIKey,
			"prompt": {
				"conversation": PromptConversation,
				"parameters": PromptParameters
			},
			"user_parameters": UserParameters
		}
	}
	data["content"] = _EncryptionScript.Encrypt(
		_Configuration.Encryption_Hash,
		_ServerPublicKey,
		JSON.stringify(data["content"]),
		_Configuration.Encryption_Threads
	)
	
	Send(JSON.stringify(data))
	AdvancedSendAndReceive_OnToken.connect(OnReceivedToken)
	
	var redirectTo = null
	
	while (true):
		var recvData = Receive()
		recvData = JSON.parse_string(recvData)
		recvData = _EncryptionScript.Decrypt(
			recvData["hash"],
			_PrivateKey,
			recvData["data"],
			_Configuration.Encryption_Threads
		)
		recvData = JSON.parse_string(recvData)
		
		if ("redirect_to" in recvData):
			redirectTo = recvData["redirect_to"]
			break
		
		AdvancedSendAndReceive_OnToken.emit(recvData)
		await get_tree().process_frame
		
		if ("ended" in recvData && recvData["ended"]):
			break
	
	AdvancedSendAndReceive_OnToken.disconnect(OnReceivedToken)
	
	if (redirectTo != null):
		var previousConnection = null
		
		if (redirectTo["host"] != null && redirectTo["port"] != null):
			previousConnection = _CurrentConnection
			
			_Type = "websocket" if (redirectTo["type"] == "ws") else "socket" if (redirectTo["type"] == "s") else ""
			await Connect(redirectTo["host"], redirectTo["port"], redirectTo["secure"])
		
		_UpdateSocket()
		await AdvancedSendAndReceive(
			redirectTo["model"],
			APIKey,
			PromptConversation,
			PromptParameters,
			UserParameters,
			Service,
			OnReceivedToken
		)
		
		if (previousConnection != null):
			_Type = previousConnection[0]
			await Connect(previousConnection[1], previousConnection[2], previousConnection[3])
		
		return

func GetAvailableModels() -> PackedStringArray:
	var models = []
	await AdvancedSendAndReceive("", "", [], {}, {}, "get_available_models", func(token: Dictionary) -> void:
		if ("models" in token):
			for model in token["models"]:
				models.append(model)
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (models.size() == 0):
		push_error("Could not get models.")
	
	return models

func GetModelInfo(ModelName: String) -> Dictionary:
	var modelInfo = {}
	await AdvancedSendAndReceive(ModelName, "", [], {}, {}, "get_model_info", func(token: Dictionary) -> void:
		if ("config" in token):
			for k in token["config"].keys():
				modelInfo[k] = token["config"][k]
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (modelInfo.size() == 0):
		push_error("Could not get model information.")
	
	return modelInfo

func GetQueueData(ModelName: String) -> Dictionary:
	var queueData = {}
	await AdvancedSendAndReceive(ModelName, "", [], {}, {}, "get_queue_data", func(token: Dictionary) -> void:
		if ("queue" in token):
			for k in token["queue"].keys():
				queueData[k] = token["queue"][k]
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (queueData.size() == 0):
		push_error("Could not get queue data.")
	
	return queueData

func CreateAPIKey(
	Tokens: float = 0,
	ResetDaily: bool = false,
	ExpireDate: Dictionary = {},
	AllowedIPs: PackedStringArray = [],
	PrioritizeModels: PackedStringArray = [],
	Groups: PackedStringArray = []
) -> String:
	var expireDate = null
	var allowedIPs = null
	
	if (ExpireDate.size() > 0):
		expireDate = ExpireDate
	
	if (AllowedIPs.size() > 0):
		allowedIPs = AllowedIPs
	
	var key = [""]
	await AdvancedSendAndReceive("", "", [], {
		"tokens": Tokens,
		"reset_daily": ResetDaily,
		"expire_date": expireDate,
		"allowed_ips": allowedIPs,
		"prioritize_models": PrioritizeModels,
		"groups": Groups
	}, {}, "create_api_key", func(token: Dictionary) -> void:
		if ("key" in token):
			key[0] = token["key"]
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (key.size() == 0):
		push_error("Could not create new API key.")
	
	return key[0]

func DeleteAPIKey(APIKey: String) -> void:
	await AdvancedSendAndReceive("", "", [], {
		"key": APIKey
	}, {}, "delete_api_key", func(token: Dictionary) -> void:
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)

func GetKeyData(APIKey: String) -> Dictionary:
	var key = [null]
	await AdvancedSendAndReceive("", "", [], {
		"key": APIKey
	}, {}, "get_key_data", func(token: Dictionary) -> void:
		if ("key" in token):
			key[0] = token["key"]
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (key[0] == null):
		push_error("Could not fetch key data.")
	
	return key[0]

func BanUser(Type: String, Value: String) -> void:
	if (Type not in ["key", "ip"]):
		push_error("Invalid ban type.")
		return
	
	await AdvancedSendAndReceive("", "", [], {
		"type": Type,
		"value": Value
	}, {}, "ban", func(token: Dictionary) -> void:
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)

func PardonUser(Type: String, Value: String) -> void:
	if (Type not in ["key", "ip"]):
		push_error("Invalid pardon type.")
		return
	
	await AdvancedSendAndReceive("", "", [], {
		"type": Type,
		"value": Value
	}, {}, "pardon", func(token: Dictionary) -> void:
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)

func GetSupport() -> Array:
	var support = [null]
	await AdvancedSendAndReceive("", "", [], {}, {}, "get_support", func(token: Dictionary) -> void:
		if ("support" in token):
			support[0] = token["support"]
		
		if ("errors" in token && token["errors"].size() > 0):
			push_error("Unexpected server error(s): " + str(token["errors"]))
	)
	
	if (support[0] == null):
		push_error("Could not fetch support data.")
	
	return support[0]
