# Playlist MCP Agent

Create, manage, and optimize Spotify playlists through natural language using AI and MCP.

## Prerequisites

1. **Python 3.12+**
2. **Spotify Developer app**
   - Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Copy the Client ID and Client Secret
   - Add redirect URI: `http://127.0.0.1:8888/callback`
   - Add your Spotify account under **User Management** (required for write operations in Development Mode)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llm]"

cp .env.example .env
# Edit .env with your Spotify credentials
```

## Authenticate with Spotify

Run once to save a refresh token locally:

```bash
python authenticate.py
```

Tokens are stored at `~/.playlist_agent/tokens.json`.

## Run the MCP server

Streamable HTTP (recommended):

```bash
python server.py --http
```

Server URL: `http://127.0.0.1:8080/mcp`

Stdio mode (local dev):

```bash
python server.py --stdio
```

## Connect to Claude Desktop / Cursor

Add an MCP server with:

- **Type:** MCP (Streamable HTTP)
- **URL:** `http://127.0.0.1:8080/mcp`

Example Cursor config:

```json
{
  "mcpServers": {
    "playlist-agent": {
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `spotify_login` | Check Spotify auth status |
| `search_track` | Search Spotify tracks |
| `create_playlist` | Create a new playlist |
| `add_tracks` | Add tracks to a playlist |
| `get_playlist` | Fetch playlist metadata and tracks |
| `generate_playlist` | Generate a playlist from a natural-language prompt |
| `remove_tracks` | Remove tracks from a playlist |
| `modify_playlist` | Edit a playlist using natural language |
| `analyze_playlist` | Analyze mood, energy, and diversity |
| `recommend_tracks` | Recommend tracks based on a playlist |
| `optimize_playlist` | Improve a playlist for energy, calm, or diversity |

## Smoke test (Phase 1)

After authenticating:

```bash
python smoke_test.py
```

## Tests

```bash
pytest
```

Integration tests (requires real Spotify auth):

```bash
RUN_INTEGRATION=1 pytest -m integration
```

## Environment variables

See [.env.example](.env.example) for all options.

LLM generation (Phase 3+) requires `LLM_PROVIDER` (`openai` or `anthropic`) and the matching API key.
