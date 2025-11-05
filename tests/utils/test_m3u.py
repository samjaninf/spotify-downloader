import pytest

from spotdl.types.playlist import Playlist
from spotdl.utils.m3u import create_m3u_content, create_m3u_file, gen_m3u_files

PLAYLIST = "https://open.spotify.com/playlist/5LkNhFidYyyjRWwnkcMbQs"


def test_create_m3u_content():
    playlist = Playlist.from_url(PLAYLIST)
    content = create_m3u_content(
        playlist.songs, "{title} - {output-ext}.{output-ext}", "mp3"
    )

    assert content != ""
    assert len(content.split("\n")) > 5
    assert content.split("\n")[0] == "#EXTM3U"
    assert content.split("\n")[1].startswith("#EXTINF:")
    assert content.split("\n")[2].endswith(".mp3")

def test_create_m3u_file(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    playlist = Playlist.from_url(PLAYLIST)
    create_m3u_file("test.m3u", playlist.songs, "", "mp3")
    assert tmpdir.join("test.m3u").isfile() is True

def test_gen_m3u_files(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    playlist = Playlist.from_url(PLAYLIST)
    for song in playlist.songs:
        song.list_name = "something / or other"
    gen_m3u_files(playlist.songs, "./{list}", "", "mp3")
    assert tmpdir.join("something or other.m3u8").isfile()
    