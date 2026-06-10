using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;

namespace TAO71.I4_0
{
    public static class ServerConnection
    {
        public const int VERSION = 220000;
        public const int TRANSFER_RATE = 8192 * 1024;
    }

    public class ClientSocket
    {
        private ClientWebSocket? Sock = null;
        private string SockType = "";
        protected ClientConfiguration Config;
        private string? ServerPublicKeyStr = null;
        private string? PublicKeyStr = null;
        private RSA? ServerPublicKey = null;
        private (string, string, int, bool)? CurrentConnection = null;
        private RSA? PrivateKey = null;
        private RSA? PublicKey = null;

        public ClientSocket(
            string Type,
            ClientConfiguration Configuration
        )
        {
            SockType = Type;
            Config = Configuration;

            if (Configuration.Encryption_PublicKey == null || Configuration.Encryption_PrivateKey == null)
            {
                (RSA, RSA) keys = Encryption.GenerateRSAKeys(Configuration.Encryption_RSASize);
                PrivateKey = keys.Item1;
                PublicKey = keys.Item2;
            }

            (byte[]?, byte[]?) keysBytes = Encryption.SaveKeys(null, null, "", PublicKey, null);
            PublicKeyStr = Encoding.UTF8.GetString(keysBytes.Item2!);
        }

        public bool IsConnected()
        {
            if (SockType == "websocket" && Sock != null)
            {
                return Sock.State == WebSocketState.Open;
            }

            return false;
        }

        public async Task Connect(string Host, int Port, bool Secure = false)
        {
            await Close();

            if (SockType == "websocket")
            {
                string scheme = Secure ? "wss" : "ws";
                string uri = $"{scheme}://{Host}:{Port}";

                Sock = new ClientWebSocket();
                Sock.Options.SetBuffer(ServerConnection.TRANSFER_RATE, ServerConnection.TRANSFER_RATE);

                await Sock.ConnectAsync(new Uri(uri), CancellationToken.None);
            }

            CurrentConnection = (SockType, Host, Port, Secure);
            await _SetServerPublicKey();
        }

        public async Task Close()
        {
            if (Sock == null) return;

            if (SockType == "websocket")
            {
                try
                {
                    await Send("close");

                    if (Sock.State == WebSocketState.Open)
                    {
                        await Sock.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    }
                }
                catch
                {
                    
                }
            }

            Sock = null;
        }

        private async Task _SetServerPublicKey()
        {
            ServerPublicKeyStr = await SendAndReceive("get_public_key");
            (_, RSA? pub) = Encryption.LoadKeysFromContent(null, "", Convert.FromBase64String(ServerPublicKeyStr));
            ServerPublicKey = pub;
        }

        private async Task _Send(string Data)
        {
            if (!IsConnected()) throw new InvalidOperationException("Socket is not connected.");

            if (SockType == "websocket" && Sock != null)
            {
                byte[] buffer = Encoding.UTF8.GetBytes(Data);
                await Sock.SendAsync(new ArraySegment<byte>(buffer), WebSocketMessageType.Text, true, CancellationToken.None);
            }
        }

        private async Task<string> _Receive()
        {
            if (!IsConnected()) throw new InvalidOperationException("Socket is not connected.");

            if (SockType == "websocket" && Sock != null)
            {
                using MemoryStream ms = new MemoryStream();
                byte[] buffer = new byte[ServerConnection.TRANSFER_RATE];
                WebSocketReceiveResult result;

                do
                {
                    result = await Sock.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                    ms.Write(buffer, 0, result.Count);
                }
                while (!result.EndOfMessage);

                string data = Encoding.UTF8.GetString(ms.ToArray());

                ms.Close();
                return data;
            }

            return "";
        }

        public async Task Send(string Data)
        {
            for (int i = 0; i < Data.Length; i += ServerConnection.TRANSFER_RATE)
            {
                string chunk = Data.Substring(i, Math.Min(ServerConnection.TRANSFER_RATE, Data.Length));
                await _Send(chunk);
            }

            await _Send("--END--");
        }

        public async Task<string> Receive()
        {
            StringBuilder data = new StringBuilder();

            while (true)
            {
                string chunk = await _Receive();
                if (chunk == "--END--") break;

                if (chunk.Length > ServerConnection.TRANSFER_RATE)
                {
                    chunk = chunk.Substring(0, ServerConnection.TRANSFER_RATE);
                }

                data.Append(chunk);
            }

            return data.ToString();
        }

        public async Task<string> SendAndReceive(string Data)
        {
            await Send(Data);
            return await Receive();
        }

        public async IAsyncEnumerable<JsonNode> AdvancedSendAndReceive(
            string ModelName,
            string? Key = null,
            List<JsonNode>? PromptConversation = null,
            JsonNode? PromptParameters = null,
            JsonNode? UserParameters = null,
            string Service = "inference"
        )
        {
            PromptConversation ??= new List<JsonNode>();
            PromptParameters ??= new JsonObject();
            UserParameters ??= new JsonObject();

            if (ServerPublicKey == null)
            {
                await _SetServerPublicKey();
            }

            HashAlgorithm? h = Encryption.ParseHash(Config.Encryption_Hash);
            string conversationJson = JsonSerializer.Serialize(PromptConversation);
            JsonObject content = new JsonObject
            {
                ["model_name"] = ModelName,
                ["service"] = Service,
                ["key"] = (JsonNode?)(Key ?? Config.Service_DefaultAPIKey),
                ["prompt"] = new JsonObject
                {
                    ["conversation"] = JsonNode.Parse(conversationJson),
                    ["parameters"] = PromptParameters.DeepClone()
                },
                ["user_parameters"] = UserParameters.DeepClone()
            };
            string contentJson = content.ToJsonString();
            string encryptedContent = Encryption.Encrypt(h, ServerPublicKey!, contentJson, Config.Encryption_Threads);
            JsonObject data = new JsonObject
            {
                ["hash"] = Config.Encryption_Hash,
                ["public_key"] = PublicKeyStr!,
                ["version"] = ServerConnection.VERSION,
                ["content"] = encryptedContent
            };

            await Send(data.ToJsonString());

            JsonNode? redirectNode = null;
            JsonNode? lastToken = null;

            while (true)
            {
                string recvData = await Receive();
                JsonNode recvJson = JsonNode.Parse(recvData)!;
                string decrypted = Encryption.Decrypt(
                    Encryption.ParseHash(recvJson["hash"]!.GetValue<string>()),
                    PrivateKey!,
                    recvJson["data"]!.GetValue<string>(),
                    Config.Encryption_Threads
                );
                
                JsonNode token = JsonNode.Parse(decrypted)!;
                lastToken = token;

                if (token["redirect_to"] != null)
                {
                    redirectNode = token["redirect_to"];

                    yield return token;
                    break;
                }

                yield return token;

                if (token["ended"] != null && token["ended"]!.GetValue<bool>())
                {
                    break;
                }
            }

            if (redirectNode != null)
            {
                (string, string, int, bool)? previousConnection = null;

                string? rHost = redirectNode["host"]?.GetValue<string>();
                int? rPort = redirectNode["port"]?.GetValue<int>();
                string? rType = redirectNode["type"]?.GetValue<string>();
                bool? rSecure = redirectNode["secure"]?.GetValue<bool>();
                string? rModel = redirectNode["model"]?.GetValue<string>();

                if (rHost != null && rPort != null && rModel != null)
                {
                    previousConnection = CurrentConnection;
                    SockType = (rType == "ws") ? "websocket" : "";

                    await Connect(rHost, rPort.Value, rSecure ?? false);
                }

                IAsyncEnumerable<JsonNode> innerGen = AdvancedSendAndReceive(
                    rModel ?? ModelName,
                    Key,
                    PromptConversation,
                    PromptParameters,
                    UserParameters,
                    Service
                );

                try
                {
                    await foreach (JsonNode innerToken in innerGen)
                    {
                        yield return innerToken;
                    }
                }
                finally
                {
                    if (previousConnection != null)
                    {
                        SockType = previousConnection.Value.Item1;
                        await Connect(previousConnection.Value.Item2, previousConnection.Value.Item3, previousConnection.Value.Item4);
                    }
                }
            }
        }

        public async Task<List<string>> GetAvailableModels()
        {
            List<string>? models = null;

            await foreach (JsonNode token in AdvancedSendAndReceive("", Service: "get_available_models"))
            {
                if (token["models"] != null)
                {
                    models = token["models"]!.AsArray().GetValues<string>().ToList();
                }

                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return models ?? throw new Exception("Could not get models.");
        }

        public async Task<JsonNode> GetModelInfo(string ModelName)
        {
            JsonNode? modelInfo = null;

            await foreach (JsonNode token in AdvancedSendAndReceive(ModelName, Service: "get_model_info"))
            {
                if (token["config"] != null) modelInfo = token["config"];
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return modelInfo ?? throw new Exception("Could not get model information.");
        }

        public async Task<JsonNode> GetQueueData(string ModelName)
        {
            JsonNode? queueData = null;

            await foreach (JsonNode token in AdvancedSendAndReceive(ModelName, Service: "get_queue_data"))
            {
                if (token["queue"] != null) queueData = token["queue"];
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return queueData ?? throw new Exception("Could not get queue data.");
        }

        public async Task<string> CreateAPIKey(
            int Tokens = 0,
            bool ResetDaily = false,
            JsonNode? ExpireDate = null,
            List<string>? AllowedIPs = null,
            List<string>? PrioritizeModels = null,
            List<string>? Groups = null
        )
        {
            JsonObject promptParams = new JsonObject
            {
                ["tokens"] = Tokens,
                ["reset_daily"] = ResetDaily,
                ["expire_date"] = ExpireDate,
                ["allowed_ips"] = JsonSerializer.SerializeToNode(AllowedIPs ?? new List<string>()),
                ["prioritize_models"] = JsonSerializer.SerializeToNode(PrioritizeModels ?? new List<string>()),
                ["groups"] = JsonSerializer.SerializeToNode(Groups ?? new List<string>())
            };
            string? key = null;

            await foreach (JsonNode token in AdvancedSendAndReceive("", PromptParameters: promptParams, Service: "create_api_key"))
            {
                if (token["key"] != null) key = token["key"]!.GetValue<string>();
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return key ?? throw new Exception("Could not create new API key.");
        }

        public async Task DeleteAPIKey(string Key)
        {
            JsonObject promptParams = new JsonObject {["key"] = Key};

            await foreach (JsonNode token in AdvancedSendAndReceive("", PromptParameters: promptParams, Service: "delete_api_key"))
            {
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }
        }

        public async Task<JsonNode?> GetKeyData(string Key)
        {
            JsonObject promptParams = new JsonObject {["key"] = Key};
            JsonNode? keyData = null;

            await foreach (JsonNode token in AdvancedSendAndReceive("", PromptParameters: promptParams, Service: "get_key_data"))
            {
                if (token["key"] != null) keyData = token["key"];
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return keyData ?? throw new Exception("Could not fetch key data.");
        }

        public async Task BanUser(string Type, string Value)
        {
            JsonObject promptParams = new JsonObject
            {
                ["type"] = Type,
                ["value"] = Value
            };

            await foreach (JsonNode token in AdvancedSendAndReceive("", PromptParameters: promptParams, Service: "ban"))
            {
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }
        }

        public async Task PardonUser(string Type, string Value)
        {
            JsonObject promptParams = new JsonObject
            {
                ["type"] = Type,
                ["value"] = Value
            };

            await foreach (JsonNode token in AdvancedSendAndReceive("", PromptParameters: promptParams, Service: "pardon"))
            {
                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }
        }

        public async Task<List<JsonNode>> GetSupport()
        {
            List<JsonNode>? support = null;

            await foreach (JsonNode token in AdvancedSendAndReceive("", Service: "get_support"))
            {
                if (token["support"] != null)
                {
                    support = token["support"]!.AsArray().ToList()!;
                }

                if (token["errors"] != null && token["errors"]!.AsArray().Count > 0)
                {
                    throw new Exception($"Unexpected server error(s): {token["errors"]}");
                }
            }

            return support ?? throw new Exception("Could not fetch support data.");
        }
    }
}