from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from pathlib import Path

EXPECTED_BASE64_SHA256 = "c85692cf17c8e2585f4183eae9c4c79e03c9c232428dbde4e32d67448d17da77"
EXPECTED_ARCHIVE_SHA256 = "99e08f536e2c884634c1559d7be496ef4a6c95b738986694d5c75591ee9f76fc"

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
out = Path("/tmp/lovelink-recovery")
out.mkdir(parents=True, exist_ok=True)
parts: list[str] = []
summary: dict[str, object] = {
    "expected_base64_sha256": EXPECTED_BASE64_SHA256,
    "expected_archive_sha256": EXPECTED_ARCHIVE_SHA256,
    "parts": [],
}

for index, (commit, path) in enumerate(PAYLOAD_SOURCES):
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root, text=True)
    cleaned = "".join(raw.split())
    parts.append(cleaned)
    (out / f"part_{index:02d}.txt").write_text(cleaned, encoding="ascii")
    summary["parts"].append(
        {
            "index": index,
            "commit": commit,
            "path": path,
            "length": len(cleaned),
            "sha256": hashlib.sha256(cleaned.encode("ascii")).hexdigest(),
            "equals_count": cleaned.count("="),
            "starts_with": cleaned[:32],
            "ends_with": cleaned[-32:],
        }
    )

encoded = "".join(parts)
(out / "encoded.txt").write_text(encoded, encoding="ascii")
summary["encoded_length"] = len(encoded)
summary["encoded_sha256"] = hashlib.sha256(encoded.encode("ascii")).hexdigest()
summary["encoded_mod_4"] = len(encoded) % 4
summary["equals_positions"] = [i for i, char in enumerate(encoded) if char == "="]

# Produce a best-effort binary for local forensic analysis. This is diagnostic;
# the final recovery still requires the exact verified archive.
without_padding = encoded.replace("=", "")
without_padding += "=" * ((-len(without_padding)) % 4)
try:
    decoded = base64.b64decode(without_padding, validate=False)
    (out / "best_effort.bin").write_bytes(decoded)
    summary["best_effort_length"] = len(decoded)
    summary["best_effort_sha256"] = hashlib.sha256(decoded).hexdigest()
    summary["zip_local_headers"] = [i for i in range(len(decoded)) if decoded.startswith(b"PK\x03\x04", i)]
    summary["zip_central_headers"] = [i for i in range(len(decoded)) if decoded.startswith(b"PK\x01\x02", i)]
    summary["zip_end_headers"] = [i for i in range(len(decoded)) if decoded.startswith(b"PK\x05\x06", i)]
except Exception as exc:  # pragma: no cover - diagnostic output
    summary["decode_error"] = repr(exc)

# Boundary overlap diagnostics.
overlaps = []
for index in range(len(parts) - 1):
    left, right = parts[index], parts[index + 1]
    overlap = 0
    for size in range(1, min(512, len(left), len(right)) + 1):
        if left[-size:] == right[:size]:
            overlap = size
    overlaps.append({"left": index, "right": index + 1, "max_overlap": overlap})
summary["boundary_overlaps"] = overlaps

(out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print(f"Diagnostic files written to {out}")
