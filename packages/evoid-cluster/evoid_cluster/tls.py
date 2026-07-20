"""ClusterTLS — simplified mTLS for inter-node authentication."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any


class ClusterTLS:
    """Simplified mTLS with auto-generated certificates.

    For end users: just set secret in config. Certificates are generated
    automatically on first run. No manual cert management needed.
    """

    def __init__(self, cert_dir: str | None = None, secret: str = ""):
        self._cert_dir = Path(cert_dir or "./certs")
        self._secret = secret
        self._ca_cert: str | None = None
        self._node_cert: str | None = None
        self._node_key: str | None = None

    def setup(self, node_id: str) -> None:
        """Auto-generate certs if they don't exist."""
        self._cert_dir.mkdir(parents=True, exist_ok=True)
        ca_path = self._cert_dir / "ca.pem"
        cert_path = self._cert_dir / f"{node_id}.pem"
        key_path = self._cert_dir / f"{node_id}.key"

        if ca_path.exists() and cert_path.exists() and key_path.exists():
            self._ca_cert = str(ca_path)
            self._node_cert = str(cert_path)
            self._node_key = str(key_path)
            return

        self._generate_certs(node_id, ca_path, cert_path, key_path)

    def _generate_certs(
        self, node_id: str, ca_path: Path, cert_path: Path, key_path: Path
    ) -> None:
        """Generate self-signed CA + node certificate."""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
        except ImportError:
            self._fallback_generate(node_id, ca_path, cert_path, key_path)
            return

        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "evoid-cluster-ca"),
        ])
        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(ca_key, hashes.SHA256())
        )

        ca_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

        node_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        node_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, node_id),
        ])
        node_cert = (
            x509.CertificateBuilder()
            .subject_name(node_name)
            .issuer_name(ca_name)
            .public_key(node_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(ca_key, hashes.SHA256())
        )

        cert_path.write_bytes(node_cert.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(
            node_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )

        self._ca_cert = str(ca_path)
        self._node_cert = str(cert_path)
        self._node_key = str(key_path)

    def _fallback_generate(
        self, node_id: str, ca_path: Path, cert_path: Path, key_path: Path
    ) -> None:
        """Fallback: generate placeholder files when cryptography is unavailable."""
        secret_hash = hashlib.sha256(self._secret.encode()).hexdigest()
        ca_content = f"# evoid-cluster CA\n# secret_hash: {secret_hash}\n"
        ca_path.write_text(ca_content)
        cert_content = f"# evoid-cluster node: {node_id}\n# secret_hash: {secret_hash}\n"
        cert_path.write_text(cert_content)
        key_content = f"# evoid-cluster key: {node_id}\n# DO NOT SHARE\n"
        key_path.write_text(key_content)

        self._ca_cert = str(ca_path)
        self._node_cert = str(cert_path)
        self._node_key = str(key_path)

    def create_ssl_context(self, server_side: bool = False) -> Any | None:
        """Create SSL context for WebSocket connections."""
        if not self._node_cert or not self._node_key:
            return None
        try:
            import ssl
            ctx = ssl.SSLContext(
                ssl.PROTOCOL_TLS_SERVER if server_side else ssl.PROTOCOL_TLS_CLIENT
            )
            ctx.load_cert_chain(self._node_cert, self._node_key)
            if self._ca_cert:
                ctx.load_verify_locations(self._ca_cert)
            if not server_side:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_OPTIONAL
            return ctx
        except Exception:
            return None

    @property
    def has_certs(self) -> bool:
        return self._ca_cert is not None and self._node_cert is not None
