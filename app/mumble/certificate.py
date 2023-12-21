from app.mumble.schema import Certificate
"""
X.509 Certificate support for Mumble client authentication
Matt Currie
"""


import asyncio
import datetime
import os
import logging
import traceback

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
import aiofiles


logger = logging.getLogger(__name__)


async def create_self_signed_cert(certs_path: str, cn: str) -> Certificate:

    dns_name = cn
    certfile = f"{cn}.pem"
    keyfile = f"{cn}.key"

    # ensure path exists
    if not os.path.exists(certs_path):
        os.makedirs(certs_path, exist_ok=True)

    cert = Certificate(
        common_name=cn,
        certfile=os.path.join(certs_path, certfile),
        keyfile=os.path.join(certs_path, keyfile)
    )

    # Generate private key (RSA)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"CA"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"BC"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Vancouver"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Mumble"),
        x509.NameAttribute(NameOID.COMMON_NAME, cn),
    ])

    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(dns_name)]),
            critical=False,
        )
        # Sign the certificate with our private key
        .sign(private_key, hashes.SHA256())
    )

    # Write our certificate out to disk.
    async with aiofiles.open(cert.certfile, "wb") as f:
        await f.write(certificate.public_bytes(Encoding.PEM))
        logger.debug(f"wrote certificate: {cert.certfile}")

    # Also write the private key
    async with aiofiles.open(cert.keyfile, "wb") as f:
        # Use encryption for private key - this is optional
        await f.write(private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption()  # Or use BestAvailableEncryption for password-protected encryption
        ))
        logger.debug(f"wrote private key: {cert.keyfile}")

    return cert


async def get_certificate(certs_path: str, cn: str) -> Certificate:

    try:
        logger.debug(f"get_certificate({certs_path}, {cn})")
        certfile = f"{cn}.pem"
        certfile_path = os.path.join(certs_path, certfile)
        keyfile = f"{cn}.key"
        keyfile_path = os.path.join(certs_path, keyfile)

        if os.path.exists(certfile_path) and os.path.exists(keyfile_path):
            return Certificate(
                common_name=cn,
                certfile=certfile_path,
                keyfile=keyfile_path
            )

        return await create_self_signed_cert(certs_path, cn)

    except Exception as e:
        logger.error(f"get_certificate() exception {type(e)}: {e} {traceback.format_exc()}")
        raise e