from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from spotify.auth import PROFILE_PATH


class TasteProfileStore:
    def __init__(self, path: Path = PROFILE_PATH) -> None:
        self.path = path

    def load(self) -> dict:
        if not self.path.exists():
            return {"artists": {}, "genres": {}, "playlists": []}
        return json.loads(self.path.read_text())

    def save(self, profile: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(profile, indent=2))

    def record_playlist(self, playlist_id: str, tracks: list[dict]) -> None:
        profile = self.load()
        artist_counts = Counter(profile.get("artists", {}))
        for track in tracks:
            for artist in track.get("artists", []):
                artist_counts[artist] += 1
        profile["artists"] = dict(artist_counts)
        playlists = profile.setdefault("playlists", [])
        if playlist_id not in playlists:
            playlists.append(playlist_id)
        self.save(profile)

    def preferences_summary(self) -> str:
        profile = self.load()
        artists = profile.get("artists", {})
        if not artists:
            return "None"
        top = sorted(artists.items(), key=lambda item: item[1], reverse=True)[:10]
        return ", ".join(f"{artist} ({count})" for artist, count in top)


def get_taste_store() -> TasteProfileStore:
    return TasteProfileStore()
