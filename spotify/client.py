from __future__ import annotations

import asyncio
from typing import Any

import httpx

from spotify.auth import SpotifyAuth, SpotifyAuthError
from spotify.models import (
    AudioFeatures,
    SearchResult,
    SpotifyPlaylist,
    SpotifyTrack,
    SpotifyUser,
)

API_BASE = "https://api.spotify.com/v1"
MAX_SEARCH_LIMIT = 10
MAX_ADD_BATCH = 100


class SpotifyAPIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class SpotifyClient:
    def __init__(self, auth: SpotifyAuth | None = None) -> None:
        self.auth = auth or SpotifyAuth()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry_on_401: bool = True,
    ) -> dict[str, Any]:
        url = f"{API_BASE}{path}"
        headers = self.auth.auth_headers()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, url, headers=headers, params=params, json=json
            )

            if response.status_code == 401 and retry_on_401:
                self.auth.refresh_access_token()
                headers = self.auth.auth_headers()
                response = await client.request(
                    method, url, headers=headers, params=params, json=json
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                raise SpotifyAPIError(
                    429, f"Spotify rate limit exceeded. Retry after {retry_after}s."
                )

            if response.status_code >= 400:
                raise SpotifyAPIError(response.status_code, response.text)

            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

    @staticmethod
    def _parse_track(item: dict[str, Any]) -> SpotifyTrack | None:
        if not item or item.get("type") != "track":
            return None
        return SpotifyTrack(
            id=item["id"],
            uri=item["uri"],
            name=item["name"],
            artists=[artist["name"] for artist in item.get("artists", [])],
            album=item.get("album", {}).get("name"),
            popularity=item.get("popularity"),
        )

    async def get_current_user(self) -> SpotifyUser:
        data = await self._request("GET", "/me")
        return SpotifyUser(id=data["id"], display_name=data.get("display_name"))

    async def search_tracks(self, query: str, limit: int = 5) -> SearchResult:
        limit = min(max(limit, 1), MAX_SEARCH_LIMIT)
        data = await self._request(
            "GET",
            "/search",
            params={"q": query, "type": "track", "limit": limit},
        )
        tracks = [
            track
            for item in data.get("tracks", {}).get("items", [])
            if (track := self._parse_track(item)) is not None
        ]
        return SearchResult(query=query, tracks=tracks)

    async def create_playlist(
        self,
        name: str,
        description: str = "",
        *,
        public: bool = False,
    ) -> SpotifyPlaylist:
        payload = {"name": name, "description": description, "public": public}
        data = await self._request("POST", "/me/playlists", json=payload)
        return SpotifyPlaylist(
            id=data["id"],
            uri=data["uri"],
            name=data["name"],
            description=data.get("description"),
            url=data["external_urls"]["spotify"],
            owner_id=data.get("owner", {}).get("id"),
            track_count=data.get("tracks", {}).get("total", 0),
        )

    async def add_tracks(self, playlist_id: str, track_uris: list[str]) -> int:
        if not track_uris:
            return 0

        added = 0
        for start in range(0, len(track_uris), MAX_ADD_BATCH):
            batch = track_uris[start : start + MAX_ADD_BATCH]
            await self._request(
                "POST",
                f"/playlists/{playlist_id}/items",
                json={"uris": batch},
            )
            added += len(batch)
        return added

    async def remove_tracks(self, playlist_id: str, track_uris: list[str]) -> int:
        if not track_uris:
            return 0

        removed = 0
        for start in range(0, len(track_uris), MAX_ADD_BATCH):
            batch = track_uris[start : start + MAX_ADD_BATCH]
            await self._request(
                "DELETE",
                f"/playlists/{playlist_id}/items",
                json={"items": [{"uri": uri} for uri in batch]},
            )
            removed += len(batch)
        return removed

    async def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        data = await self._request("GET", f"/playlists/{playlist_id}")
        return SpotifyPlaylist(
            id=data["id"],
            uri=data["uri"],
            name=data["name"],
            description=data.get("description"),
            url=data["external_urls"]["spotify"],
            owner_id=data.get("owner", {}).get("id"),
            track_count=data.get("tracks", {}).get("total", 0),
        )

    async def get_playlist_tracks(self, playlist_id: str) -> list[SpotifyTrack]:
        tracks: list[SpotifyTrack] = []
        offset = 0
        limit = 100

        while True:
            data = await self._request(
                "GET",
                f"/playlists/{playlist_id}/items",
                params={"limit": limit, "offset": offset},
            )
            items = data.get("items", [])
            for item in items:
                track = self._parse_track(item.get("track"))
                if track:
                    tracks.append(track)
            if len(items) < limit:
                break
            offset += limit

        return tracks

    async def get_audio_features(self, track_ids: list[str]) -> list[AudioFeatures]:
        if not track_ids:
            return []

        features: list[AudioFeatures] = []
        for start in range(0, len(track_ids), 100):
            batch = track_ids[start : start + 100]
            data = await self._request(
                "GET",
                "/audio-features",
                params={"ids": ",".join(batch)},
            )
            for item in data.get("audio_features", []):
                if not item:
                    continue
                features.append(
                    AudioFeatures(
                        track_id=item["id"],
                        energy=item["energy"],
                        valence=item["valence"],
                        danceability=item["danceability"],
                        tempo=item["tempo"],
                        acousticness=item["acousticness"],
                        instrumentalness=item["instrumentalness"],
                    )
                )
        return features

    async def get_recommendations(
        self,
        *,
        seed_track_ids: list[str],
        limit: int = 10,
        target_energy: float | None = None,
        target_valence: float | None = None,
        target_danceability: float | None = None,
    ) -> list[SpotifyTrack]:
        if not seed_track_ids:
            return []

        params: dict[str, Any] = {
            "seed_tracks": ",".join(seed_track_ids[:5]),
            "limit": min(max(limit, 1), MAX_SEARCH_LIMIT),
        }
        if target_energy is not None:
            params["target_energy"] = target_energy
        if target_valence is not None:
            params["target_valence"] = target_valence
        if target_danceability is not None:
            params["target_danceability"] = target_danceability

        data = await self._request("GET", "/recommendations", params=params)
        return [
            track
            for item in data.get("tracks", [])
            if (track := self._parse_track(item)) is not None
        ]

    async def resolve_song(self, title: str, artist: str) -> SpotifyTrack | None:
        queries = [
            f'track:"{title}" artist:"{artist}"',
            f"{title} {artist}",
            title,
        ]
        for query in queries:
            result = await self.search_tracks(query, limit=1)
            if result.tracks:
                return result.tracks[0]
        return None

    async def resolve_songs(
        self, songs: list[tuple[str, str]]
    ) -> tuple[list[SpotifyTrack], list[tuple[str, str]]]:
        resolved: list[SpotifyTrack] = []
        unresolved: list[tuple[str, str]] = []
        seen_uris: set[str] = set()

        for title, artist in songs:
            track = await self.resolve_song(title, artist)
            if track and track.uri not in seen_uris:
                resolved.append(track)
                seen_uris.add(track.uri)
            else:
                unresolved.append((title, artist))

        return resolved, unresolved


def get_client() -> SpotifyClient:
    return SpotifyClient()


def map_spotify_error(exc: Exception) -> str:
    if isinstance(exc, SpotifyAuthError):
        return str(exc)
    if isinstance(exc, SpotifyAPIError):
        if exc.status_code == 401:
            return "Spotify authentication expired. Run `python authenticate.py`."
        if exc.status_code == 403:
            return (
                "Spotify permission denied. Ensure your account is added to the app's "
                "User Management tab in the Spotify Developer Dashboard."
            )
        if exc.status_code == 429:
            return str(exc)
        return f"Spotify API error ({exc.status_code}): {exc}"
    return str(exc)


def run_async(coro: Any) -> Any:
    return asyncio.run(coro)
