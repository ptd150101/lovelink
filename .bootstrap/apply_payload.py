from __future__ import annotations

import base64
import binascii
import shutil
import struct
import subprocess
import zlib
from pathlib import Path, PurePosixPath

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
parts: list[str] = []
for commit, path in PAYLOAD_SOURCES:
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root, text=True)
    parts.append("".join(raw.split()))
encoded = "".join(parts)

# Repair the three known text-transport defects in the historical payload.
encoded = encoded[:4735] + "z" + encoded[4735:32443] + encoded[32444:]
encoded = encoded[:140072] + "B" + encoded[140072:]
encoded = encoded[:141864] + "B" + encoded[141864:]
encoded = encoded.replace("=", "")
encoded += "=" * ((-len(encoded)) % 4)
archive = base64.b64decode(encoded, validate=False)

LOCAL = b"PK\x03\x04"
HEADER = struct.Struct("<IHHHHHIIIHH")
recovered: dict[str, bytes] = {}
valid_records = 0
position = 0
while True:
    offset = archive.find(LOCAL, position)
    if offset < 0:
        break
    position = offset + 1
    if offset + HEADER.size > len(archive):
        continue
    try:
        sig, version, flags, method, mtime, mdate, crc, csize, usize, name_len, extra_len = HEADER.unpack_from(archive, offset)
    except struct.error:
        continue
    if sig != 0x04034B50 or flags & 0x08 or method not in {0, 8}:
        continue
    name_start = offset + HEADER.size
    data_start = name_start + name_len + extra_len
    data_end = data_start + csize
    if name_len == 0 or data_end > len(archive):
        continue
    name_bytes = archive[name_start:name_start + name_len]
    try:
        name = name_bytes.decode("utf-8")
    except UnicodeDecodeError:
        continue
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or name.endswith("/"):
        continue
    compressed = archive[data_start:data_end]
    try:
        payload = compressed if method == 0 else zlib.decompress(compressed, -15)
    except zlib.error:
        continue
    if len(payload) != usize or (binascii.crc32(payload) & 0xFFFFFFFF) != crc:
        continue
    recovered[name] = payload
    valid_records += 1

critical = {"backend/manage.py", "backend/config/settings.py", "frontend/package.json", "docker-compose.yml", "README.md"}
missing = critical.difference(recovered)
if missing or len(recovered) < 150:
    raise RuntimeError(f"Recovery incomplete: {len(recovered)} files; missing={sorted(missing)}")

for name, payload in recovered.items():
    destination = root / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)

shutil.rmtree(root / ".bootstrap", ignore_errors=True)
for temporary in [
    root / ".github" / "workflows" / "bootstrap.yml",
    root / ".github" / "workflows" / "generate-migrations.yml",
    root / ".migration-trigger",
]:
    temporary.unlink(missing_ok=True)
print(f"Recovered {len(recovered)} unique files from {valid_records} valid ZIP records")
