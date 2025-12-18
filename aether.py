import argparse
import sys
import os
import subprocess

# Path setup to ensure local modules are found
sys.path.append(os.getcwd())

try:
    from utility.vault import AetherVault
    from utility.keygen import AetherKeyGen
except ImportError:
    print("ERROR: Could not find utility modules. Ensure you are running from the project root.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="AETHER: High-Entropy Chaos-Based Security Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example Usage:\n"
               "  python aether.py --gen-key\n"
               "  python aether.py --encrypt secret.txt\n"
               "  python aether.py --decrypt secret.txt.aether\n"
               "  python aether.py --visualize"
    )
    
    # Command groups
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gen-key", action="store_true", help="Generate a 256-bit secure Hex key")
    group.add_argument("--gen-phrase", action="store_true", help="Generate a 12-word recovery phrase")
    group.add_argument("--encrypt", metavar="FILE", help="Encrypt a file using chaotic entropy")
    group.add_argument("--decrypt", metavar="FILE", help="Decrypt an .aether file (requires key)")
    group.add_argument("--visualize", action="store_true", help="Launch the 3D Chaos Visualizer")

    args = parser.parse_args()
    
    print("\n" + "="*50)
    print("          AETHER SECURITY COMMAND CENTER")
    print("="*50)

    try:
        if args.gen_key:
            key = AetherKeyGen().generate_hex_key()
            print(f"[SUCCESS] New 256-bit Key Generated:")
            print(f"\n{key}\n")
            print("[!] WARNING: Save this key manually. It is NOT stored anywhere.")
        
        elif args.gen_phrase:
            phrase = AetherKeyGen().generate_passphrase()
            print(f"[SUCCESS] Mnemonic Phrase Generated:")
            print(f"\n{phrase}\n")
            
        elif args.encrypt:
            if not os.path.exists(args.encrypt):
                print(f"[ERROR] File not found: {args.encrypt}")
                return
            vault = AetherVault()
            vault.encrypt_file(args.encrypt)
            print("\n[!] Encryption complete. Delete the original file only after saving the key.")
            
        elif args.decrypt:
            if not os.path.exists(args.decrypt):
                print(f"[ERROR] File not found: {args.decrypt}")
                return
            key = input("Enter the Hex Key for decryption: ").strip()
            vault = AetherVault()
            vault.decrypt_file(args.decrypt, key)
            
        elif args.visualize:
            print("[*] Initializing Chaos Engine and Visualizer...")
            # Using -m to run as a module
            subprocess.run(["python", "-m", "tests.visualize_chaos"])

    except Exception as e:
        print(f"[CRITICAL ERROR] {str(e)}")

    print("="*50 + "\n")

if __name__ == "__main__":
    main()