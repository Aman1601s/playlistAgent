from __future__ import annotations

from spotify.models import GeneratedSong, PlaylistEditPlan
from llm.provider import get_llm_provider, load_prompt, parse_json_response


async def plan_playlist_edit(tracks: list[dict], instruction: str) -> PlaylistEditPlan:
    provider = get_llm_provider()
    track_lines = [
        f"- {track['name']} by {', '.join(track['artists'])} ({track['uri']})"
        for track in tracks
    ]
    prompt = load_prompt(
        "modify_playlist.txt",
        tracks="\n".join(track_lines) or "No tracks",
        instruction=instruction,
    )
    response = await provider.complete(prompt)
    data = parse_json_response(response)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")

    add = [
        GeneratedSong(
            title=item["title"],
            artist=item["artist"],
            reason=item.get("reason"),
        )
        for item in data.get("add", [])
    ]
    return PlaylistEditPlan(
        add=add,
        remove_uris=data.get("remove_uris", []),
        notes=data.get("notes"),
    )
