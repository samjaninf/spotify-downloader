"""
Module for checking for a Deno binary, finding a local one, and downloading it.
"""

import os
import platform
import shutil
import stat
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import requests

from spotdl.utils.config import get_spotdl_path

__all__ = [
    "DENO_RELEASE_LATEST_URL",
    "DENO_RELEASE_URL",
    "DENO_TARGETS",
    "DenoError",
    "is_deno_installed",
    "get_deno_path",
    "get_local_deno",
    "ensure_local_deno_on_path",
    "download_deno",
]

DENO_RELEASE_LATEST_URL = "https://dl.deno.land/release-latest.txt"
DENO_RELEASE_URL = "https://dl.deno.land/release/{version}/deno-{target}.zip"

DENO_TARGETS: Dict[str, Dict[str, str]] = {
    "windows": {
        "amd64": "x86_64-pc-windows-msvc",
        "x86_64": "x86_64-pc-windows-msvc",
        "arm64": "aarch64-pc-windows-msvc",
        "aarch64": "aarch64-pc-windows-msvc",
    },
    "linux": {
        "amd64": "x86_64-unknown-linux-gnu",
        "x86_64": "x86_64-unknown-linux-gnu",
        "arm64": "aarch64-unknown-linux-gnu",
        "aarch64": "aarch64-unknown-linux-gnu",
    },
    "darwin": {
        "amd64": "x86_64-apple-darwin",
        "x86_64": "x86_64-apple-darwin",
        "arm64": "aarch64-apple-darwin",
        "aarch64": "aarch64-apple-darwin",
    },
}


class DenoError(Exception):
    """
    Base class for all exceptions related to Deno.
    """


def is_deno_installed(deno: str = "deno") -> bool:
    """
    Check if Deno is installed.

    ### Arguments
    - deno: Deno executable to check.

    ### Returns
    - True if Deno is installed, False otherwise.
    """

    if deno == "deno":
        deno_path = get_deno_path()
    else:
        deno_path = Path(deno)

    if deno_path is None:
        return False

    return deno_path.exists() and os.access(deno_path, os.X_OK)


def get_deno_path() -> Optional[Path]:
    """
    Get path to global Deno binary or a local Deno binary.

    ### Returns
    - Path to Deno binary or None if not found.
    """

    global_deno = shutil.which("deno")
    if global_deno:
        return Path(global_deno)

    return get_local_deno()


def get_local_deno() -> Optional[Path]:
    """
    Get local Deno binary path.

    ### Returns
    - Path to Deno binary or None if not found.
    """

    deno_path = Path(get_spotdl_path()) / (
        "deno" + (".exe" if platform.system() == "Windows" else "")
    )

    if deno_path.is_file():
        return deno_path

    return None


def ensure_local_deno_on_path() -> Optional[Path]:
    """
    Add spotDL's local Deno directory to PATH when no global Deno is installed.

    ### Returns
    - Path to local Deno binary or None if no PATH update was needed.
    """

    if shutil.which("deno") is not None:
        return None

    local_deno = get_local_deno()
    if local_deno is None or not os.access(local_deno, os.X_OK):
        return None

    os.environ["PATH"] = (
        str(local_deno.parent) + os.pathsep + os.environ.get("PATH", "")
    )

    return local_deno


def download_deno() -> Path:
    """
    Download Deno binary to spotdl directory.

    ### Returns
    - Path to Deno binary.

    ### Notes
    - Deno is downloaded from dl.deno.land for the current platform and architecture.
    - executable permission is set for Deno binary on linux and mac.
    """

    os_name = platform.system().lower()
    os_arch = platform.machine().lower()
    deno_target = DENO_TARGETS.get(os_name, {}).get(os_arch)

    if deno_target is None:
        raise DenoError("Deno binary is not available for your system.")

    latest_version = (
        requests.get(DENO_RELEASE_LATEST_URL, allow_redirects=True, timeout=10)
        .content.decode("utf-8")
        .strip()
    )
    deno_url = DENO_RELEASE_URL.format(version=latest_version, target=deno_target)

    deno_archive = requests.get(deno_url, allow_redirects=True, timeout=10).content
    deno_filename = "deno" + (".exe" if os_name == "windows" else "")
    deno_path = Path(get_spotdl_path()) / deno_filename

    try:
        archive = zipfile.ZipFile(BytesIO(deno_archive))
    except zipfile.BadZipFile as error:
        raise DenoError("Downloaded Deno archive is not a valid zip file.") from error

    with archive:
        binary_name = next(
            (name for name in archive.namelist() if Path(name).name == deno_filename),
            None,
        )

        if binary_name is None:
            raise DenoError("Deno binary was not found in the downloaded archive.")

        with archive.open(binary_name) as deno_binary:
            deno_path.write_bytes(deno_binary.read())

    if os_name in ["linux", "darwin"]:
        deno_path.chmod(deno_path.stat().st_mode | stat.S_IEXEC)

    return deno_path
