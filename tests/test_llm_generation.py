import json

import pytest

from llm.provider import parse_json_response


def test_parse_json_response_strips_markdown_fence():
    text = """```json
[{"title": "Song", "artist": "Artist", "reason": "fits"}]
```"""
    data = parse_json_response(text)
    assert isinstance(data, list)
    assert data[0]["title"] == "Song"


@pytest.mark.asyncio
async def test_generate_songs_with_mock_provider(monkeypatch):
    class FakeProvider:
        async def complete(self, prompt: str) -> str:
            return json.dumps(
                [
                    {"title": "Lose Yourself", "artist": "Eminem", "reason": "hype"},
                    {"title": "Stronger", "artist": "Kanye West", "reason": "energy"},
                ]
            )

    monkeypatch.setattr("llm.song_generator.get_llm_provider", lambda: FakeProvider())

    from llm.song_generator import generate_songs

    songs = await generate_songs("workout playlist", target_length=2)
    assert len(songs) == 2
    assert songs[0].title == "Lose Yourself"
