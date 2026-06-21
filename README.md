# Playlist MCP Agent

Create, manage, and optimize Spotify playlists through natural language using AI and MCP.

## Prerequisites

1. **Python 3.12+**
2. **Spotify Developer app**

   * Create an app at https://developer.spotify.com/dashboard
   * Copy the Client ID and Client Secret
   * Add redirect URI: `http://127.0.0.1:8888/callback`
   * Add your Spotify account under **User Management** (required for write operations in Development Mode)

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

Tokens are stored at:

```text
~/.playlist_agent/tokens.json
```

## Run the MCP Server

### Streamable HTTP (Recommended)

```bash
python server.py --http
```

Server URL:

```text
http://127.0.0.1:8080/mcp
```

### Stdio Mode (Claude Desktop)

```bash
python server.py --stdio
```

## Connect to Claude Desktop

Edit:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add:

```json
{
  "mcpServers": {
    "playlistAgent": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": [
        "/absolute/path/to/server.py",
        "--stdio"
      ]
    }
  }
}
```

Example:

```json
{
  "mcpServers": {
    "playlistAgent": {
      "command": "/Users/amankumar/Documents/projects/playlistAgent/.venv/bin/python",
      "args": [
        "/Users/amankumar/Documents/projects/playlistAgent/server.py",
        "--stdio"
      ]
    }
  }
}
```

Restart Claude Desktop after updating the configuration.

### Verify Claude Connection

Check logs:

```text
~/Library/Logs/Claude/
```

Successful startup should show:

```text
Server started and connected successfully
```

## Connect to Cursor

Add an MCP server with:

* Type: MCP (Streamable HTTP)
* URL: `http://127.0.0.1:8080/mcp`

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

| Tool              | Description                                        |
| ----------------- | -------------------------------------------------- |
| spotify_login     | Check Spotify auth status                          |
| search_track      | Search Spotify tracks                              |
| create_playlist   | Create a new playlist                              |
| add_tracks        | Add tracks to a playlist                           |
| get_playlist      | Fetch playlist metadata and tracks                 |
| generate_playlist | Generate a playlist from a natural-language prompt |
| remove_tracks     | Remove tracks from a playlist                      |
| modify_playlist   | Edit a playlist using natural language             |
| analyze_playlist  | Analyze mood, energy, and diversity                |
| recommend_tracks  | Recommend tracks based on a playlist               |
| optimize_playlist | Improve a playlist for energy, calm, or diversity  |

## Smoke Test (Phase 1)

After authenticating:

```bash
python smoke_test.py
```

## Tests

```bash
pytest
```

Integration tests:

```bash
RUN_INTEGRATION=1 pytest -m integration
```

Requires a valid Spotify authentication setup.

## Environment Variables

See `.env.example` for all supported options.

LLM generation (Phase 3+) requires:

```text
LLM_PROVIDER=openai
```

or

```text
LLM_PROVIDER=anthropic
```

and the corresponding API key.

## Architecture

```text
Claude / Cursor / ChatGPT
            │
            ▼
      PlaylistAgent MCP
            │
    ┌───────┼────────┐
    ▼       ▼        ▼
 Spotify   LLM    Recommendation
   API    Provider    Engine
```

## Roadmap

### Phase 1

* Spotify OAuth
* Search tracks
* Create playlists
* Add tracks

### Phase 2

* MCP integration
* Claude Desktop support
* Cursor support

### Phase 3

* AI playlist generation
* Mood and genre understanding

### Phase 4

* Playlist editing
* Playlist optimization
* Recommendation engine

### Phase 5

* Taste profile engine
* Personalized playlist memory
* Advanced music discovery

```
```
