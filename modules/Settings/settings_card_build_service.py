import time


class SettingsCardBuildService:
    @staticmethod
    def insert_cards_batch(*, pending_names, cards_container, cards_layout, module_cards, create_card):
        created_cards = []
        try:
            cards_container.setUpdatesEnabled(False)
        except Exception:
            pass

        try:
            for module_name in pending_names:
                card = create_card(module_name)
                module_cards[module_name] = card
                insert_at = max(0, cards_layout.count() - 1)
                cards_layout.insertWidget(insert_at, card)
                created_cards.append(card)
        finally:
            try:
                cards_container.setUpdatesEnabled(True)
                cards_container.update()
            except Exception:
                pass

        return created_cards

    @staticmethod
    def activate_cards_with_profile(*, created_cards, activate_card, profile_log):
        batch_started = time.monotonic()

        for card in created_cards:
            started = time.monotonic()
            activate_card(card)
            elapsed_ms = int((time.monotonic() - started) * 1000)
            profile_log(
                "settings_card_activate_profile",
                {
                    "card": getattr(card, "module_key", type(card).__name__),
                    "elapsed_ms": elapsed_ms,
                },
            )

        if created_cards:
            total_ms = int((time.monotonic() - batch_started) * 1000)
            profile_log(
                "settings_card_batch_activate_profile",
                {
                    "count": len(created_cards),
                    "elapsed_ms": total_ms,
                },
            )

    @staticmethod
    def build_missing_cards(*, allowed_modules, module_cards, cards_container, cards_layout, create_card, activate_card, profile_log):
        pending_names = [
            name
            for name in (allowed_modules or [])
            if name and name not in module_cards
        ]

        if not pending_names:
            return []

        created_cards = SettingsCardBuildService.insert_cards_batch(
            pending_names=pending_names,
            cards_container=cards_container,
            cards_layout=cards_layout,
            module_cards=module_cards,
            create_card=create_card,
        )

        SettingsCardBuildService.activate_cards_with_profile(
            created_cards=created_cards,
            activate_card=activate_card,
            profile_log=profile_log,
        )

        return created_cards

    @staticmethod
    def dispose_card(*, card, cards_layout, on_pending_changed, log_error):
        if not card:
            return
        try:
            card.on_settings_deactivate()
        except Exception as exc:
            log_error(exc, "settings_card_deactivate_failed")
        try:
            card.pendingChanged.disconnect(on_pending_changed)
        except Exception as exc:
            log_error(exc, "settings_card_disconnect_failed")
        try:
            cards_layout.removeWidget(card)
        except Exception as exc:
            log_error(exc, "settings_card_remove_failed")
        try:
            card.setParent(None)
            card.deleteLater()
        except Exception as exc:
            log_error(exc, "settings_card_delete_failed")
