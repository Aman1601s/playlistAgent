from __future__ import annotations

from spotify.models import GeneratedSong
from llm.provider import get_llm_provider, load_prompt, parse_json_response


async def generate_songs(
    prompt: str,
    *,
    target_length: int = 20,
    preferences: str = "None",
) -> list[GeneratedSong]:
    provider = get_llm_provider()
    full_prompt = load_prompt(
        "generate_playlist.txt",
        prompt=prompt,
        preferences=preferences,
    )
    response = await provider.complete(full_prompt)
    data = parse_json_response(response)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of songs")

    songs: list[GeneratedSong] = []
    for item in data[:target_length]:
        songs.append(
            GeneratedSong(
                title=item["title"],
                artist=item["artist"],
                reason=item.get("reason"),
            )
        )
    return songs
