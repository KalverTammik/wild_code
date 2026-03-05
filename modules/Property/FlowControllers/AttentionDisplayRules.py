from __future__ import annotations

from typing import Iterable, List, Sequence
from ....languages.translation_keys import TranslationKeys


class AttentionDisplayRules:
    """Pure helpers for building the SignalTest/Property-style Attention text."""

    @staticmethod
    def _normalize_causes(*cause_lists: Sequence[object] | None) -> List[str]:
        combined: List[str] = []
        for lst in cause_lists:
            if not lst:
                continue
            for c in lst:
                s = str(c).strip()
                if s:
                    combined.append(s)
        return combined

    @staticmethod
    def combined_causes(main_causes: Sequence[object] | None, backend_causes: Sequence[object] | None) -> List[str]:
        return AttentionDisplayRules._normalize_causes(main_causes, backend_causes)

    @staticmethod
    def _translate_cause_text(cause: str, translate=None) -> str:
        text = str(cause or "").strip()
        if not text:
            return ""

        if not callable(translate):
            return text

        key_by_cause = {
            "backend lookup failed": TranslationKeys.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED,
            "missing in backend": TranslationKeys.ATTENTION_CAUSE_MISSING_BACKEND,
            "archived only": TranslationKeys.ATTENTION_CAUSE_ARCHIVED_ONLY,
            "import newer": TranslationKeys.ATTENTION_CAUSE_IMPORT_NEWER,
            "missing in main layer": TranslationKeys.ATTENTION_CAUSE_MISSING_MAIN_LAYER,
            "main layer older": TranslationKeys.ATTENTION_CAUSE_MAIN_LAYER_OLDER,
        }

        key = key_by_cause.get(text.lower())
        if not key:
            return text

        try:
            translated = translate(key)
        except Exception:
            translated = ""

        translated = str(translated or "").strip()
        return translated or text

    @staticmethod
    def build_attention_text(
        main_causes: Sequence[object] | None,
        backend_causes: Sequence[object] | None,
        *,
        main_done: bool,
        backend_done: bool,
        in_progress_text: str = "Võrdlen andmeid...",
        translate=None,
    ) -> str:
        combined_raw = AttentionDisplayRules._normalize_causes(main_causes, backend_causes)
        combined = [AttentionDisplayRules._translate_cause_text(c, translate=translate) for c in combined_raw]
        combined = [c for c in combined if c]
        all_done = bool(main_done and backend_done)

        if not all_done:
            if combined:
                return f"{in_progress_text}; " + "; ".join(combined)
            return in_progress_text

        return "; ".join(combined) if combined else ""
