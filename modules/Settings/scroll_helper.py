from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt5.QtCore import QTimer


if TYPE_CHECKING:
    from ...modules.Settings.SettingsUI import SettingsModule

class SettingsScrollHelper:
    @staticmethod
    def scroll_to_module(settings_module: "SettingsModule", module_key: str, *, attempt: int = 0, max_attempts: int = 6) -> None:
        """Center the scroll area on the given module card. Retries while data loads."""

        if not module_key or settings_module is None:
            return

        # Rebuild cards if not ready
        if not settings_module._module_cards:
            settings_module._build_module_cards()

        # Locate the target card
        target_card = None
        for name, card in settings_module._module_cards.items():
            if str(name).lower() == str(module_key).lower():
                target_card = card
                break

        # Retry while cards load (e.g., async user fetch)
        if not target_card:
            if attempt >= max_attempts:
                return
            QTimer.singleShot(
                150,
                lambda: SettingsScrollHelper.scroll_to_module(
                    settings_module,
                    module_key,
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                ),
            )
            return

        def _scroll():
            try:
                viewport_h = settings_module.scroll_area.viewport().height()
                container_h = settings_module.cards_container.height()
                if viewport_h == 0 or container_h == 0:
                    if attempt < max_attempts:
                        QTimer.singleShot(
                            150,
                            lambda: SettingsScrollHelper.scroll_to_module(
                                settings_module,
                                module_key,
                                attempt=attempt + 1,
                                max_attempts=max_attempts,
                            ),
                        )
                    return

                center_y = target_card.mapTo(settings_module.cards_container, target_card.rect().center()).y()
                offset = max(0, center_y - (viewport_h // 2))

                bar = settings_module.scroll_area.verticalScrollBar()
                if bar:
                    bar.setValue(offset)
                target_card.setFocus()
            except Exception as exc:
                print(f"[SettingsScrollHelper] Failed to scroll to module {module_key}: {exc}")

        # Give the layout a brief moment on first attempt, immediate on retries
        initial_delay = 150 if attempt == 0 else 0
        QTimer.singleShot(initial_delay, _scroll)
