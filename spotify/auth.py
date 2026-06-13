from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

DEFAULT_SCOPES = [
    "playlist-modify-public",
    "playlist-modify-private",
    "playlist-read-private",
    "user-read-private",
]

TOKEN_DIR = Path.home() / ".playlist_agent"
TOKEN_PATH = TOKEN_DIR / "tokens.json"
PROFILE_PATH = TOKEN_DIR / "profile.json"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyAuthError(Exception):
    pass


@dataclass
class SpotifySettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]

    @classmethod
    def from_env(cls) -> SpotifySettings:
        client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = os.getenv(
            "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"
        )
        if not client_id or not client_secret:
            raise SpotifyAuthError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env"
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=DEFAULT_SCOPES,
        )


class SpotifyAuth:
    def __init__(self, settings: SpotifySettings | None = None) -> None:
        self.settings = settings or SpotifySettings.from_env()
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def is_authenticated(self) -> bool:
        tokens = self.load_tokens()
        return bool(tokens.get("refresh_token"))

    def load_tokens(self) -> dict[str, Any]:
        if not TOKEN_PATH.exists():
            return {}
        return json.loads(TOKEN_PATH.read_text())

    def save_tokens(self, tokens: dict[str, Any]) -> None:
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        existing = self.load_tokens()
        existing.update(tokens)
        TOKEN_PATH.write_text(json.dumps(existing, indent=2))

    def build_authorize_url(self, state: str, code_challenge: str) -> str:
        from urllib.parse import urlencode

        params = {
            "client_id": self.settings.client_id,
            "response_type": "code",
            "redirect_uri": self.settings.redirect_uri,
            "scope": " ".join(self.settings.scopes),
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str, code_verifier: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.redirect_uri,
            "client_id": self.settings.client_id,
            "code_verifier": code_verifier,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                TOKEN_URL,
                data=data,
                auth=(self.settings.client_id, self.settings.client_secret),
            )
        if response.status_code >= 400:
            raise SpotifyAuthError(f"Token exchange failed: {response.text}")
        payload = response.json()
        self.save_tokens(payload)
        self._access_token = payload["access_token"]
        self._expires_at = time.time() + payload.get("expires_in", 3600) - 60
        return payload

    def refresh_access_token(self) -> str:
        tokens = self.load_tokens()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise SpotifyAuthError(
                "No refresh token found. Run `python authenticate.py` first."
            )

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                TOKEN_URL,
                data=data,
                auth=(self.settings.client_id, self.settings.client_secret),
            )
        if response.status_code >= 400:
            raise SpotifyAuthError(f"Token refresh failed: {response.text}")

        payload = response.json()
        if "refresh_token" not in payload:
            payload["refresh_token"] = refresh_token
        self.save_tokens(payload)
        self._access_token = payload["access_token"]
        self._expires_at = time.time() + payload.get("expires_in", 3600) - 60
        return self._access_token

    def get_access_token(self) -> str:
        if self._access_token and time.time() < self._expires_at:
            return self._access_token
        return self.refresh_access_token()

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def login_status(self) -> dict[str, Any]:
        if not self.is_authenticated:
            return {
                "authenticated": False,
                "message": "Run `python authenticate.py` to connect Spotify.",
            }
        return {
            "authenticated": True,
            "message": "Spotify is connected.",
            "token_path": str(TOKEN_PATH),
        }
