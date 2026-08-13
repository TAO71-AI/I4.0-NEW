using Godot;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading.Tasks;

using RandomNumberGenerator = System.Security.Cryptography.RandomNumberGenerator;

namespace TAO71.I4_0_Godot
{
    public partial class I40_Encryption : GodotObject
    {
        public static HashAlgorithm? _ParseHash(string HashName)
        {
            return HashName.ToLower() switch
            {
                "sha256" => SHA256.Create(),
                "sha384" => SHA384.Create(),
                "sha512" => SHA512.Create(),
                "sha1" => SHA1.Create(),
                "none" => null,
                _ => throw new ArgumentException("Invalid hash name.", nameof(HashName))
            };
        }

        public static (RSA PrivateKey, RSA PublicKey) _GenerateRSAKeys(int Size = 8192)
        {
            RSA priv = RSA.Create(Size);
            RSA pub = RSA.Create();
            pub.ImportSubjectPublicKeyInfo(priv.ExportSubjectPublicKeyInfo(), out _);

            return (priv, pub);
        }

        public static (byte[]? PrivatePemBase64, byte[]? PublicPemBase64) _SaveKeys(
            RSA? PrivateKey,
            string? PrivateFile,
            string PrivatePassword,
            RSA? PublicKey,
            string? PublicFile
        )
        {
            byte[]? privatePem = null;
            byte[]? publicPem = null;

            if (PrivateKey != null)
            {
                byte[] pkcs8 = PrivateKey.ExportEncryptedPkcs8PrivateKey(
                    Encoding.UTF8.GetBytes(PrivatePassword),
                    new PbeParameters(PbeEncryptionAlgorithm.Aes256Cbc, HashAlgorithmName.SHA256, 100000)
                );
                char[] pem = PemEncoding.Write("ENCRYPTED PRIVATE KEY", pkcs8);
                privatePem = Encoding.UTF8.GetBytes(new string(pem));

                if (!string.IsNullOrEmpty(PrivateFile))
                {
                    File.WriteAllBytes(PrivateFile, privatePem);
                }
            }

            if (PublicKey != null)
            {
                byte[] spki = PublicKey.ExportSubjectPublicKeyInfo();
                char[] pem = PemEncoding.Write("PUBLIC KEY", spki);
                publicPem = Encoding.UTF8.GetBytes(new string(pem));

                if (!string.IsNullOrEmpty(PublicFile))
                {
                    File.WriteAllBytes(PublicFile, publicPem);
                }
            }

            return (
                privatePem != null ? Encoding.UTF8.GetBytes(Convert.ToBase64String(privatePem)) : null,
                publicPem != null ? Encoding.UTF8.GetBytes(Convert.ToBase64String(publicPem)) : null
            );
        }

        public static (RSA? PrivateKey, RSA? PublicKey) _LoadKeysFromFile(
            string? PrivateFile,
            string PrivatePassword,
            string? PublicFile
        )
        {
            byte[]? privatePemBytes = !string.IsNullOrEmpty(PrivateFile) ? File.ReadAllBytes(PrivateFile) : null;
            byte[]? publicPemBytes = !string.IsNullOrEmpty(PublicFile) ? File.ReadAllBytes(PublicFile) : null;

            return _LoadKeysFromContent(privatePemBytes, PrivatePassword, publicPemBytes);
        }

        public static (RSA? PrivateKey, RSA? PublicKey) _LoadKeysFromContent(
            byte[]? PrivateContent,
            string PrivatePassword,
            byte[]? PublicContent
        )
        {
            RSA? privateKey = null;
            RSA? publicKey = null;

            if (PrivateContent != null)
            {
                privateKey = RSA.Create();
                string pemStr = Encoding.UTF8.GetString(PrivateContent);
                privateKey.ImportFromEncryptedPem(pemStr, Encoding.UTF8.GetBytes(PrivatePassword));
            }

            if (PublicContent != null)
            {
                publicKey = RSA.Create();
                string pemStr = Encoding.UTF8.GetString(PublicContent);
                publicKey.ImportFromPem(pemStr);
            }

            return (privateKey, publicKey);
        }

        public static string _EncryptBasic(HashAlgorithm? Hash, RSA PublicKey, string Data, int MaxThreads)
        {
            byte[] encryptedBytes = _Encrypt(Hash, PublicKey, Encoding.UTF8.GetBytes(Data), MaxThreads);
            return Convert.ToBase64String(encryptedBytes);
        }

        public static byte[] _EncryptBasic(HashAlgorithm? Hash, RSA PublicKey, byte[] Data, int MaxThreads)
        {
            byte[] encryptedBytes = _Encrypt(Hash, PublicKey, Data, MaxThreads);
            return Encoding.UTF8.GetBytes(Convert.ToBase64String(encryptedBytes));
        }

        private static byte[] _Encrypt(HashAlgorithm? Hash, RSA PublicKey, byte[] Data, int MaxThreads)
        {
            if (Hash == null) return Data;

            byte[] key = new byte[32];
            RandomNumberGenerator.Fill(key);

            RSAEncryptionPadding padding = GetPadding(Hash);
            byte[] encryptedKey = PublicKey.Encrypt(key, padding);

            byte[] nonce = new byte[16];
            RandomNumberGenerator.Fill(nonce);

            int chunkSize = 1024 * 1024;
            int numChunks = (Data.Length + chunkSize - 1) / chunkSize;
            byte[][] results = new byte[numChunks][];

            Parallel.For(0, numChunks, new ParallelOptions { MaxDegreeOfParallelism = MaxThreads }, idx =>
            {
                int offset = idx * chunkSize;
                int length = Math.Min(chunkSize, Data.Length - offset);
                byte[] chunk = new byte[length];
                Array.Copy(Data, offset, chunk, 0, length);

                results[idx] = AesCtrTransform(key, nonce, chunk, idx, chunkSize);
            });

            using MemoryStream ms = new MemoryStream();
            using BinaryWriter bw = new BinaryWriter(ms);
            
            byte[] lenKeyBytes = BitConverter.GetBytes((uint)encryptedKey.Length);
            if (BitConverter.IsLittleEndian) Array.Reverse(lenKeyBytes); // Python usa Big Endian

            bw.Write(lenKeyBytes);
            bw.Write(encryptedKey);
            bw.Write(nonce);

            foreach (byte[] chunk in results)
            {
                bw.Write(chunk);
            }

            return ms.ToArray();
        }

        public static string _DecryptBasic(HashAlgorithm? Hash, RSA PrivateKey, string Data, int MaxThreads)
        {
            byte[] decryptedBytes = _Decrypt(Hash, PrivateKey, Convert.FromBase64String(Data), MaxThreads);
            return Encoding.UTF8.GetString(decryptedBytes);
        }

        public static byte[] _DecryptBasic(HashAlgorithm? Hash, RSA PrivateKey, byte[] Data, int MaxThreads)
        {
            string base64Str = Encoding.UTF8.GetString(Data);
            return _Decrypt(Hash, PrivateKey, Convert.FromBase64String(base64Str), MaxThreads);
        }

        private static byte[] _Decrypt(HashAlgorithm? Hash, RSA PrivateKey, byte[] Data, int MaxThreads)
        {
            if (Hash == null) return Data;

            using MemoryStream ms = new MemoryStream(Data);
            using BinaryReader br = new BinaryReader(ms);

            byte[] lenKeyBytes = br.ReadBytes(4);
            if (BitConverter.IsLittleEndian) Array.Reverse(lenKeyBytes);
            uint lenKey = BitConverter.ToUInt32(lenKeyBytes);

            byte[] encryptedKey = br.ReadBytes((int)lenKey);
            byte[] nonce = br.ReadBytes(16);
            byte[] ciphertext = br.ReadBytes((int)(ms.Length - ms.Position));

            RSAEncryptionPadding padding = GetPadding(Hash);
            byte[] key = PrivateKey.Decrypt(encryptedKey, padding);

            int chunkSize = 1024 * 1024;
            int numChunks = (ciphertext.Length + chunkSize - 1) / chunkSize;
            byte[][] results = new byte[numChunks][];

            Parallel.For(0, numChunks, new ParallelOptions { MaxDegreeOfParallelism = MaxThreads }, idx =>
            {
                int offset = idx * chunkSize;
                int length = Math.Min(chunkSize, ciphertext.Length - offset);
                byte[] chunk = new byte[length];
                Array.Copy(ciphertext, offset, chunk, 0, length);

                results[idx] = AesCtrTransform(key, nonce, chunk, idx, chunkSize);
            });

            using MemoryStream outMs = new MemoryStream();
            foreach (byte[] chunk in results)
            {
                outMs.Write(chunk, 0, chunk.Length);
            }

            return outMs.ToArray();
        }

        private static RSAEncryptionPadding GetPadding(HashAlgorithm Hash)
        {
            if (Hash is SHA1) return RSAEncryptionPadding.OaepSHA1;
            if (Hash is SHA256) return RSAEncryptionPadding.OaepSHA256;
            if (Hash is SHA384) return RSAEncryptionPadding.OaepSHA384;
            if (Hash is SHA512) return RSAEncryptionPadding.OaepSHA512;
            return RSAEncryptionPadding.OaepSHA256;
        }

        private static byte[] AesCtrTransform(byte[] key, byte[] nonce, byte[] data, long chunkIdx, int chunkSize)
        {
            byte[] nonceLe = new byte[16];
            Array.Copy(nonce, 0, nonceLe, 0, 16);
            Array.Reverse(nonceLe);

            byte[] nonceLeUnsigned = new byte[17];
            Array.Copy(nonceLe, 0, nonceLeUnsigned, 0, 16);

            BigInteger nonceBigInt = new BigInteger(nonceLeUnsigned);

            long blocksPerChunk = chunkSize / 16;
            BigInteger initialCounter = nonceBigInt + chunkIdx * blocksPerChunk;

            using Aes aes = Aes.Create();
            aes.Mode = CipherMode.ECB;
            aes.Padding = PaddingMode.None;
            aes.Key = key;

            using ICryptoTransform encryptor = aes.CreateEncryptor();

            byte[] output = new byte[data.Length];
            byte[] counterBlock = new byte[16];
            byte[] keystreamBlock = new byte[16];

            BigInteger counter = initialCounter;

            for (int i = 0; i < data.Length; i += 16)
            {
                byte[] counterBytes = ToBigEndianBytes(counter, 16);
                encryptor.TransformBlock(counterBytes, 0, 16, keystreamBlock, 0);

                int blockLen = Math.Min(16, data.Length - i);

                for (int j = 0; j < blockLen; j++)
                {
                    output[i + j] = (byte)(data[i + j] ^ keystreamBlock[j]);
                }

                counter++;
            }

            return output;
        }

        private static byte[] ToBigEndianBytes(BigInteger value, int length)
        {
            byte[] bytes = value.ToByteArray();
            byte[] result = new byte[length];

            int copyLen = Math.Min(bytes.Length, length);

            for (int i = 0; i < copyLen; i++)
            {
                result[length - 1 - i] = bytes[i];
            }

            return result;
        }

        public static string _HashContent(string Content, HashAlgorithm Hash)
        {
            return _HashContent(Encoding.UTF8.GetBytes(Content), Hash);
        }

        public static string _HashContent(byte[] Content, HashAlgorithm Hash)
        {
            if (Hash == null)
            {
                throw new ArgumentNullException(nameof(Hash), "Hash cannot be null.");
            }

            byte[] hashBytes = Hash.ComputeHash(Content);
            return BitConverter.ToString(hashBytes).Replace("-", "").ToLower();
        }

        // Godot-adapted functions

        public static Godot.Collections.Array<byte[]> GenerateRSAKeys(int Size = 8192)
        {
            (RSA priv, RSA pub) keys = _GenerateRSAKeys(Size);
            (byte[]? priv, byte[]? pub) savedKeys = _SaveKeys(keys.priv, null, "", keys.pub, null);

            return new Godot.Collections.Array<byte[]>()
            {
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.priv!)),
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.pub!))
            };
        }

        public static Godot.Collections.Array<byte[]> SaveKeys(byte[] PrivateKey, string PrivateFile, string PrivatePassword, byte[] PublicKey, string PublicFile)
        {
            if (PrivateFile.Trim().Length == 0)
            {
                PrivateFile = null;
            }

            if (PublicFile.Trim().Length == 0)
            {
                PublicFile = null;
            }

            if (PrivateKey.Length == 0)
            {
                PrivateKey = null;
            }

            if (PublicKey.Length == 0)
            {
                PublicKey = null;
            }

            (RSA priv, RSA pub) keys = _LoadKeysFromContent(PrivateKey, PrivatePassword, PublicKey);
            (byte[]? priv, byte[]? pub) savedKeys = _SaveKeys(keys.priv, PrivateFile, PrivatePassword, keys.pub, PublicFile);

            if (savedKeys.priv == null)
            {
                savedKeys.priv = new byte[0];
            }

            if (savedKeys.pub == null)
            {
                savedKeys.pub = new byte[0];
            }

            return new Godot.Collections.Array<byte[]>()
            {
                savedKeys.priv!,
                savedKeys.pub!
            };
        }

        public static Godot.Collections.Array<byte[]> LoadKeysFromContent(string PrivateContent, string PrivatePassword, string PublicContent)
        {
            (byte[]? priv, byte[]? pub) keys = (null, null);

            if (PrivateContent.Trim().Length > 0)
            {
                keys.priv = Encoding.UTF8.GetBytes(PrivateContent);
            }

            if (PublicContent.Trim().Length > 0)
            {
                keys.pub = Encoding.UTF8.GetBytes(PublicContent);
            }

            (RSA? priv, RSA? pub) loadedKeys = _LoadKeysFromContent(keys.priv, PrivatePassword, keys.pub);
            (byte[]? priv, byte[]? pub) savedKeys = _SaveKeys(loadedKeys.priv, null, PrivatePassword, loadedKeys.pub, null);

            if (savedKeys.priv == null)
            {
                savedKeys.priv = new byte[0];
            }

            if (savedKeys.pub == null)
            {
                savedKeys.pub = new byte[0];
            }

            return new Godot.Collections.Array<byte[]>()
            {
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.priv!)),
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.pub!))
            };
        }

        public static Godot.Collections.Array<byte[]> LoadKeysFromFile(string PrivateFile, string PrivatePassword, string PublicFile)
        {
            if (PrivateFile.Trim().Length == 0)
            {
                PrivateFile = null;
            }

            if (PublicFile.Trim().Length == 0)
            {
                PublicFile = null;
            }

            (RSA priv, RSA pub) keys = _LoadKeysFromFile(PrivateFile, PrivatePassword, PublicFile);
            (byte[]? priv, byte[]? pub) savedKeys = _SaveKeys(keys.priv, null, PrivatePassword, keys.pub, null);

            if (savedKeys.priv == null)
            {
                savedKeys.priv = new byte[0];
            }

            if (savedKeys.pub == null)
            {
                savedKeys.pub = new byte[0];
            }

            return new Godot.Collections.Array<byte[]>()
            {
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.priv!)),
                Convert.FromBase64String(Encoding.UTF8.GetString(savedKeys.pub!))
            };
        }

        public static string Encrypt(string Hash, byte[] PublicKey, string Data, int MaxThreads)
        {
            return _EncryptBasic(
                _ParseHash(Hash),
                _LoadKeysFromContent(null, "", PublicKey).PublicKey,
                Data,
                MaxThreads
            );
        }

        public static byte[] Encrypt(string Hash, byte[] PublicKey, byte[] Data, int MaxThreads)
        {
            return _EncryptBasic(
                _ParseHash(Hash),
                _LoadKeysFromContent(null, "", PublicKey).PublicKey,
                Data,
                MaxThreads
            );
        }

        public static string Decrypt(string Hash, byte[] PrivateKey, string Data, int MaxThreads)
        {
            return _DecryptBasic(
                _ParseHash(Hash),
                _LoadKeysFromContent(PrivateKey, "", null).PrivateKey,
                Data,
                MaxThreads
            );
        }

        public static byte[] Decrypt(string Hash, byte[] PrivateKey, byte[] Data, int MaxThreads)
        {
            return _DecryptBasic(
                _ParseHash(Hash),
                _LoadKeysFromContent(PrivateKey, "", null).PrivateKey,
                Data,
                MaxThreads
            );
        }

        public static string HashContent(string Content, string Hash)
        {
            return _HashContent(Content, _ParseHash(Hash));
        }

        public static string HashContent(byte[] Content, string Hash)
        {
            return _HashContent(Content, _ParseHash(Hash));
        }
    }
}
