#!/usr/bin/env python3
"""Patch a user-provided Nintendo Switch YouTube v4 main NSO."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile

try:
    import lz4.block
except ImportError:
    print(
        "Missing dependency: lz4\n"
        "Install it with: python3 -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)


TITLE_ID = "01003A400C3DA000"
SUPPORTED_BUILD_ID = "825C18BBF5008500091842636FC2D8DE"
EXPECTED_INPUT_SHA256 = "33f71d01f6d581cd6148ceb97b2829e211460b69d61db03ede050c1045eda2e2"
EXPECTED_OUTPUT_SHA256 = "2f4a7aa4962bcda0131607d799b651fbff570496823de42bd48d13e4c0a640cd"

HEADER_SIZE = 0x100
TEXT_PATCH_OFFSET = 0x1E9F90
TEXT_APPEND_OFFSET = 0x190E9A0
RO_APPEND_OFFSET = 0x12EBD24
EXPECTED_TEXT_INSTRUCTION = bytes.fromhex("60621691")
PATCHED_TEXT_INSTRUCTION = bytes.fromhex("84925c94")

# Compiled AArch64 hook. Its readable source is in src/hook.S.
HOOK = bytes.fromhex(
    "ff8301d1fe2f00f960ca42f9600300b4283c80d2e80300f9"
    "683b80d2e80700f96897009008913491e80b00f9280280d2"
    "e80f00f9280180d2e81300f96897009008013c91e81700f9"
    "28008052e83300b9e83700b9e8e30091e1030091e2630091"
    "e3031faaa7e0a397e8e3403968000036e02740f9cbf7ff97"
    "60621691fe2f40f9ff830191c0035fd6"
)

# Keep this minified: the hook encodes this exact byte length.
JAVASCRIPT = (
    '(function(){var p=JSON.parse;JSON.parse=function(){var r=p.apply(this,arguments),c,s;'
    'if(r&&typeof r==="object"){delete r.adPlacements;delete r.adSlots;delete r.playerAds;'
    'c=r.contents;s=c&&c.sectionListRenderer;if(!s){c=c&&c.tvBrowseRenderer;'
    'c=c&&c.content&&c.content.tvSurfaceContentRenderer;'
    's=c&&c.content&&c.content.sectionListRenderer}'
    'if(s&&Array.isArray(s.contents))s.contents=s.contents.filter(function(x){'
    'return !x.adSlotRenderer&&!x.tvMastheadRenderer})}return r}})();'
).encode("ascii")
RO_PAYLOAD = JAVASCRIPT + b"\0[adblock]\0"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def write_u32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value)


def decode_segments(raw: bytes) -> tuple[bytearray, list[bytearray], int]:
    if raw[:4] != b"NSO0":
        raise ValueError("input is not an NSO0 file")

    flags = read_u32(raw, 0x0C)
    first_file_offset = read_u32(raw, 0x10)
    segments: list[bytearray] = []

    for index in range(3):
        descriptor = 0x10 + index * 0x10
        file_offset = read_u32(raw, descriptor)
        decompressed_size = read_u32(raw, descriptor + 8)
        compressed_size = read_u32(raw, 0x60 + index * 4)
        stored_size = compressed_size if flags & (1 << index) else decompressed_size
        stored = raw[file_offset : file_offset + stored_size]
        if len(stored) != stored_size:
            raise ValueError(f"segment {index} is truncated")

        if flags & (1 << index):
            decoded = lz4.block.decompress(stored, uncompressed_size=decompressed_size)
        else:
            decoded = stored
        segments.append(bytearray(decoded))

    return bytearray(raw[:HEADER_SIZE]), segments, first_file_offset


def apply_payload(segments: list[bytearray]) -> None:
    text, ro, _data = segments

    if len(text) != TEXT_APPEND_OFFSET or len(ro) != RO_APPEND_OFFSET:
        raise ValueError("supported hash matched, but segment layout was unexpected")
    if text[TEXT_PATCH_OFFSET : TEXT_PATCH_OFFSET + 4] != EXPECTED_TEXT_INSTRUCTION:
        raise ValueError("supported hash matched, but hook site was unexpected")
    if len(HOOK) != 136 or len(JAVASCRIPT) != 475 or len(RO_PAYLOAD) != 486:
        raise AssertionError("internal payload lengths changed")

    text[TEXT_PATCH_OFFSET : TEXT_PATCH_OFFSET + 4] = PATCHED_TEXT_INSTRUCTION
    text.extend(HOOK)
    ro.extend(RO_PAYLOAD)


def encode_nso(raw: bytes, header: bytearray, segments: list[bytearray], first_offset: int) -> bytes:
    compressed = [
        lz4.block.compress(
            bytes(segment),
            mode="high_compression",
            compression=12,
            store_size=False,
        )
        for segment in segments
    ]

    cursor = first_offset
    for index, (segment, stored) in enumerate(zip(segments, compressed)):
        descriptor = 0x10 + index * 0x10
        write_u32(header, descriptor, cursor)
        write_u32(header, descriptor + 8, len(segment))
        write_u32(header, 0x60 + index * 4, len(stored))
        header[0xA0 + index * 0x20 : 0xC0 + index * 0x20] = hashlib.sha256(segment).digest()
        cursor += len(stored)

    preserved_prefix = raw[HEADER_SIZE:first_offset]
    return bytes(header) + preserved_prefix + b"".join(compressed)


def patch(input_path: Path, output_path: Path, force: bool) -> None:
    raw = input_path.read_bytes()
    input_hash = sha256(raw)

    if input_hash == EXPECTED_OUTPUT_SHA256:
        raise ValueError("this file is already patched")
    if input_hash != EXPECTED_INPUT_SHA256:
        build_id = raw[0x40:0x50].hex().upper() if len(raw) >= 0x50 else "unknown"
        raise ValueError(
            "unsupported input; refusing to patch\n"
            f"  SHA-256: {input_hash}\n"
            f"  Build ID: {build_id}\n"
            f"Expected SHA-256: {EXPECTED_INPUT_SHA256}\n"
            f"Expected Build ID: {SUPPORTED_BUILD_ID}"
        )
    if input_path.resolve() == output_path.resolve():
        raise ValueError("input and output must be different so the original stays untouched")
    if output_path.exists() and not force:
        raise ValueError(f"output already exists: {output_path} (use --force to replace it)")

    header, segments, first_offset = decode_segments(raw)
    apply_payload(segments)
    patched = encode_nso(raw, header, segments, first_offset)
    output_hash = sha256(patched)
    if output_hash != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            "output verification failed; nothing was installed\n"
            f"Expected: {EXPECTED_OUTPUT_SHA256}\n"
            f"Actual:   {output_hash}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_mode = stat.S_IMODE(input_path.stat().st_mode)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, delete=False) as temporary:
        temporary.write(patched)
        temporary_path = Path(temporary.name)
    try:
        temporary_path.chmod(source_mode)
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    print("Patch complete and verified.")
    print(f"Output:  {output_path}")
    print(f"SHA-256: {output_hash}")
    print(f"Install as: SD:/atmosphere/contents/{TITLE_ID}/exefs/main")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch a legally obtained YouTube v4 main NSO to suppress video and TV UI ads."
    )
    parser.add_argument("input", type=Path, help="path to your untouched YouTube v4 main NSO")
    parser.add_argument("-o", "--output", type=Path, default=Path("main.adfree"))
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args()

    try:
        patch(args.input, args.output, args.force)
    except (OSError, ValueError, RuntimeError, lz4.block.LZ4BlockError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
