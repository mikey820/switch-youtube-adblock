#!/usr/bin/env python3
"""Build the directly installable Atmosphere IPS32 package."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import zipfile

from patch_youtube import (
    HOOK,
    JAVASCRIPT,
    PATCHED_TEXT_INSTRUCTION,
    RO_APPEND_OFFSET,
    RO_PAYLOAD,
    SUPPORTED_BUILD_ID,
    TEXT_APPEND_OFFSET,
    TEXT_PATCH_OFFSET,
)


NSO_HEADER_SIZE = 0x100
RO_MEMORY_OFFSET = 0x190F000
PATCH_DIRECTORY = "YouTubeAdBlock"
IPS_RELATIVE_PATH = Path(
    "atmosphere",
    "exefs_patches",
    PATCH_DIRECTORY,
    f"{SUPPORTED_BUILD_ID}.ips",
)


def make_ips32() -> bytes:
    records = (
        (TEXT_PATCH_OFFSET + NSO_HEADER_SIZE, PATCHED_TEXT_INSTRUCTION),
        (TEXT_APPEND_OFFSET + NSO_HEADER_SIZE, HOOK),
        (RO_MEMORY_OFFSET + RO_APPEND_OFFSET + NSO_HEADER_SIZE, RO_PAYLOAD),
    )

    output = bytearray(b"IPS32")
    for offset, payload in records:
        if len(payload) > 0xFFFF:
            raise ValueError("IPS32 record is too large")
        output.extend(struct.pack(">IH", offset, len(payload)))
        output.extend(payload)
    output.extend(b"EEOF")
    return bytes(output)


def deterministic_zip(path: Path, archive_name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(archive_name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.1.0")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    ips = make_ips32()
    if len(ips) != 653 or len(HOOK) != 136 or len(JAVASCRIPT) != 475:
        raise RuntimeError("unexpected payload size")

    ips_path = root / IPS_RELATIVE_PATH
    ips_path.parent.mkdir(parents=True, exist_ok=True)
    ips_path.write_bytes(ips)

    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    package = dist / f"switch-youtube-adblock-atmosphere-{args.version}.zip"
    deterministic_zip(package, IPS_RELATIVE_PATH.as_posix(), ips)

    ips_hash = hashlib.sha256(ips).hexdigest()
    package_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    checksums = dist / "SHA256SUMS.txt"
    checksums.write_text(
        f"{ips_hash}  {ips_path.name}\n"
        f"{package_hash}  {package.name}\n",
        encoding="ascii",
    )

    print(f"IPS32:  {ips_path} ({len(ips)} bytes)")
    print(f"SHA-256: {ips_hash}")
    print(f"Package: {package}")
    print(f"SHA-256: {package_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
