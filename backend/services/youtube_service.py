import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow, Flow
    HAS_YOUTUBE_CLIENT = True
except ImportError:
    HAS_YOUTUBE_CLIENT = False
    build = None
    MediaFileUpload = None
    Credentials = None
    Request = None
    InstalledAppFlow = None
    Flow = None

from backend.config import settings

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

# Tag always added to every SkullBot upload
SKULLBOT_MANDATORY_TAG = "skullbot.ai"
REELBOT_MANDATORY_TAG = "skullbot.ai"


class YouTubeService:
    TOKEN_FILE = settings.STORAGE_DIR / "youtube_token.json"
    CLIENT_SECRET_FILE = settings.STORAGE_DIR / "client_secret.json"

    # ─────────────────────────────────────────────────────────────────────────
    # Auth helpers
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def _is_web_client(cls) -> bool:
        """Returns True if the saved client_secret.json is a Web-type OAuth client."""
        if not cls.CLIENT_SECRET_FILE.exists():
            return False
        try:
            data = json.loads(cls.CLIENT_SECRET_FILE.read_text())
            return "web" in data
        except Exception:
            return False

    @classmethod
    def get_auth_status(cls) -> Dict[str, Any]:
        if not HAS_YOUTUBE_CLIENT or not cls.TOKEN_FILE.exists():
            return {"authenticated": False, "channel_title": None}
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(cls.TOKEN_FILE.read_text()), SCOPES
            )
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                cls.TOKEN_FILE.write_text(creds.to_json())

            youtube = build('youtube', 'v3', credentials=creds)
            resp = youtube.channels().list(mine=True, part='snippet').execute()
            items = resp.get('items', [])
            if items:
                snippet = items[0].get('snippet', {})
                return {
                    "authenticated": True,
                    "channel_title": snippet.get('title', 'My Channel'),
                    "thumbnail": snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                }
            return {"authenticated": True, "channel_title": "YouTube Channel", "thumbnail": ""}
        except Exception as e:
            print(f"YouTube auth status error: {e}")
            return {"authenticated": False, "channel_title": None, "error": str(e)}

    @classmethod
    def save_client_secret(cls, client_secret_json_str: str) -> bool:
        """Saves Google OAuth2 client_secret JSON (supports both Web and Desktop types)."""
        try:
            data = json.loads(client_secret_json_str)
            settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            cls.CLIENT_SECRET_FILE.write_text(json.dumps(data, indent=2))
            # Clear any old token so re-auth happens with the new credentials
            if cls.TOKEN_FILE.exists():
                cls.TOKEN_FILE.unlink()
            return True
        except Exception as e:
            print(f"Error saving client_secret: {e}")
            return False

    @classmethod
    def get_credentials(cls) -> Optional[Credentials]:
        """Retrieves or refreshes YouTube OAuth credentials.
        Handles both 'installed' (Desktop) and 'web' client types."""
        creds = None

        # Load cached token
        if cls.TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(cls.TOKEN_FILE.read_text()), SCOPES
                )
            except Exception as e:
                print(f"Token load error: {e}")

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                cls.TOKEN_FILE.write_text(creds.to_json())
                return creds
            except Exception as e:
                print(f"Token refresh error: {e}")
                creds = None

        if creds and creds.valid:
            return creds

        # No valid token — start OAuth flow
        if not cls.CLIENT_SECRET_FILE.exists():
            raise RuntimeError(
                "YouTube credentials not found. Please paste your client_secret.json "
                "in ⚙️ Configure → YouTube Auto-Upload."
            )

        try:
            if cls._is_web_client():
                # Web client: use run_local_server (opens browser for consent)
                flow = Flow.from_client_secrets_file(
                    str(cls.CLIENT_SECRET_FILE),
                    scopes=SCOPES,
                    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
                )
                # Fall back to InstalledAppFlow which also works for web clients
                # when redirect_uri is localhost
                flow2 = InstalledAppFlow.from_client_config(
                    json.loads(cls.CLIENT_SECRET_FILE.read_text()),
                    scopes=SCOPES
                )
                creds = flow2.run_local_server(port=0)
            else:
                # Desktop / Installed app client
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(cls.CLIENT_SECRET_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)

            cls.TOKEN_FILE.write_text(creds.to_json())
            return creds
        except Exception as e:
            raise RuntimeError(f"YouTube OAuth flow failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Upload
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def upload_video(
        cls,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "public",
        category_id: str = "24",
    ) -> Dict[str, Any]:
        """Uploads a video to YouTube with full SEO metadata.
        Always appends #reelbot.ai to every video's tags."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        creds = cls.get_credentials()
        if not creds:
            raise RuntimeError(
                "YouTube is not authenticated. Please connect your account in ⚙️ Configure → YouTube Setup."
            )

        youtube = build('youtube', 'v3', credentials=creds)

        # Clean tags and always inject #skullbot.ai
        clean_tags = [t.lstrip("#").strip() for t in tags if t.strip()]
        if SKULLBOT_MANDATORY_TAG not in clean_tags:
            clean_tags.append(SKULLBOT_MANDATORY_TAG)

        # Add skullbot.ai to description footer too
        desc_with_branding = (
            description.strip()
            + f"\n\n🎬 Made with SkullBot.Ai — AI-Powered True Crime & Documentary Engine\n"
            + "#skullbot.ai #shorts #truecrime #documentary"
        )

        body = {
            'snippet': {
                'title': title[:100],
                'description': desc_with_branding[:5000],
                'tags': clean_tags[:30],
                'categoryId': category_id,
                'defaultLanguage': 'en',
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False,
                'madeForKids': False,
            }
        }

        media = MediaFileUpload(str(video_path), mimetype='video/mp4', resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"YouTube Upload: {int(status.progress() * 100)}%")

        video_id = response.get('id')
        return {
            "success": True,
            "video_id": video_id,
            "watch_url": f"https://youtube.com/shorts/{video_id}",
            "title": title,
            "privacy_status": privacy_status,
            "tags": clean_tags,
        }


    @classmethod
    def get_auth_status(cls) -> Dict[str, Any]:
        """Checks if YouTube account is authenticated."""
        if not cls.TOKEN_FILE.exists():
            return {"authenticated": False, "channel_title": None}
        
        try:
            with open(cls.TOKEN_FILE, "r") as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(cls.TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            
            youtube = build('youtube', 'v3', credentials=creds)
            channels_response = youtube.channels().list(mine=True, part='snippet').execute()
            items = channels_response.get('items', [])
            if items:
                snippet = items[0].get('snippet', {})
                return {
                    "authenticated": True,
                    "channel_title": snippet.get('title', 'My Channel'),
                    "thumbnail": snippet.get('thumbnails', {}).get('default', {}).get('url', '')
                }
            return {"authenticated": True, "channel_title": "YouTube Channel", "thumbnail": ""}
        except Exception as e:
            print(f"Error checking YouTube auth status: {e}")
            return {"authenticated": False, "channel_title": None, "error": str(e)}

    @classmethod
    def save_client_secret(cls, client_secret_json_str: str) -> bool:
        """Saves Google OAuth2 client_secret JSON."""
        try:
            data = json.loads(client_secret_json_str)
            settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.CLIENT_SECRET_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving client_secret: {e}")
            return False

    @classmethod
    def get_credentials(cls) -> Optional[Credentials]:
        """Retrieves or refreshes YouTube OAuth credentials."""
        creds = None
        if cls.TOKEN_FILE.exists():
            try:
                with open(cls.TOKEN_FILE, "r") as f:
                    token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            except Exception as e:
                print(f"Error loading token: {e}")

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(cls.TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

        if not creds or not creds.valid:
            if not cls.CLIENT_SECRET_FILE.exists():
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(cls.CLIENT_SECRET_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
                with open(cls.TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"OAuth flow error: {e}")
                return None

        return creds

    @classmethod
    def upload_video(
        cls,
        video_path: Path,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "public",
        category_id: str = "24"  # Entertainment / Education
    ) -> Dict[str, Any]:
        """Uploads a video to YouTube with viral SEO metadata."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        creds = cls.get_credentials()
        if not creds:
            raise RuntimeError(
                "YouTube is not authenticated. Please connect your YouTube account in Configure -> YouTube Setup."
            )

        youtube = build('youtube', 'v3', credentials=creds)

        # Clean tags
        clean_tags = [t.replace("#", "").strip() for t in tags if t.strip()]

        body = {
            'snippet': {
                'title': title[:100],
                'description': description[:5000],
                'tags': clean_tags[:30],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype='video/mp4',
            resumable=True
        )

        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"YouTube Upload Progress: {int(status.progress() * 100)}%")

        video_id = response.get('id')
        watch_url = f"https://youtube.com/shorts/{video_id}"

        return {
            "success": True,
            "video_id": video_id,
            "watch_url": watch_url,
            "title": title,
            "privacy_status": privacy_status
        }
