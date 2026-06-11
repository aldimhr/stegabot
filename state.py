"""In-memory per-chat session state for encode flow."""
from typing import Any


class SessionManager:
    def __init__(self):
        self._sessions: dict[int, dict[str, Any]] = {}

    def get(self, chat_id: int) -> dict[str, Any]:
        """Get session for chat_id, creating default if needed."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = {
                "step": None,        # 'awaiting_cover' | 'awaiting_secret' | 'awaiting_decode' | 'awaiting_detect' | None
                "method": None,      # 'zwc' | 'snow' | 'acrostic' | 'homoglyph'
                "cover": None,       # Cover text entered by user
                "encrypt": False,    # Whether AES encryption is enabled
                "passphrase": None,  # Optional AES key
            }
        return self._sessions[chat_id]

    def update(self, chat_id: int, **kwargs) -> None:
        """Update session fields."""
        session = self.get(chat_id)
        session.update(kwargs)

    def reset(self, chat_id: int) -> None:
        """Reset session to defaults."""
        if chat_id in self._sessions:
            del self._sessions[chat_id]

    def is_encoding(self, chat_id: int) -> bool:
        """Check if user is mid-encode flow."""
        session = self.get(chat_id)
        return session["step"] is not None
