import pytest

from spotdl.types.playlist import Playlist
from spotdl.types.song import Song
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
    songs = [_song(list_name="something / or other")]

    gen_m3u_files(songs, "./{list}", "", "mp3")

    assert tmpdir.join("something or other.m3u8").isfile()


def _song(list_name):
    return Song(
        name="test",
        artists=["test"],
        artist="test",
        genres=[],
        disc_number=1,
        disc_count=1,
        album_name="test",
        album_artist="test",
        duration=1,
        year=2024,
        date="2024-01-01",
        track_number=1,
        tracks_count=1,
        song_id="test",
        explicit=False,
        publisher="test",
        url="https://example.com/test",
        isrc=None,
        cover_url=None,
        copyright_text=None,
        list_name=list_name,
    )
