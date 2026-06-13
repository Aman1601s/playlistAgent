#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from spotify.auth import TOKEN_PATH, SpotifyAuth, SpotifyAuthError

load_dotenv()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None
    error: str | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "error" in params:
            OAuthCallbackHandler.error = params["error"][0]
            self._respond("Authentication failed. You can close this window.")
            return

        code = params.get("code", [None])[0]
        if not code:
            OAuthCallbackHandler.error = "missing_code"
            self._respond("Missing authorization code.")
            return

        OAuthCallbackHandler.auth_code = code
        self._respond("Spotify connected successfully. You can close this window.")

    def _respond(self, message: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"<html><body><p>{message}</p></body></html>".encode())

    def log_message(self, format: str, *args: object) -> None:
        return


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
    verifier = verifier.rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("utf-8")).digest()
    ).decode("utf-8")
    challenge = challenge.rstrip("=")
    return verifier, challenge


def main() -> None:
    auth = SpotifyAuth()
    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    auth_url = auth.build_authorize_url(state=state, code_challenge=challenge)

    parsed = urlparse(auth.settings.redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8888

    server = HTTPServer((host, port), OAuthCallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    print("Opening browser for Spotify login...")
    print(f"If it does not open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)
    thread.join(timeout=120)
    server.server_close()

    if OAuthCallbackHandler.error:
        raise SpotifyAuthError(OAuthCallbackHandler.error)
    if not OAuthCallbackHandler.auth_code:
        raise SpotifyAuthError("Timed out waiting for Spotify authorization.")

    auth.exchange_code(OAuthCallbackHandler.auth_code, verifier)
    print(f"Authentication complete. Tokens saved to {TOKEN_PATH}")


if __name__ == "__main__":
    try:
        main()
    except SpotifyAuthError as exc:
        print(f"Authentication failed: {exc}")
        raise SystemExit(1) from exc
