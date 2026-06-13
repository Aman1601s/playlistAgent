#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from llm.song_generator import generate_songs
from llm.playlist_editor import plan_playlist_edit
from llm.taste_profile import get_taste_store
from spotify.auth import SpotifyAuth
from spotify.client import map_spotify_error, run_async
from tools.analysis import analyze_playlist as analyze_playlist_impl
from tools.playlist import (
    add_tracks as add_tracks_impl,
    create_playlist as create_playlist_impl,
    get_playlist as get_playlist_impl,
    remove_tracks as remove_tracks_impl,
    resolve_generated_songs,
)
from tools.recommendation import recommend_tracks as recommend_tracks_impl
from tools.search import search_track as search_track_impl

load_dotenv()

mcp = FastMCP("Playlist Agent")


def _handle_tool(coro):
    try:
        return run_async(coro)
    except Exception as exc:
        return {"error": map_spotify_error(exc)}


@mcp.tool
def spotify_login() -> dict:
    """Check Spotify authentication status and token location."""
    auth = SpotifyAuth()
    return auth.login_status()


@mcp.tool
def search_track(query: str, limit: int = 5) -> dict:
    """Search Spotify for tracks matching a query."""
    return _handle_tool(search_track_impl(query, limit=limit))


@mcp.tool
def create_playlist(
    name: str,
    description: str = "",
    track_uris: list[str] | None = None,
    public: bool = False,
) -> dict:
    """Create a Spotify playlist and optionally add track URIs."""
    return _handle_tool(
        create_playlist_impl(
            name,
            description,
            track_uris=track_uris,
            public=public,
        )
    )


@mcp.tool
def add_tracks(playlist_id: str, track_uris: list[str]) -> dict:
    """Add tracks to an existing playlist, skipping duplicates."""
    return _handle_tool(add_tracks_impl(playlist_id, track_uris))


@mcp.tool
def get_playlist(playlist_id: str, include_tracks: bool = True) -> dict:
    """Get playlist metadata and optionally its tracks."""
    return _handle_tool(get_playlist_impl(playlist_id, include_tracks=include_tracks))


@mcp.tool
def generate_playlist(
    name: str,
    prompt: str,
    target_length: int = 20,
    public: bool = False,
) -> dict:
    """Generate a playlist from a natural-language prompt using an LLM."""
    async def _run() -> dict:
        from spotify.client import get_client

        taste = get_taste_store()
        songs = await generate_songs(
            prompt,
            target_length=target_length,
            preferences=taste.preferences_summary(),
        )
        client = get_client()
        uris, unresolved = await resolve_generated_songs(client, songs)
        created = await create_playlist_impl(
            name,
            prompt,
            track_uris=uris,
            public=public,
        )
        playlist = await get_playlist_impl(created["playlist_id"], include_tracks=True)
        taste.record_playlist(created["playlist_id"], playlist.get("tracks", []))
        return {
            **created,
            "requested_tracks": len(songs),
            "resolved_tracks": len(uris),
            "unresolved_tracks": unresolved,
            "summary": f"Created playlist with {len(uris)} tracks from prompt.",
        }

    try:
        return run_async(_run())
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool
def remove_tracks(playlist_id: str, track_uris: list[str]) -> dict:
    """Remove tracks from a playlist by Spotify track URI."""
    return _handle_tool(remove_tracks_impl(playlist_id, track_uris))


@mcp.tool
def modify_playlist(playlist_id: str, instruction: str) -> dict:
    """Modify an existing playlist using a natural-language instruction."""
    async def _run() -> dict:
        from spotify.client import get_client

        playlist = await get_playlist_impl(playlist_id, include_tracks=True)
        tracks = playlist.get("tracks", [])
        plan = await plan_playlist_edit(tracks, instruction)

        removed = 0
        if plan.remove_uris:
            result = await remove_tracks_impl(playlist_id, plan.remove_uris)
            removed = result["tracks_removed"]

        added = 0
        unresolved: list[dict] = []
        if plan.add:
            client = get_client()
            uris, unresolved = await resolve_generated_songs(client, plan.add)
            if uris:
                add_result = await add_tracks_impl(playlist_id, uris)
                added = add_result["tracks_added"]

        updated = await get_playlist_impl(playlist_id, include_tracks=True)
        taste = get_taste_store()
        taste.record_playlist(playlist_id, updated.get("tracks", []))
        return {
            "playlist_id": playlist_id,
            "url": updated["url"],
            "tracks_added": added,
            "tracks_removed": removed,
            "unresolved_tracks": unresolved,
            "notes": plan.notes,
            "repeated_artists": updated.get("repeated_artists", []),
        }

    try:
        return run_async(_run())
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool
def analyze_playlist(playlist_id: str) -> dict:
    """Analyze playlist mood, energy, valence, and artist diversity."""
    return _handle_tool(analyze_playlist_impl(playlist_id))


@mcp.tool
def recommend_tracks(
    playlist_id: str,
    limit: int = 10,
    target_energy: float | None = None,
    target_valence: float | None = None,
    target_danceability: float | None = None,
) -> dict:
    """Recommend tracks based on an existing playlist."""
    return _handle_tool(
        recommend_tracks_impl(
            playlist_id,
            limit=limit,
            target_energy=target_energy,
            target_valence=target_valence,
            target_danceability=target_danceability,
        )
    )


@mcp.tool
def optimize_playlist(playlist_id: str, goal: str = "diverse") -> dict:
    """Improve a playlist for energy, calm, or diversity."""
    async def _run() -> dict:
        analysis = await analyze_playlist_impl(playlist_id)
        targets = {
            "energy": {"target_energy": 0.85, "target_valence": 0.6},
            "calm": {"target_energy": 0.25, "target_valence": 0.45},
            "diverse": {},
        }
        target_kwargs = targets.get(goal, targets["diverse"])
        recommendations = await recommend_tracks_impl(playlist_id, limit=10, **target_kwargs)
        rec_uris = [track["uri"] for track in recommendations.get("recommendations", [])]
        added = 0
        if rec_uris:
            add_result = await add_tracks_impl(playlist_id, rec_uris)
            added = add_result["tracks_added"]

        playlist = await get_playlist_impl(playlist_id, include_tracks=True)
        repeated = playlist.get("repeated_artists", [])
        removed = 0
        if goal == "diverse" and repeated:
            tracks = playlist.get("tracks", [])
            remove_uris: list[str] = []
            from collections import Counter

            counts: Counter[str] = Counter()
            for track in tracks:
                for artist in track.get("artists", []):
                    counts[artist] += 1
            for track in reversed(tracks):
                artists = track.get("artists", [])
                if any(counts[artist] > 2 for artist in artists):
                    remove_uris.append(track["uri"])
                    for artist in artists:
                        counts[artist] -= 1
            if remove_uris:
                remove_result = await remove_tracks_impl(playlist_id, remove_uris)
                removed = remove_result["tracks_removed"]

        updated = await get_playlist_impl(playlist_id, include_tracks=True)
        return {
            "playlist_id": playlist_id,
            "url": updated["url"],
            "goal": goal,
            "analysis": analysis,
            "tracks_added": added,
            "tracks_removed": removed,
            "summary": f"Optimized playlist for '{goal}'.",
        }

    return _handle_tool(_run())


@mcp.tool
def get_user_preferences() -> dict:
    """Return accumulated taste profile from past playlist activity."""
    taste = get_taste_store()
    profile = taste.load()
    return {
        "summary": taste.preferences_summary(),
        "profile": profile,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Playlist Agent MCP Server")
    parser.add_argument("--http", action="store_true", help="Run Streamable HTTP server")
    parser.add_argument("--stdio", action="store_true", help="Run stdio transport")
    args = parser.parse_args()

    if args.http:
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8080"))
        mcp.run(transport="http", host=host, port=port)
    elif args.stdio:
        mcp.run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
