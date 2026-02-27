from functools import partial

from ...constants.file_paths import ConfigPaths
from ...python.api_client import APIClient
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.workers import FunctionWorker, start_worker
from ...utils.SessionManager import SessionManager
from ...utils.auth.user_utils import UserUtils


class SettingsUserFetchService:
    @staticmethod
    def start_user_fetch(*, active_token, on_success, on_error, on_finished):
        query_loader = GraphQLQueryLoader()
        api_client = APIClient(SessionManager(), ConfigPaths.CONFIG)
        fetcher = partial(UserUtils.fetch_user_payload, query_loader, api_client)

        worker = FunctionWorker(fetcher)
        worker.active_token = active_token
        worker.finished.connect(on_success)
        worker.error.connect(on_error)

        thread = start_worker(worker, on_thread_finished=on_finished)
        return worker, thread

    @staticmethod
    def cancel_user_fetch(*, worker, thread, on_success, on_error, log_error):
        if worker is not None:
            try:
                worker.finished.disconnect(on_success)
            except Exception as exc:
                log_error(exc, "settings_disconnect_finished_failed")
            try:
                worker.error.disconnect(on_error)
            except Exception as exc:
                log_error(exc, "settings_disconnect_error_failed")

        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(200)
