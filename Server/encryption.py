from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor
import base64
import os
import Utilities.logs as logs

def ParseHash(HashName: str) -> hashes.HashAlgorithm:
    if (HashName == "sha224"):
        return hashes.SHA224()
    elif (HashName == "sha256"):
        return hashes.SHA256()
    elif (HashName == "sha384"):
        return hashes.SHA384()
    elif (HashName == "sha512"):
        return hashes.SHA512()
    elif (HashName == "sha1"):
        return hashes.SHA1()
    
    raise ValueError("Invalid hash name.")

def GenerateRSAKeys(Size: int = 8192) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    logs.WriteLog(logs.INFO, "[encryption] Generating public-private key pair.")

    if (Size < 2048):
        logs.PrintLog(logs.WARNING, "[encryption] Keys size is less than 2048. Errors are expected.")

    privateKey = rsa.generate_private_key(65537, Size)
    publicKey = privateKey.public_key()

    return privateKey, publicKey

def SaveKeys(
    PrivateKey: rsa.RSAPrivateKey | None,
    PrivateFile: str | None,
    PrivatePassword: str,
    PublicKey: rsa.RSAPublicKey | None,
    PublicFile: str | None
) -> tuple[bytes | None, bytes | None]:
    logs.WriteLog(logs.INFO, "[encryption] Saving public-private key pair to disk (or getting values).")

    if (len(PrivatePassword.strip()) == 0 and PrivateKey is not None):
        logs.WriteLog(logs.WARNING, "[encryption] Private password is not secure or empty.")

    privatePem = PrivateKey.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.BestAvailableEncryption(PrivatePassword.encode("utf-8"))
    ) if (PrivateKey is not None) else None
    publicPem = PublicKey.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    ) if (PublicKey is not None) else None

    if (PrivateKey is not None and PrivateFile is not None):
        with open(PrivateFile, "wb") as f:
            f.write(privatePem)
    
    if (PublicKey is not None and PublicFile is not None):
        with open(PublicFile, "wb") as f:
            f.write(publicPem)
    
    return (
        base64.b64encode(privatePem) if (privatePem is not None) else None,
        base64.b64encode(publicPem) if (publicPem is not None) else None
    )

def LoadKeys(
    PrivateFile: str,
    PrivatePassword: str,
    PublicFile: str
) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    logs.WriteLog(logs.INFO, "[encryption] Loading public-private key pair from disk.")

    with open(PrivateFile, "rb") as f:
        privatePem = f.read()
    
    with open(PublicFile, "rb") as f:
        publicPem = f.read()
    
    privateKey = serialization.load_pem_private_key(
        privatePem,
        password = PrivatePassword.encode("utf-8"),
        backend = default_backend()
    )
    publicKey = serialization.load_der_public_key(
        publicPem,
        backend = default_backend()
    )

    return (privateKey, publicKey)

def Encrypt(Hash: hashes.HashAlgorithm, PublicKey: rsa.RSAPublicKey, Data: str | bytes) -> str | bytes:
    if (isinstance(Data, bytes)):
        returnAsBytes = True
        data = Data
    else:
        returnAsBytes = False
        data = Data.encode("utf-8")
    
    key = os.urandom(32)
    encriptedKey = PublicKey.encrypt(
        key,
        padding.OAEP(
            mgf = padding.MGF1(Hash),
            algorithm = Hash,
            label = None
        )
    )

    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend = default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()

    result = (
        len(encriptedKey).to_bytes(4, "big") +
        encriptedKey +
        nonce +
        ciphertext
    )
    result = base64.b64encode(result)

    if (returnAsBytes):
        return result
    
    return result.decode("utf-8")

def Decrypt(Hash: hashes.HashAlgorithm, PrivateKey: rsa.RSAPrivateKey, Data: str | bytes, MaxThreads: int) -> str | bytes:
    def _decrypt(Key: bytes, Nonce: bytes, Idx: int, Chunk: bytes, ChunkSize: int) -> tuple[int, bytes]:
        nonceInt = int.from_bytes(Nonce, "big")
        blocksPerChunks = ChunkSize // 16
        offset = Idx * blocksPerChunks

        newNonce = (nonceInt + offset).to_bytes(16, "big")
        cipher = Cipher(algorithms.AES(Key), modes.CTR(newNonce), backend = default_backend())
        decryptor = cipher.decryptor()

        return (Idx, decryptor.update(Chunk) + decryptor.finalize())

    if (isinstance(Data, bytes)):
        returnAsBytes = True
        data = Data
    else:
        returnAsBytes = False
        data = Data.encode("utf-8")
    
    data = base64.b64decode(data)
    
    lenKey = int.from_bytes(data[:4], "big")
    encryptedKey = data[4:4 + lenKey]
    nonce = data[4 + lenKey:4 + lenKey + 16]
    ciphertext = data[4 + lenKey + 16:]

    key = PrivateKey.decrypt(
        encryptedKey,
        padding.OAEP(
            mgf = padding.MGF1(Hash),
            algorithm = Hash,
            label = None
        )
    )
    chunkSize = 1024 * 1024
    chunks = [
        ciphertext[i:i + chunkSize]
        for i in range(0, len(ciphertext), chunkSize)
    ]

    results = [None] * len(chunks)

    with ThreadPoolExecutor(max_workers = MaxThreads) as executor:
        futures = [
            executor.submit(_decrypt, key, nonce, idx, chunk, chunkSize)
            for idx, chunk in enumerate(chunks)
        ]

        for future in futures:
            idx, plaintext = future.result()
            results[idx] = plaintext

    if (returnAsBytes):
        return b"".join(results)
    
    return "".join([p.decode("utf-8") for p in results])