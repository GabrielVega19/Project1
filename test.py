from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA3_512
from Crypto.Signature import PKCS1_v1_5


message = "test"
privKey = RSA.generate(2048)
pubKey = privKey.public_key()

mHash = SHA3_512.new(message.encode())
sHash = PKCS1_v1_5.new(privKey).sign(mHash)


h = SHA3_512.new(message.encode())
verifier = PKCS1_v1_5.new(pubKey)
if verifier.verify(h, sHash):
    print ("The signature is authentic.")
else:
   print ("The signature is not authentic.")