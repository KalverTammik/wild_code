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
            TranslationKeys.PROPERTY_ADD_BACKEND_DIFFERS: TranslationKeys.PROPERTY_ADD_BACKEND_DIFFERS,
            TranslationKeys.PROPERTY_ADD_AMBIGUOUS: TranslationKeys.PROPERTY_ADD_AMBIGUOUS,
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
    def causes_text(causes: Sequence[object] | None, translate=None) -> str:
        """Translated reasons of one column, for that column's tooltip."""
        parts = [AttentionDisplayRules._translate_cause_text(cause, translate=translate)
                 for cause in AttentionDisplayRules._normalize_causes(causes)]
        return "; ".join(part for part in parts if part)

