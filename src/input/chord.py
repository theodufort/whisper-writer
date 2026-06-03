from __future__ import annotations

from input.events import InputEvent, KeyCode


class KeyChord:
    """Represents a combination of keys that need to be pressed simultaneously."""

    def __init__(self, keys: set[KeyCode | frozenset[KeyCode]]):
        """Initialize the KeyChord."""
        self.keys = keys
        self.pressed_keys: set[KeyCode] = set()

    def update(self, key: KeyCode, event_type: InputEvent) -> bool:
        """Update the state of pressed keys and check if the chord is active."""
        if event_type == InputEvent.KEY_PRESS:
            self.pressed_keys.add(key)
        elif event_type == InputEvent.KEY_RELEASE:
            self.pressed_keys.discard(key)

        return self.is_active()

    def is_active(self) -> bool:
        """Check if all keys in the chord are currently pressed."""
        for key in self.keys:
            if isinstance(key, frozenset):
                if not any(k in self.pressed_keys for k in key):
                    return False
            elif key not in self.pressed_keys:
                return False
        return True


__all__ = ["KeyChord"]
