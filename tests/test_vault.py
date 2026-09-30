"""Unit tests for the AetherVault key manager and file encryption.

These run without the Rust core: the vault falls back to the OS CSPRNG for
key material, so the cryptographic guarantees (confidentiality, integrity,
passphrase protection) are exercised on every machine.
"""

import os
import tempfile

import pytest

from utility.vault import AetherVault


@pytest.fixture
def vault(tmp_path):
    return AetherVault(keystore_path=str(tmp_path / "keystore.json"))


def test_store_and_load_key_roundtrip(vault):
    key = vault.store_key("svc-a", passphrase="correct horse")
    loaded = vault.load_key("svc-a", passphrase="correct horse")
    assert key == loaded
    assert len(key) == 32


def test_wrong_passphrase_rejected(vault):
    vault.store_key("svc-a", passphrase="right")
    with pytest.raises(Exception):
        vault.load_key("svc-a", passphrase="wrong")


def test_list_keys(vault):
    vault.store_key("one", passphrase="p")
    vault.store_key("two", passphrase="p")
    assert vault.list_keys() == ["one", "two"]


def test_missing_key_raises(vault):
    with pytest.raises(KeyError):
        vault.load_key("nope", passphrase="p")


def test_file_encrypt_decrypt_roundtrip(vault, tmp_path):
    plaintext = b"the quick brown fox" * 100
    src = tmp_path / "data.bin"
    src.write_bytes(plaintext)

    enc = vault.encrypt_file(str(src), key_name="filekey", passphrase="pw")
    assert enc.endswith(".aether")
    # ciphertext must not contain the plaintext
    assert plaintext not in (tmp_path / "data.bin.aether").read_bytes()

    dec = vault.decrypt_file(enc, passphrase="pw")
    assert open(dec, "rb").read() == plaintext


def test_file_decrypt_wrong_passphrase(vault, tmp_path):
    src = tmp_path / "data.bin"
    src.write_bytes(b"secret")
    enc = vault.encrypt_file(str(src), key_name="k", passphrase="right")
    with pytest.raises(Exception):
        vault.decrypt_file(enc, passphrase="wrong")


def test_tampered_file_rejected(vault, tmp_path):
    src = tmp_path / "data.bin"
    src.write_bytes(b"secret payload")
    enc = vault.encrypt_file(str(src), key_name="k", passphrase="pw")

    blob = bytearray(open(enc, "rb").read())
    blob[-1] ^= 0x01  # flip one bit of the auth tag / ciphertext
    open(enc, "wb").write(blob)

    with pytest.raises(Exception):
        vault.decrypt_file(enc, passphrase="pw")


def test_keys_are_unique(vault):
    k1 = vault.store_key("a", passphrase="p")
    k2 = vault.store_key("b", passphrase="p")
    assert k1 != k2
