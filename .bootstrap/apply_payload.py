from __future__ import annotations

import base64
import hashlib
import io
import shutil
import zipfile
from pathlib import Path

EXPECTED_BASE64_SHA256 = "c85692cf17c8e2585f4183eae9c4c79e03c9c232428dbde4e32d67448d17da77"
EXPECTED_ARCHIVE_SHA256 = "99e08f536e2c884634c1559d7be496ef4a6c95b738986694d5c75591ee9f76fc"

root = Path(__file__).resolve().parents[1]
parts = sorted((root / ".bootstrap").glob("payload_*.part"))
if not parts:
    raise RuntimeError("No payload parts were found")

# Whitespace is ignored intentionally so the payload remains robust when moved
# through text-based repository APIs.
encoded = "".join("".join(part.read_text(encoding="utf-8").split()) for part in parts)
encoded_digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()
if encoded_digest != EXPECTED_BASE64_SHA256:
    raise RuntimeError(
        f"Payload checksum mismatch: expected {EXPECTED_BASE64_SHA256}, got {encoded_digest}"
    )

archive_bytes = base64.b64decode(encoded, validate=True)
archive_digest = hashlib.sha256(archive_bytes).hexdigest()
if archive_digest != EXPECTED_ARCHIVE_SHA256:
    raise RuntimeError(
        f"Archive checksum mismatch: expected {EXPECTED_ARCHIVE_SHA256}, got {archive_digest}"
    )

with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    for member in archive.infolist():
        destination = (root / member.filename).resolve()
        if root.resolve() not in destination.parents and destination != root.resolve():
            raise RuntimeError(f"Unsafe archive path: {member.filename}")
    archive.extractall(root)

shutil.rmtree(root / ".bootstrap")
bootstrap_workflow = root / ".github" / "workflows" / "bootstrap.yml"
if bootstrap_workflow.exists():
    bootstrap_workflow.unlink()
