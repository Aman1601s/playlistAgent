from __future__ import annotations

from collections import Counter

from spotify.client import SpotifyClient, get_client
from spotify.models import GeneratedSong, SpotifyTrack


def dedupe_uris(existing: list[str], incoming: list[str]) -> list[str]:
    existing_set = set(existing)
    return [uri for uri in incoming if uri not in existing_set]


def find_repeated_artists(tracks: list[SpotifyTrack], threshold: int = 2) -> list[str]:
    counts = Counter(
        artist for track in tracks for artist in track.artists if artist
    )
    return [artist for artist, count in counts.items() if count > threshold]


async def create_playlist(
    name: str,
    description: str = "",
    track_uris: list[str] | None = None,
    *,
    public: bool = False,
) -> dict:
    client = get_client()
    playlist = await client.create_playlist(name, description, public=public)
    added = 0
    if track_uris:
        unique_uris = list(dict.fromkeys(track_uris))
        added = await client.add_tracks(playlist.id, unique_uris)
    return {
        "playlist_id": playlist.id,
        "url": playlist.url,
        "name": playlist.name,
        "tracks_added": added,
    }


async def add_tracks(playlist_id: str, track_uris: list[str]) -> dict:
    client = get_client()
    existing = await client.get_playlist_tracks(playlist_id)
    existing_uris = [track.uri for track in existing]
    new_uris = dedupe_uris(existing_uris, list(dict.fromkeys(track_uris)))
    added = await client.add_tracks(playlist_id, new_uris)
    return {
        "playlist_id": playlist_id,
        "tracks_added": added,
        "skipped_duplicates": len(track_uris) - added,
    }


async def remove_tracks(playlist_id: str, track_uris: list[str]) -> dict:
    client = get_client()
    removed = await client.remove_tracks(playlist_id, track_uris)
    return {"playlist_id": playlist_id, "tracks_removed": removed}


async def get_playlist(playlist_id: str, *, include_tracks: bool = True) -> dict:
    client = get_client()
    playlist = await client.get_playlist(playlist_id)
    payload = playlist.model_dump()
    if include_tracks:
        tracks = await client.get_playlist_tracks(playlist_id)
        payload["tracks"] = [track.model_dump() for track in tracks]
        payload["repeated_artists"] = find_repeated_artists(tracks)
    return payload


async def resolve_generated_songs(
    client: SpotifyClient, songs: list[GeneratedSong]
) -> tuple[list[str], list[dict]]:
    resolved, unresolved = await client.resolve_songs(
        [(song.title, song.artist) for song in songs]
    )
    return [track.uri for track in resolved], [
        {"title": title, "artist": artist} for title, artist in unresolved
    ]
