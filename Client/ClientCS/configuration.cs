using System.Reflection;
using System.Collections.Generic;

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
            Dictionary<string, object?> d = new Dictionary<string, object?>();
            PropertyInfo[] properties = this.GetType().GetProperties();

            foreach (PropertyInfo prop in properties)
            {
                d[prop.Name] = prop.GetValue(this);
            }

            if (!SavePublicKey)
            {
                d["Encryption_PublicKey"] = null;
                d["Encryption_PrivateKey"] = null;
            }

            return d;
        }

        public static ClientConfiguration FromDict(Dictionary<string, object?> Dict)
        {
            ClientConfiguration instance = new ClientConfiguration();

            if (Dict == null)
            {
                throw new ArgumentNullException(nameof(Dict));
            }

            foreach (KeyValuePair<string, object?> kvp in Dict)
            {
                PropertyInfo? prop = instance.GetType().GetProperty(kvp.Key);

                if (prop != null && prop.CanWrite)
                {
                    try
                    {
                        prop.SetValue(instance, kvp.Value);
                    }
                    catch
                    {
                        
                    }
                }
            }

            return instance;
        }
    }
}