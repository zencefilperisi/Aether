import os
import sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Path setup
sys.path.append(os.getcwd())
from utility.keygen import AetherKeyGen

class AetherVault:
    def __init__(self):
        self.keygen = AetherKeyGen()

    def encrypt_file(self, file_path):
        """Encrypts a file using an Aether-generated key."""
        # 1. Aether'den 256-bit (32 byte) anahtar üret
        key = self.keygen.generate_bytes(32)
        aesgcm = AESGCM(key)
        
        # 2. Rastgele bir Nonce (IV) üret (Yine Aether üzerinden)
        nonce = self.keygen.generate_bytes(12)
        
        # 3. Dosyayı oku
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # 4. Şifrele
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # 5. Şifreli dosyayı kaydet (.aether uzantısıyla)
        with open(file_path + ".aether", 'wb') as f:
            f.write(nonce + ciphertext)
            
        print(f"\n[+] File Encrypted: {file_path}.aether")
        print(f"[!] SAVE THIS KEY (HEX): {key.hex().upper()}")
        return key.hex()

    def decrypt_file(self, encrypted_path, hex_key):
        """Decrypts an .aether file using the provided hex key."""
        key = bytes.fromhex(hex_key)
        aesgcm = AESGCM(key)
        
        with open(encrypted_path, 'rb') as f:
            file_data = f.read()
            
        # İlk 12 byte Nonce, kalanı şifreli veri
        nonce = file_data[:12]
        ciphertext = file_data[12:]
        
        # Çöz ve orijinal ismine geri döndür
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
        original_path = encrypted_path.replace(".aether", "_decrypted")
        
        with open(original_path, 'wb') as f:
            f.write(decrypted_data)
            
        print(f"\n[+] File Decrypted: {original_path}")

if __name__ == "__main__":
    vault = AetherVault()
    print("--- AETHER VAULT: SECURE FILE SYSTEM ---")
    # Test için bir dosya yolu verilebilir veya küçük bir TXT oluşturulabilir
    mode = input("Select Mode (E: Encrypt / D: Decrypt): ").upper()
    
    if mode == "E":
        path = input("Enter file path to encrypt: ")
        vault.encrypt_file(path)
    elif mode == "D":
        path = input("Enter .aether file path: ")
        key = input("Enter Hex Key: ")
        vault.decrypt_file(path, key)