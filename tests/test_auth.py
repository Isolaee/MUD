"""Tests for server.auth password hashing and verification."""

from server.auth import hash_password, verify_password


def test_hash_and_verify():
	stored = hash_password("mysecretpassword")
	assert verify_password("mysecretpassword", stored)


def test_wrong_password():
	stored = hash_password("correct")
	assert not verify_password("wrong", stored)


def test_different_hashes_for_same_password():
	"""Each call should produce a unique salt, so hashes differ."""
	h1 = hash_password("same")
	h2 = hash_password("same")
	assert h1 != h2
	# But both should verify correctly
	assert verify_password("same", h1)
	assert verify_password("same", h2)


def test_stored_format():
	stored = hash_password("test")
	assert "$" in stored
	salt_hex, hash_hex = stored.split("$", 1)
	# 32-byte salt = 64 hex chars
	assert len(salt_hex) == 64
	# SHA-256 = 32 bytes = 64 hex chars
	assert len(hash_hex) == 64


def test_verify_malformed_stored():
	"""Malformed stored string should not crash, just return False."""
	assert not verify_password("test", "no-dollar-sign")
	assert not verify_password("test", "")
