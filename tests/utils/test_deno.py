import os
import pathlib
import platform
import shutil
import zipfile
from io import BytesIO

import pytest

import spotdl.utils.deno
from spotdl.utils.deno import *


class MockResponse:
    def __init__(self, content):
        self.content = content


def make_deno_archive(filename="deno"):
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as deno_archive:
        deno_archive.writestr(filename, b"deno")

    return archive.getvalue()


def test_is_not_deno_installed(monkeypatch):
    """
    Test is_deno_installed function.
    """

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    monkeypatch.setattr(pathlib.Path, "is_file", lambda *_: False)

    assert is_deno_installed() is False


def test_get_none_deno_path(monkeypatch):
    """
    Test get_deno_path function.
    """

    monkeypatch.setattr(shutil, "which", lambda *_: None)
    monkeypatch.setattr(pathlib.Path, "is_file", lambda *_: False)

    assert get_deno_path() is None


def test_get_none_local_deno(monkeypatch):
    """
    Test get_local_deno function.
    """

    monkeypatch.setattr(pathlib.Path, "is_file", lambda *_: False)

    assert get_local_deno() is None


def test_get_local_deno(monkeypatch):
    """
    Test get_local_deno function.
    """

    monkeypatch.setattr(pathlib.Path, "is_file", lambda *_: True)

    local_deno = get_local_deno()

    assert local_deno is not None

    if platform.system() == "Windows":
        assert str(local_deno).endswith("deno.exe")
    else:
        assert str(local_deno).endswith("deno")


def test_ensure_local_deno_on_path(monkeypatch, tmp_path):
    """
    Test ensure_local_deno_on_path function.
    """

    local_deno = tmp_path / "deno"
    local_deno.write_bytes(b"deno")
    local_deno.chmod(0o755)
    monkeypatch.setattr(shutil, "which", lambda *_: None)
    monkeypatch.setattr(spotdl.utils.deno, "get_local_deno", lambda *_: local_deno)
    monkeypatch.setenv("PATH", "old-path")

    assert ensure_local_deno_on_path() == local_deno
    assert os.environ["PATH"] == f"{tmp_path}{os.pathsep}old-path"


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Windows does not use POSIX executable bits.",
)
def test_ensure_local_deno_on_path_ignores_non_executable(monkeypatch, tmp_path):
    """
    Test ensure_local_deno_on_path does not add non-executable files to PATH.
    """

    local_deno = tmp_path / "deno"
    local_deno.write_bytes(b"deno")
    local_deno.chmod(0o644)
    monkeypatch.setattr(shutil, "which", lambda *_: None)
    monkeypatch.setattr(spotdl.utils.deno, "get_local_deno", lambda *_: local_deno)
    monkeypatch.setenv("PATH", "old-path")

    assert ensure_local_deno_on_path() is None
    assert os.environ["PATH"] == "old-path"


def test_ensure_local_deno_on_path_prefers_global(monkeypatch, tmp_path):
    """
    Test ensure_local_deno_on_path does not change PATH when Deno is globally installed.
    """

    monkeypatch.setattr(shutil, "which", lambda *_: str(tmp_path / "deno"))
    monkeypatch.setenv("PATH", "old-path")

    assert ensure_local_deno_on_path() is None
    assert os.environ["PATH"] == "old-path"


@pytest.mark.parametrize(
    ("system", "machine", "filename", "target"),
    [
        ("Windows", "AMD64", "deno.exe", "x86_64-pc-windows-msvc"),
        ("Windows", "ARM64", "deno.exe", "aarch64-pc-windows-msvc"),
        ("Linux", "x86_64", "deno", "x86_64-unknown-linux-gnu"),
        ("Linux", "aarch64", "deno", "aarch64-unknown-linux-gnu"),
        ("Darwin", "x86_64", "deno", "x86_64-apple-darwin"),
        ("Darwin", "arm64", "deno", "aarch64-apple-darwin"),
    ],
)
def test_download_deno(monkeypatch, tmp_path, system, machine, filename, target):
    """
    Test download_deno function.
    """

    urls = []

    def mock_get(url, *_args, **_kwargs):
        urls.append(url)
        if url == DENO_RELEASE_LATEST_URL:
            return MockResponse(b"v1.0.0\n")

        return MockResponse(make_deno_archive(filename))

    monkeypatch.setattr(spotdl.utils.deno, "get_spotdl_path", lambda *_: tmp_path)
    monkeypatch.setattr(spotdl.utils.deno.platform, "system", lambda: system)
    monkeypatch.setattr(spotdl.utils.deno.platform, "machine", lambda: machine)
    monkeypatch.setattr(spotdl.utils.deno.requests, "get", mock_get)

    deno_path = download_deno()

    assert urls == [
        DENO_RELEASE_LATEST_URL,
        f"https://dl.deno.land/release/v1.0.0/deno-{target}.zip",
    ]
    assert deno_path == tmp_path / filename
    assert deno_path.read_bytes() == b"deno"


def test_download_deno_unsupported_platform(monkeypatch):
    """
    Test download_deno raises when Deno does not publish a matching binary.
    """

    monkeypatch.setattr(spotdl.utils.deno.platform, "system", lambda: "FreeBSD")
    monkeypatch.setattr(spotdl.utils.deno.platform, "machine", lambda: "x86_64")

    with pytest.raises(DenoError):
        download_deno()


def test_download_deno_invalid_archive(monkeypatch, tmp_path):
    """
    Test download_deno raises when the downloaded archive is invalid.
    """

    def mock_get(url, *_args, **_kwargs):
        if url == DENO_RELEASE_LATEST_URL:
            return MockResponse(b"v1.0.0\n")

        return MockResponse(b"not a zip")

    monkeypatch.setattr(spotdl.utils.deno, "get_spotdl_path", lambda *_: tmp_path)
    monkeypatch.setattr(spotdl.utils.deno.platform, "system", lambda: "Linux")
    monkeypatch.setattr(spotdl.utils.deno.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(spotdl.utils.deno.requests, "get", mock_get)

    with pytest.raises(DenoError):
        download_deno()
