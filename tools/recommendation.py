from __future__ import annotations

from spotify.client import get_client


async def recommend_tracks(
    playlist_id: str,
    *,
    limit: int = 10,
    target_energy: float | None = None,
    target_valence: float | None = None,
    target_danceability: float | None = None,
) -> dict:
    client = get_client()
    tracks = await client.get_playlist_tracks(playlist_id)
    if not tracks:
        return {"playlist_id": playlist_id, "recommendations": []}

    seed_ids = [track.id for track in tracks[:5]]
    existing_uris = [track.uri for track in tracks]
    recommendations = await client.get_recommendations(
        seed_track_ids=seed_ids,
        limit=limit,
        target_energy=target_energy,
        target_valence=target_valence,
        target_danceability=target_danceability,
    )
    filtered = [
        track
        for track in recommendations
        if track.uri not in set(existing_uris)
    ]
    return {
        "playlist_id": playlist_id,
        "recommendations": [track.model_dump() for track in filtered],
    }
