from __future__ import annotations

import base64
import hashlib
import io
import shutil
import subprocess
import zipfile
from pathlib import Path

EXPECTED_BASE64_SHA256 = "c85692cf17c8e2585f4183eae9c4c79e03c9c232428dbde4e32d67448d17da77"
EXPECTED_ARCHIVE_SHA256 = "99e08f536e2c884634c1559d7be496ef4a6c95b738986694d5c75591ee9f76fc"

# The original payload chunks were committed independently. Several files in the
# current tree were later damaged while being split, so recover the immutable
# versions directly from the commits that introduced them.
PAYLOAD_SOURCES = [
    ("1770e5909a2f4e64c9df55e75ecbf51cef310e2c", ".bootstrap/payload_00.part"),
    ("f8dc24f2530d98a36c26ad8c1f28ea6663ef0987", ".bootstrap/payload_01.part"),
    ("298f213ab2232ca7b4e2cbf07b383481fb4fe73f", ".bootstrap/payload_02.part"),
    ("c610c00aa44bc641e31a50d801f56735105f5def", ".bootstrap/payload_03.part"),
    ("a3fd64b5c72f12a7aa901be8d415c7c52372b770", ".bootstrap/payload_04.part"),
    ("df028ed44d0329f5c9902e10bfd418c254ebb7b6", ".bootstrap/payload_05.part"),
    ("1c939d3e418b9a8d89d99d92dfccc9960df9f65c", ".bootstrap/payload_06.part"),
    ("e329877c0cdde7304bb334c04334e0d71ea7d2bd", ".bootstrap/payload_07.part"),
    ("7a8775310254b7325745708ffbec49867bb61f89", ".bootstrap/payload_08.part"),
    ("f529b2d223927f774ff3ef6df699529a2a88abad", ".bootstrap/payload_09.part"),
]

root = Path(__file__).resolve().parents[1]
clean_parts: list[str] = []
for commit, path in PAYLOAD_SOURCES:
    raw = subprocess.check_output(
        ["git", "show", f"{commit}:{path}"],
        cwd=root,
        text=True,
    )
    cleaned = "".join(raw.split())
    clean_parts.append(cleaned)
    print(f"Recovered {path} from {commit[:8]} ({len(cleaned)} chars)")

encoded = "".join(clean_parts)
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
    bad_member = archive.testzip()
    if bad_member is not None:
        raise RuntimeError(f"Corrupted archive member: {bad_member}")
    for member in archive.infolist():
        destination = (root / member.filename).resolve()
        if root.resolve() not in destination.parents and destination != root.resolve():
            raise RuntimeError(f"Unsafe archive path: {member.filename}")
    archive.extractall(root)

# Remove transport-only files so the final repository contains normal source.
shutil.rmtree(root / ".bootstrap", ignore_errors=True)
for path in [
    root / ".github" / "workflows" / "bootstrap.yml",
    root / ".github" / "workflows" / "generate-migrations.yml",
    root / ".migration-trigger",
]:
    if path.exists():
        path.unlink()

print(f"Extracted {len(archive_bytes)} bytes of LoveLink source successfully")
