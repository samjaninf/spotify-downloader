import pytest
from unittest.mock import Mock

from spotdl.download.downloader import Downloader
from spotdl.types.saved import SavedError
from spotdl.types.song import Song
from spotdl.utils.search import get_search_results, get_simple_songs, parse_query

SONG = ["https://open.spotify.com/track/2Ikdgh3J5vCRmnCL3Xcrtv"]
PLAYLIST = ["https://open.spotify.com/playlist/78Lg6HmUqlTnmipvNxc536"]
ALBUM = ["https://open.spotify.com/album/4MQnUDGXmHOvnsWCpzeqWT"]
YT = [
    "https://www.youtube.com/watch?v=BZKwsPIhVO8|https://open.spotify.com/track/4B2kkxg3wKSTZw5JPaUtzQ"
]
ARTIST = ["https://open.spotify.com/artist/1FPC2zwfMHhrP3frOfaai6"]
ALBUM_SEARCH = ["album: yeezus"]

QUERY = SONG + PLAYLIST + ALBUM + YT + ARTIST

SAVED = ["saved"]


@pytest.mark.vcr()
def test_parse_song():
    songs = parse_query(SONG)

    song = songs[0]
    assert len(songs) == 1
    assert song.download_url == None


@pytest.mark.vcr()
def test_parse_album():
    songs = parse_query(ALBUM)

    assert len(songs) > 1
    assert songs[0].url == "https://open.spotify.com/track/2Ikdgh3J5vCRmnCL3Xcrtv"


@pytest.mark.vcr()
def test_parse_yt_link():
    songs = parse_query(YT)

    assert len(songs) == 1
    assert songs[0].url == "https://open.spotify.com/track/4B2kkxg3wKSTZw5JPaUtzQ"
    assert songs[0].download_url == "https://www.youtube.com/watch?v=BZKwsPIhVO8"


@pytest.mark.vcr()
def test_parse_artist():
    songs = parse_query(ARTIST)

    assert len(songs) > 1


@pytest.mark.vcr()
def test_parse_album_search():
    songs = parse_query(ALBUM_SEARCH)

    assert len(songs) > 0


@pytest.mark.vcr()
def test_parse_saved():
    with pytest.raises(SavedError):
        parse_query(SAVED)


def test_parse_query():
    songs = parse_query(QUERY)

    assert len(songs) > 1


@pytest.mark.vcr()
def test_get_search_results():
    results = get_search_results("test")
    assert len(results) > 1


def test_create_empty_song():
    song = Song.from_missing_data(name="test")
    assert song.name == "test"
    assert song.url == None
    assert song.download_url == None
    assert song.duration == None
    assert song.artists == None


@pytest.mark.vcr()
def test_get_simple_songs():
    songs = get_simple_songs(QUERY)
    assert len(songs) > 1


def test_search_all_returns_ordered_candidate_urls():
    downloader = Downloader.__new__(Downloader)
    downloader.settings = {"only_verified_results": False}

    provider_one = Mock()
    provider_one.search.return_value = "https://youtube.com/watch?v=primary"
    provider_one.get_results.return_value = [
        Mock(url="https://youtube.com/watch?v=primary", verified=True),
        Mock(url="https://youtube.com/watch?v=secondary1", verified=False),
    ]

    provider_two = Mock()
    provider_two.search.return_value = None
    provider_two.get_results.return_value = [
        Mock(url="https://youtube.com/watch?v=secondary2", verified=True),
    ]

    downloader.audio_providers = [provider_one, provider_two]

    song = Song.from_missing_data(name="Test Song", artists=["Artist"])
    results = downloader.search_all(song)

    assert results == [
        "https://youtube.com/watch?v=primary",
        "https://youtube.com/watch?v=secondary1",
        "https://youtube.com/watch?v=secondary2",
    ]


def test_search_all_respects_verified_only_for_primary_urls():
    downloader = Downloader.__new__(Downloader)
    downloader.settings = {"only_verified_results": True}

    provider = Mock()
    provider.search.return_value = None
    provider.get_results.return_value = [
        Mock(url="https://youtube.com/watch?v=verified", verified=True),
        Mock(url="https://youtube.com/watch?v=unverified", verified=False),
    ]

    downloader.audio_providers = [provider]

    song = Song.from_missing_data(name="Test Song", artists=["Artist"])
    results = downloader.search_all(song)

    provider.search.assert_called_once_with(song, True)
    assert results == ["https://youtube.com/watch?v=verified"]
