from __future__ import annotations

from typing import Iterable, List, Sequence


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
    def build_attention_text(
        main_causes: Sequence[object] | None,
        backend_causes: Sequence[object] | None,
        *,
        main_done: bool,
        backend_done: bool,
        in_progress_text: str = "Võrdlen andmeid...",
    ) -> str:
        combined = AttentionDisplayRules._normalize_causes(main_causes, backend_causes)
        all_done = bool(main_done and backend_done)

        if not all_done:
            if combined:
                return f"{in_progress_text}; " + "; ".join(combined)
            return in_progress_text

        return "; ".join(combined) if combined else ""
