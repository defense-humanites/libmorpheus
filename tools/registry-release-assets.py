# SPDX-License-Identifier: AGPL-3.0-or-later
"""Download a published binding version from its registry, verify it, and
stage it as GitHub release assets with a SHA256SUMS file.

    python3 tools/registry-release-assets.py npm 0.1.3 OUTPUT
    python3 tools/registry-release-assets.py pypi 0.2.0 OUTPUT

npm: the four packages of the Node.js binding (`@libmorpheus/node` and its
three platform addon packages), each tarball checked against the registry's
SHA-512 integrity. PyPI: every file of the `libmorpheus` release (wheel and
source distribution), each checked against the registry's SHA-256 digest.
The staged files are therefore the bytes users install. Standard library
only; a version not yet visible is retried for up to five minutes, since a
registry can lag a fresh publication.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

NPM_PACKAGES = (
    "@libmorpheus/node",
    "@libmorpheus/node-darwin-arm64",
    "@libmorpheus/node-linux-arm64-gnu",
    "@libmorpheus/node-linux-x64-gnu",
)
PYPI_PROJECT = "libmorpheus"
ATTEMPTS = 20
DELAY_SECONDS = 15


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "libmorpheus-release-assets"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def fetch_json_when_visible(url: str) -> dict:
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return json.loads(fetch(url))
        except urllib.error.HTTPError as error:
            if error.code != 404 or attempt == ATTEMPTS:
                raise
        print(f"not yet visible, retrying: {url}", file=sys.stderr)
        time.sleep(DELAY_SECONDS)
    raise AssertionError("unreachable")


def stage_npm(version: str, output: Path) -> list[Path]:
    staged = []
    for package in NPM_PACKAGES:
        metadata = fetch_json_when_visible(
            f"https://registry.npmjs.org/{urllib.parse.quote(package, safe='@')}/{version}"
        )
        if metadata.get("version") != version:
            raise SystemExit(f"{package}: registry returned version {metadata.get('version')}")
        integrity = metadata["dist"]["integrity"]
        algorithm, _, expected = integrity.partition("-")
        if algorithm != "sha512":
            raise SystemExit(f"{package}: unsupported integrity {integrity}")
        tarball = fetch(metadata["dist"]["tarball"])
        if base64.b64encode(hashlib.sha512(tarball).digest()).decode() != expected:
            raise SystemExit(f"{package}: tarball does not match the registry integrity")
        name = package.removeprefix("@").replace("/", "-") + f"-{version}.tgz"
        path = output / name
        path.write_bytes(tarball)
        staged.append(path)
    return staged


def stage_pypi(version: str, output: Path) -> list[Path]:
    metadata = fetch_json_when_visible(f"https://pypi.org/pypi/{PYPI_PROJECT}/{version}/json")
    files = metadata.get("urls") or []
    if not any(entry["packagetype"] == "bdist_wheel" for entry in files) or not any(
        entry["packagetype"] == "sdist" for entry in files
    ):
        raise SystemExit(f"{PYPI_PROJECT} {version}: wheel or source distribution missing on PyPI")
    staged = []
    for entry in files:
        content = fetch(entry["url"])
        if hashlib.sha256(content).hexdigest() != entry["digests"]["sha256"]:
            raise SystemExit(f"{entry['filename']}: does not match the PyPI digest")
        path = output / entry["filename"]
        path.write_bytes(content)
        staged.append(path)
    return staged


def main(arguments: list[str]) -> int:
    if len(arguments) != 3 or arguments[0] not in ("npm", "pypi"):
        print(__doc__, file=sys.stderr)
        return 2
    registry, version, output_argument = arguments
    output = Path(output_argument)
    output.mkdir(parents=True, exist_ok=False)
    staged = stage_npm(version, output) if registry == "npm" else stage_pypi(version, output)
    sums = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in sorted(staged, key=lambda path: path.name)
    )
    (output / "SHA256SUMS").write_text(sums, encoding="utf-8")
    print(sums, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
