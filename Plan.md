# AI Spotify Playlist MCP

An AI-powered Spotify playlist creator that works through ChatGPT or Claude using MCP (Model Context Protocol).

The user can simply describe a playlist in natural language, and the assistant will create it directly in their Spotify account.

---

## Overview

This project turns playlist creation into a conversational experience.

Example prompts:

- Create a workout playlist with high-energy hip-hop
- Make a chill evening playlist with soft rap and R&B
- Add more songs like Tokyo Drift
- Remove slow songs from my gym playlist

The assistant interprets the request, calls the MCP tool, searches Spotify tracks, creates the playlist, and adds songs automatically.

---

## Why This Project

This is more than a Spotify wrapper. It demonstrates:

- MCP tool development
- Spotify OAuth integration
- Third-party API integration
- AI agent workflow
- Natural language playlist generation
- Playlist editing and optimization
- Resume-worthy backend engineering

---

## Core Features

- Spotify OAuth login
- Create playlists in the user’s Spotify account
- Search tracks using Spotify API
- Add tracks to a playlist
- Generate playlists from natural language prompts
- Modify existing playlists through chat
- Analyze playlist mood, energy, and style
- Remove duplicates and improve playlist diversity
- Return Spotify playlist link after creation

---

## How It Works

1. User sends a prompt in ChatGPT or Claude.
2. The assistant calls the MCP tool.
3. The backend interprets the request.
4. Songs are generated or searched.
5. Spotify playlist is created.
6. Tracks are added automatically.
7. The playlist URL is returned to the user.

---

## Project Plan

### Phase 1: MVP
Build the basic Spotify automation flow.

Goals:
- Spotify OAuth authentication
- Create playlist
- Search songs
- Add tracks
- Return playlist URL

Deliverable:
- A working Python backend that can create playlists from a song list.

---

### Phase 2: MCP Integration
Expose Spotify actions as MCP tools so Claude or ChatGPT can use them.

Goals:
- Build MCP server in Python
- Add tools like `create_playlist`, `search_track`, `add_tracks`
- Connect the tools to an AI assistant

Deliverable:
- User can create playlists by chatting with Claude or ChatGPT.

---

### Phase 3: AI Playlist Generation
Convert a simple prompt into a full playlist.

Goals:
- Prompt to song list generation
- Genre and mood understanding
- Artist preference support
- Better track matching

Deliverable:
- User can say: “Create a gym playlist,” and get a full playlist automatically.

---

### Phase 4: Smart Playlist Editing
Allow the assistant to improve existing playlists.

Goals:
- Add songs to an existing playlist
- Remove unwanted songs
- Make the playlist more energetic, calm, or diverse
- Detect repetitive artists or tracks

Deliverable:
- User can refine playlists through conversation.

---

### Phase 5: Advanced Intelligence
Make the project feel like a real AI music agent.

Goals:
- Taste profile analysis
- Track recommendation engine
- Playlist optimization
- Memory of user preferences
- Better discovery of similar songs

Deliverable:
- A personalized playlist agent that improves over time.

---

## Suggested MCP Tools

- `spotify_login`
- `create_playlist`
- `search_track`
- `add_tracks`
- `remove_tracks`
- `get_playlist`
- `generate_playlist`
- `modify_playlist`
- `analyze_playlist`
- `recommend_tracks`

---

## Suggested Tech Stack

- Python 3.12
- FastMCP
- Spotipy or direct Spotify Web API calls
- Pydantic
- httpx
- OAuth 2.0
- OpenAI or Claude for prompt-based generation

---

## Example User Flow

### Create a new playlist
User:
> Create a workout playlist with aggressive rap and hype songs.

Assistant:
- Generates song ideas
- Searches Spotify
- Creates playlist
- Adds tracks
- Returns playlist link

### Modify an existing playlist
User:
> Add more Drake songs and make it less repetitive.

Assistant:
- Reads current playlist
- Finds suitable tracks
- Adds new songs
- Removes duplicates if needed

---

## Project Structure

```text
spotify-mcp/
├── server.py
├── tools/
│   ├── playlist.py
│   ├── search.py
│   ├── recommendation.py
│   └── analysis.py
├── spotify/
│   ├── auth.py
│   ├── client.py
│   └── models.py
├── llm/
│   ├── song_generator.py
│   └── playlist_editor.py
├── prompts/
├── tests/
└── README.md