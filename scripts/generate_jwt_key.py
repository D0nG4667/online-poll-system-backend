#!/usr/bin/env python3
"""Generate JWT private key for environment variable."""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate RSA key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Serialize to PEM format
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

# Convert to single-line format for .env file
single_line = pem.decode().replace("\n", "\\n")

print("=" * 80)
print("JWT PRIVATE KEY FOR .ENV FILE")
print("=" * 80)
print("\nCopy the following line to your .env file:")
print(f"\nJWT_PRIVATE_KEY={single_line}")
print("\n" + "=" * 80)
