from __future__ import annotations

from collections import Counter

from spotify.client import get_client
from spotify.models import PlaylistAnalysis


def _mood_label(energy: float, valence: float) -> str:
    if energy >= 0.7 and valence >= 0.5:
        return "high-energy upbeat"
    if energy >= 0.7:
        return "intense and aggressive"
    if energy <= 0.4 and valence <= 0.4:
        return "calm and melancholic"
    if energy <= 0.4:
        return "relaxed and mellow"
    if valence >= 0.6:
        return "feel-good and positive"
    return "balanced and varied"


async def analyze_playlist(playlist_id: str) -> dict:
    client = get_client()
    playlist = await client.get_playlist(playlist_id)
    tracks = await client.get_playlist_tracks(playlist_id)
    if not tracks:
        analysis = PlaylistAnalysis(
            playlist_id=playlist_id,
            track_count=0,
            avg_energy=0.0,
            avg_valence=0.0,
            avg_danceability=0.0,
            avg_tempo=0.0,
            mood="empty",
            summary="Playlist has no tracks to analyze.",
        )
        return analysis.model_dump()

    features = await client.get_audio_features([track.id for track in tracks])
    artist_counts = Counter(
        artist for track in tracks for artist in track.artists if artist
    )
    repeated = [artist for artist, count in artist_counts.items() if count > 2]
    top_artists = [artist for artist, _ in artist_counts.most_common(5)]

    avg_energy = sum(item.energy for item in features) / len(features)
    avg_valence = sum(item.valence for item in features) / len(features)
    avg_danceability = sum(item.danceability for item in features) / len(features)
    avg_tempo = sum(item.tempo for item in features) / len(features)
    mood = _mood_label(avg_energy, avg_valence)

    summary_parts = [
        f"'{playlist.name}' has {len(tracks)} tracks.",
        f"Mood: {mood}.",
        f"Average energy {avg_energy:.2f}, valence {avg_valence:.2f}.",
    ]
    if repeated:
        summary_parts.append(
            f"Repeated artists (>2 tracks): {', '.join(repeated)}."
        )

    analysis = PlaylistAnalysis(
        playlist_id=playlist_id,
        track_count=len(tracks),
        avg_energy=round(avg_energy, 3),
        avg_valence=round(avg_valence, 3),
        avg_danceability=round(avg_danceability, 3),
        avg_tempo=round(avg_tempo, 1),
        top_artists=top_artists,
        repeated_artists=repeated,
        mood=mood,
        summary=" ".join(summary_parts),
    )
    return analysis.model_dump()
