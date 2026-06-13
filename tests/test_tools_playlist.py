import pytest

from tools.playlist import dedupe_uris, find_repeated_artists
from spotify.models import SpotifyTrack


def test_add_tracks_dedupes_before_add():
    existing = ["spotify:track:1", "spotify:track:2"]
    incoming = ["spotify:track:2", "spotify:track:3"]
    assert dedupe_uris(existing, incoming) == ["spotify:track:3"]


def test_repeated_artists_threshold():
    tracks = [
        SpotifyTrack(id="1", uri="u1", name="A", artists=["A1"]),
        SpotifyTrack(id="2", uri="u2", name="B", artists=["A1"]),
        SpotifyTrack(id="3", uri="u3", name="C", artists=["A1"]),
    ]
    assert find_repeated_artists(tracks, threshold=2) == ["A1"]
