from __future__ import annotations

from spotify.client import SpotifyClient, get_client, map_spotify_error, run_async
from spotify.models import SearchResult


async def search_track(query: str, limit: int = 5) -> dict:
    client = get_client()
    result = await client.search_tracks(query, limit=limit)
    return result.model_dump()


async def search_tracks_batch(queries: list[str], limit: int = 3) -> list[SearchResult]:
    client = get_client()
    results: list[SearchResult] = []
    for query in queries:
        results.append(await client.search_tracks(query, limit=limit))
    return results
