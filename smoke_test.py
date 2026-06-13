#!/usr/bin/env python3
from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from spotify.auth import SpotifyAuth
from spotify.client import SpotifyClient, map_spotify_error

load_dotenv()


async def main() -> None:
    auth = SpotifyAuth()
    if not auth.is_authenticated:
        print("Not authenticated. Run `python authenticate.py` first.")
        raise SystemExit(1)

    client = SpotifyClient(auth)
    queries = ["Lose Yourself Eminem", "Stronger Kanye West", "Eye of the Tiger Survivor"]

    print("Searching tracks...")
    uris: list[str] = []
    for query in queries:
        result = await client.search_tracks(query, limit=1)
        if result.tracks:
            track = result.tracks[0]
            uris.append(track.uri)
            print(f"  Found: {track.name} by {', '.join(track.artists)}")
        else:
            print(f"  Not found: {query}")

    if not uris:
        print("No tracks found. Check Spotify credentials and User Management setup.")
        raise SystemExit(1)

    print("Creating playlist...")
    playlist = await client.create_playlist(
        "Playlist Agent Smoke Test",
        "Created by smoke_test.py",
        public=False,
    )
    added = await client.add_tracks(playlist.id, uris)
    print(f"Added {added} tracks.")
    print(f"Playlist URL: {playlist.url}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Smoke test failed: {map_spotify_error(exc)}")
        raise SystemExit(1) from exc
