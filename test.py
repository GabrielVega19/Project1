from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA3_512
from Crypto.Signature import PKCS1_v1_5


message = "test"
with open("ClientKeys/client.key", "rb") as file:
    k = file.read()
    privKey = RSA.import_key(k)
    print(k)
with open("ClientKeys/client.pub", "rb") as file:
    pk = file.read()
    print(k)
    pubKey = RSA.import_key(pk)

mHash = SHA3_512.new(message.encode())
sHash = PKCS1_v1_5.new(privKey).sign(mHash)


h = SHA3_512.new(message.encode())
verifier = PKCS1_v1_5.new(pubKey)
if verifier.verify(h, sHash):
    print("Authenticated")