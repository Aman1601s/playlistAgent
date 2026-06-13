import json
import time

import httpx
import pytest
import respx

from spotify.auth import SpotifyAuth, SpotifySettings
from spotify.client import SpotifyClient, map_spotify_error
from spotify.models import GeneratedSong, SpotifyTrack
from tools.playlist import dedupe_uris, find_repeated_artists, resolve_generated_songs


@pytest.fixture
def auth_settings(tmp_path, monkeypatch):
    token_path = tmp_path / "tokens.json"
    monkeypatch.setattr("spotify.auth.TOKEN_PATH", token_path)
    token_path.write_text(json.dumps({"refresh_token": "refresh", "access_token": "access"}))
    settings = SpotifySettings(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://127.0.0.1:8888/callback",
        scopes=["playlist-modify-public"],
    )
    auth = SpotifyAuth(settings)
    auth._access_token = "access"
    auth._expires_at = time.time() + 3600
    return auth


@pytest.fixture
def spotify_client(auth_settings):
    return SpotifyClient(auth_settings)


@respx.mock
@pytest.mark.asyncio
async def test_search_tracks(spotify_client):
    respx.get("https://api.spotify.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [
                        {
                            "id": "track1",
                            "uri": "spotify:track:track1",
                            "name": "Test Song",
                            "artists": [{"name": "Test Artist"}],
                            "album": {"name": "Test Album"},
                            "popularity": 80,
                            "type": "track",
                        }
                    ]
                }
            },
        )
    )

    result = await spotify_client.search_tracks("test", limit=1)
    assert len(result.tracks) == 1
    assert result.tracks[0].name == "Test Song"


@respx.mock
@pytest.mark.asyncio
async def test_create_playlist_and_add_tracks(spotify_client):
    respx.post("https://api.spotify.com/v1/me/playlists").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "playlist1",
                "uri": "spotify:playlist:playlist1",
                "name": "My Playlist",
                "description": "desc",
                "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist1"},
                "owner": {"id": "user1"},
                "tracks": {"total": 0},
            },
        )
    )
    respx.post("https://api.spotify.com/v1/playlists/playlist1/items").mock(
        return_value=httpx.Response(201, json={"snapshot_id": "snap"})
    )

    playlist = await spotify_client.create_playlist("My Playlist", "desc")
    added = await spotify_client.add_tracks(
        playlist.id,
        ["spotify:track:1", "spotify:track:2"],
    )

    assert playlist.url.endswith("playlist1")
    assert added == 2


@respx.mock
@pytest.mark.asyncio
async def test_remove_tracks(spotify_client):
    route = respx.delete("https://api.spotify.com/v1/playlists/playlist1/items").mock(
        return_value=httpx.Response(200, json={"snapshot_id": "snap"})
    )

    removed = await spotify_client.remove_tracks(
        "playlist1",
        ["spotify:track:1"],
    )
    assert removed == 1
    assert route.called


def test_dedupe_uris():
    assert dedupe_uris(["a", "b"], ["b", "c"]) == ["c"]


def test_find_repeated_artists():
    tracks = [
        SpotifyTrack(id="1", uri="u1", name="A", artists=["Drake"]),
        SpotifyTrack(id="2", uri="u2", name="B", artists=["Drake"]),
        SpotifyTrack(id="3", uri="u3", name="C", artists=["Drake"]),
        SpotifyTrack(id="4", uri="u4", name="D", artists=["Other"]),
    ]
    assert find_repeated_artists(tracks) == ["Drake"]


def test_map_spotify_error_auth():
    from spotify.auth import SpotifyAuthError

    message = map_spotify_error(SpotifyAuthError("missing token"))
    assert "missing token" in message


@respx.mock
@pytest.mark.asyncio
async def test_resolve_generated_songs(spotify_client):
    respx.get("https://api.spotify.com/v1/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "tracks": {
                    "items": [
                        {
                            "id": "track1",
                            "uri": "spotify:track:track1",
                            "name": "Song",
                            "artists": [{"name": "Artist"}],
                            "album": {"name": "Album"},
                            "type": "track",
                        }
                    ]
                }
            },
        )
    )

    uris, unresolved = await resolve_generated_songs(
        spotify_client,
        [GeneratedSong(title="Song", artist="Artist")],
    )
    assert uris == ["spotify:track:track1"]
    assert unresolved == []
