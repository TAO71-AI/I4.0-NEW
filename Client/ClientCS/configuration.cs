using System;
using System.Reflection;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace TAO71.I4_0
{
    public class ClientConfiguration
    {
        // Encryption configuration
        public byte[]? Encryption_PublicKey = null;
        public byte[]? Encryption_PrivateKey = null;
        public string Encryption_PrivateKeyPassword = "changeme";
        public int Encryption_Threads = 1;
        public int Encryption_RSASize = 4096;
        public string Encryption_Hash = "sha512";

        // Service configuration
        public string Service_DefaultAPIKey = "nokey";

        // Other configuration
        public float PingInterval = 20;

        public Dictionary<string, object?> ToDict(bool SavePublicKey = false)
        {
            Dictionary<string, object?> d = JsonConvert.DeserializeObject<Dictionary<string, object?>>(JsonConvert.SerializeObject(this))!;

            if (!SavePublicKey)
            {
                d["Encryption_PublicKey"] = null;
                d["Encryption_PrivateKey"] = null;
            }

            return d;
        }

        public static ClientConfiguration FromDict(Dictionary<string, object?> Dict)
        {
            return JsonConvert.DeserializeObject<ClientConfiguration>(JsonConvert.SerializeObject(Dict))!;
        }
    }
}