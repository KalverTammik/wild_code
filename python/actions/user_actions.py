"""User actions: the logged-in user and the users a task can be assigned to."""
from typing import Optional

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.SessionManager import SessionManager
from ...constants.module_names import Module


class UserActions:
    """Static user actions; APIModuleActions inherits them so callers keep one entry point."""

    @staticmethod
    def get_current_user_payload() -> Optional[dict]:
        session = SessionManager()
        cached_user = session.loggedInUser
        if isinstance(cached_user, dict) and str(cached_user.get("id") or "").strip():
            return cached_user

        loader = GraphQLQueryLoader()
        client = APIClient()

        try:
            query = loader.load_query_by_module(Module.USER.value, "me.graphql")
            data = client.send_query(query) or {}
            user = (data.get("me") or {}) if isinstance(data, dict) else {}
            if isinstance(user, dict) and str(user.get("id") or "").strip():
                try:
                    session.loggedInUser = user
                    SessionManager.save_session()
                except Exception as cache_exc:
                    PythonFailLogger.log_exception(
                        cache_exc,
                        module=Module.USER.value,
                        event="current_user_cache_failed",
                    )
                return user
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.USER.value,
                event="current_user_fetch_failed",
            )

        return cached_user if isinstance(cached_user, dict) else None

    @staticmethod
    def get_current_user_id() -> str:
        user = UserActions.get_current_user_payload() or {}
        return str(user.get("id") or "").strip() if isinstance(user, dict) else ""

    @staticmethod
    def user_display_name(user: Optional[dict]) -> str:
        if not isinstance(user, dict):
            return ""

        display_name = str(user.get("displayName") or "").strip()
        if display_name:
            return display_name

        first_name = str(user.get("firstName") or "").strip()
        last_name = str(user.get("lastName") or "").strip()
        full_name = " ".join(part for part in (first_name, last_name) if part).strip()
        if full_name:
            return full_name

        email = str(user.get("email") or "").strip()
        if email:
            return email

        return str(user.get("id") or "").strip()

    @staticmethod
    def get_assignable_users(limit: int = 100) -> list[dict[str, str]]:
        max_items = max(1, int(limit or 0))
        current_user = UserActions.get_current_user_payload() or {}
        current_user_id = str(current_user.get("id") or "").strip()

        users_by_id: dict[str, dict[str, str]] = {}
        current_user_name = UserActions.user_display_name(current_user)
        if current_user_id and current_user_name:
            users_by_id[current_user_id] = {
                "id": current_user_id,
                "displayName": current_user_name,
            }

        loader = GraphQLQueryLoader()
        client = APIClient()

        try:
            query = loader.load_query_by_module(Module.USER.value, "users.graphql")
            after: Optional[str] = None

            while len(users_by_id) < max_items:
                remaining = max_items - len(users_by_id)
                variables = {
                    "first": min(50, remaining),
                    "after": after,
                }
                data = client.send_query(query, variables=variables) or {}
                users_connection = (data.get("users") or {}) if isinstance(data, dict) else {}
                edges = users_connection.get("edges") or []
                if not isinstance(edges, list) or not edges:
                    break

                for edge in edges:
                    node = (edge or {}).get("node") or {}
                    if not isinstance(node, dict):
                        continue

                    user_id = str(node.get("id") or "").strip()
                    if not user_id:
                        continue

                    if str(node.get("deletedAt") or "").strip():
                        continue

                    display_name = UserActions.user_display_name(node)
                    if not display_name:
                        continue

                    users_by_id[user_id] = {
                        "id": user_id,
                        "displayName": display_name,
                    }
                    if len(users_by_id) >= max_items:
                        break

                page_info = users_connection.get("pageInfo") or {}
                after = str(page_info.get("endCursor") or "").strip()
                if not page_info.get("hasNextPage") or not after:
                    break
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.USER.value,
                event="assignable_users_fetch_failed",
                extra={"limit": max_items},
            )

        users = list(users_by_id.values())
        users.sort(
            key=lambda item: (
                str(item.get("id") or "").strip() != current_user_id,
                str(item.get("displayName") or "").casefold(),
            )
        )
        return users
