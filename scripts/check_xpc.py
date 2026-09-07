#!/usr/bin/env python3
"""Verify the signed application can communicate with its bundled XPC service."""
import subprocess
import sys
from pathlib import Path

app = Path(sys.argv[1]).resolve()
result = subprocess.run(
    [str(app / "Contents/MacOS/Ice"), "--xpc-smoke-test"],
    capture_output=True, text=True, timeout=45,
)
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
if result.returncode != 0 or "XPC_HANDSHAKE_OK" not in result.stdout.splitlines():
    raise SystemExit("Bundled XPC handshake failed; release blocked.")
