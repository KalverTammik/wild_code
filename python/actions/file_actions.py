"""File actions behind the module file dialogs: list, download link, preview, delete and upload."""
import os
import re
from typing import List, Optional

import requests

from ..api_client import APIClient
from ..GraphQLQueryLoader import GraphQLQueryLoader
from ...Logs.python_fail_logger import PythonFailLogger
from ...utils.url_manager import Module


# requests puts the request URL in its error text ("... for url: https://...", urllib3's
# "with url: /path?..."); a signed download link carries its token there.
_URL_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s'\"<>()]+")
_URL_LABEL_RE = re.compile(r"(\burl:\s*)[^\s'\"<>()]+", re.IGNORECASE)
_QUERY_RE = re.compile(r"\?[^\s'\"<>()]+")


def _redacted(exc: Exception) -> Exception:
    """Return ``exc``, or a stand-in naming its type when its text held a URL or query string."""
    original = str(exc)
    message = _URL_RE.sub("<url>", original)
    message = _URL_LABEL_RE.sub(r"\1<url>", message)
    message = _QUERY_RE.sub("?<redacted>", message)
    if message == original:
        return exc
    # The stand-in is a RuntimeError, so the original type goes into the text.
    return RuntimeError(f"{type(exc).__name__}: {message}")


class FileActions:
    """Static file actions; APIModuleActions inherits them so callers keep one entry point."""

    @staticmethod
    def _file_owner_module(module: str) -> str:
        module_name = str(module or "").strip().lower()
        if module_name in (Module.TASK.value, Module.WORKS.value, Module.ASBUILT.value):
            return Module.TASK.value
        return module_name

    @staticmethod
    def _file_model_type(module: str) -> str:
        owner = FileActions._file_owner_module(module)
        if not owner:
            return ""
        return str(owner).upper()

    @staticmethod
    def _file_query_name(module: str) -> str:
        owner = FileActions._file_owner_module(module)
        query_map = {
            Module.TASK.value: "taskFiles.graphql",
            Module.PROJECT.value: "projectFiles.graphql",
            Module.CONTRACT.value: "contractFiles.graphql",
            Module.COORDINATION.value: "coordinationFiles.graphql",
            Module.EASEMENT.value: "easementFiles.graphql",
        }
        return query_map.get(owner, "")

    @staticmethod
    def get_module_files(module_name: str, item_id: str, *, limit: Optional[int] = None) -> Optional[List[dict]]:
        owner = FileActions._file_owner_module(module_name)
        query_name = FileActions._file_query_name(module_name)
        record_id = str(item_id or "").strip()
        if not record_id:
            return []
        if not owner or not query_name:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(owner, query_name)
        client = APIClient()

        # The file dialog promises the full list. Only cap it when a caller asks.
        max_items = max(1, int(limit)) if limit is not None else None
        after: Optional[str] = None
        seen_cursors: set[str] = set()
        files_by_uuid: dict[str, dict] = {}

        try:
            while max_items is None or len(files_by_uuid) < max_items:
                remaining = max_items - len(files_by_uuid) if max_items is not None else 50
                variables = {
                    "id": record_id,
                    "first": min(50, remaining),
                    "after": after,
                }
                if owner == Module.TASK.value:
                    variables["orderBy"] = [
                        {
                            "column": "CREATED_AT",
                            "order": "DESC",
                        }
                    ]
                data = client.send_query(query, variables=variables) or {}
                root_payload = data.get(owner) if isinstance(data, dict) else None
                connection = root_payload.get("files") if isinstance(root_payload, dict) else None
                if not isinstance(connection, dict) or not isinstance(connection.get("edges"), list):
                    raise RuntimeError("File response is missing the requested connection")
                edges = connection["edges"]
                page_info = connection.get("pageInfo") or {}
                if not edges:
                    if page_info.get("hasNextPage"):
                        raise RuntimeError("File pagination returned an empty intermediate page")
                    break

                for edge in edges:
                    node = (edge or {}).get("node") or {}
                    if not isinstance(node, dict):
                        continue

                    file_uuid = str(node.get("uuid") or "").strip()
                    file_id = str(node.get("id") or "").strip()
                    if not file_uuid and not file_id:
                        continue

                    key = file_uuid or file_id
                    uploader = node.get("uploader") if isinstance(node.get("uploader"), dict) else {}
                    model = node.get("model") if isinstance(node.get("model"), dict) else {}
                    files_by_uuid[key] = {
                        "id": file_id,
                        "uuid": file_uuid,
                        "fileName": str(node.get("fileName") or "").strip(),
                        "mimeType": str(node.get("mimeType") or "").strip(),
                        "ext": str(node.get("ext") or "").strip(),
                        "size": node.get("size"),
                        "humanReadableSize": str(node.get("humanReadableSize") or "").strip(),
                        "uploader": uploader,
                        "model": model,
                        "createdAt": node.get("createdAt"),
                        "updatedAt": node.get("updatedAt"),
                        "deletedAt": node.get("deletedAt"),
                    }
                    if max_items is not None and len(files_by_uuid) >= max_items:
                        break

                if max_items is not None and len(files_by_uuid) >= max_items:
                    break
                after = str(page_info.get("endCursor") or "").strip()
                if not page_info.get("hasNextPage"):
                    break
                if not after or after in seen_cursors:
                    raise RuntimeError("File pagination did not advance")
                seen_cursors.add(after)

            return list(files_by_uuid.values())
        except Exception as exc:
            PythonFailLogger.log_exception(
                _redacted(exc),
                module=owner or Module.TASK.value,
                event="module_get_files_failed",
                extra={"item_id": record_id, "module": str(module_name or "")},
            )
            return None

    @staticmethod
    def create_file_download_link(file_uuid: str) -> Optional[str]:
        resolved_uuid = str(file_uuid or "").strip()
        if not resolved_uuid:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "createDownloadLink.graphql")
        client = APIClient()

        try:
            data = client.send_query(query, variables={"uuid": resolved_uuid}) or {}
            payload = (data.get("createDownloadLink") or {}) if isinstance(data, dict) else {}
            url = str(payload.get("url") or "").strip()
            return url or None
        except Exception as exc:
            PythonFailLogger.log_exception(
                _redacted(exc),
                module=Module.TASK.value,
                event="task_file_download_link_failed",
                extra={"uuid": resolved_uuid},
            )
            return None

    @staticmethod
    def fetch_file_preview_payload(file_uuid: str, *, max_bytes: int) -> Optional[dict]:
        resolved_uuid = str(file_uuid or "").strip()
        preview_limit = max(1, int(max_bytes or 0))
        if not resolved_uuid:
            return None

        url = FileActions.create_file_download_link(resolved_uuid)
        if not url:
            return None

        headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as response:
                response.raise_for_status()

                content = bytearray()
                truncated = False
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue

                    remaining = preview_limit - len(content)
                    if remaining <= 0:
                        truncated = True
                        break

                    if len(chunk) > remaining:
                        content.extend(chunk[:remaining])
                        truncated = True
                        break

                    content.extend(chunk)

                content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                disposition = str(response.headers.get("Content-Disposition") or "").strip()
                content_length = str(response.headers.get("Content-Length") or "").strip()

                return {
                    "url": url,
                    "content": bytes(content),
                    "contentType": content_type,
                    "contentDisposition": disposition,
                    "contentLength": content_length,
                    "truncated": truncated,
                }
        except Exception as exc:
            PythonFailLogger.log_exception(
                _redacted(exc),
                module=Module.TASK.value,
                event="task_file_preview_fetch_failed",
                extra={"uuid": resolved_uuid, "max_bytes": preview_limit},
            )
            return None

    @staticmethod
    def delete_file(file_uuid: str) -> Optional[dict]:
        resolved_uuid = str(file_uuid or "").strip()
        if not resolved_uuid:
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "deleteFile.graphql")
        client = APIClient()

        try:
            data = client.send_query(query, variables={"uuid": resolved_uuid}) or {}
            payload = (data.get("deleteFile") or {}) if isinstance(data, dict) else {}
            return payload if isinstance(payload, dict) and str(payload.get("uuid") or "").strip() else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                _redacted(exc),
                module=Module.TASK.value,
                event="task_file_delete_failed",
                extra={"uuid": resolved_uuid},
            )
            return None

    @staticmethod
    def upload_module_file(module_name: str, item_id: str, file_path: str, *, metadata: Optional[dict] = None) -> Optional[dict]:
        owner = FileActions._file_owner_module(module_name)
        model_type = FileActions._file_model_type(module_name)
        task_id = str(item_id or "").strip()
        normalized_path = str(file_path or "").strip()
        if not owner or not model_type or not task_id or not normalized_path or not os.path.isfile(normalized_path):
            return None

        # The upload mutation is shared by every module, so only the modules that have a
        # file list may reach it; anything else is refused before a request is built.
        if not FileActions._file_query_name(module_name):
            PythonFailLogger.log_exception(
                ValueError(f"unsupported_module_for_file_upload: {owner}"),
                module=owner,
                event="module_file_upload_unsupported_module",
                extra={
                    "item_id": task_id,
                    "file_name": os.path.basename(normalized_path),
                    "module": str(module_name or ""),
                },
            )
            return None

        loader = GraphQLQueryLoader()
        query = loader.load_query_by_module(Module.TASK.value, "uploadTaskFile.graphql")
        client = APIClient()

        variables = {
            "file": None,
            "model": {
                "id": task_id,
                "type": model_type,
            },
            "data": metadata if metadata is not None else None,
        }

        try:
            data = client.send_multipart_query(
                query,
                variables=variables,
                file_variables={"file": normalized_path},
                timeout=120,
            ) or {}
            payload = (data.get("uploadFile") or {}) if isinstance(data, dict) else {}
            return payload if isinstance(payload, dict) and str(payload.get("uuid") or "").strip() else None
        except Exception as exc:
            PythonFailLogger.log_exception(
                _redacted(exc),
                module=owner,
                event="module_file_upload_failed",
                extra={
                    "item_id": task_id,
                    "file_name": os.path.basename(normalized_path),
                    "module": str(module_name or ""),
                },
            )
            return None
