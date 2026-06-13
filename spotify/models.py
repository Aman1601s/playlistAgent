from __future__ import annotations

from pydantic import BaseModel, Field


class SpotifyUser(BaseModel):
    id: str
    display_name: str | None = None


class SpotifyTrack(BaseModel):
    id: str
    uri: str
    name: str
    artists: list[str] = Field(default_factory=list)
    album: str | None = None
    popularity: int | None = None


class SpotifyPlaylist(BaseModel):
    id: str
    uri: str
    name: str
    description: str | None = None
    url: str
    owner_id: str | None = None
    track_count: int = 0


class SearchResult(BaseModel):
    query: str
    tracks: list[SpotifyTrack] = Field(default_factory=list)


class AudioFeatures(BaseModel):
    track_id: str
    energy: float
    valence: float
    danceability: float
    tempo: float
    acousticness: float
    instrumentalness: float


class PlaylistAnalysis(BaseModel):
    playlist_id: str
    track_count: int
    avg_energy: float
    avg_valence: float
    avg_danceability: float
    avg_tempo: float
    top_artists: list[str] = Field(default_factory=list)
    repeated_artists: list[str] = Field(default_factory=list)
    mood: str
    summary: str


class GeneratedSong(BaseModel):
    title: str
    artist: str
    reason: str | None = None


class PlaylistEditPlan(BaseModel):
    add: list[GeneratedSong] = Field(default_factory=list)
    remove_uris: list[str] = Field(default_factory=list)
    notes: str | None = None
