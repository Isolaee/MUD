"""Password hashing and verification using PBKDF2-HMAC-SHA256.

Uses only the Python standard library (hashlib + os).
Storage format: ``salt_hex$hash_hex`` in a single text column.
"""

import hashlib
import hmac
import os

ITERATIONS = 600_000  # OWASP 2023 recommendation for PBKDF2-SHA256
SALT_LENGTH = 32  # bytes


def hash_password(password: str) -> str:
	"""Hash a password and return ``'salt_hex$hash_hex'``."""
	salt = os.urandom(SALT_LENGTH)
	h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
	return salt.hex() + "$" + h.hex()


def verify_password(password: str, stored: str) -> bool:
	"""Verify *password* against a stored ``'salt_hex$hash_hex'`` string."""
	try:
		salt_hex, hash_hex = stored.split("$", 1)
	except ValueError:
		return False
	salt = bytes.fromhex(salt_hex)
	h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
	return hmac.compare_digest(h.hex(), hash_hex)
