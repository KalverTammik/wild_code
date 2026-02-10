#!/usr/bin/env python
"""Build a QGIS custom plugin repository artifact set.

Outputs:
- plugins.xml
- <plugin_folder>.<version>.zip (zip contains root folder)
- optional repo icon file for Plugin Manager

Designed to follow:
https://medium.com/geospatial-team/publishing-qgis-plugins-fb410b958f6

Usage (from plugin root folder):
  python tools/qgis_repo_release.py --out docs/qgis-repo --base-url https://<user>.github.io/<repo>/qgis-repo/

Then enable GitHub Pages for /docs and add repository URL in QGIS:
  https://<user>.github.io/<repo>/qgis-repo/plugins.xml
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class PluginMeta:
    folder_name: str
    name: str
    description: str
    about: str
    version: str
    qgis_minimum_version: str
    homepage: str
    author: str
    email: str
    tracker: str
    repository: str
    experimental: str
    deprecated: str
    icon_path: Optional[str]


_KEYVAL_RE = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*(?:=|:)\s*(?P<val>.*)$")


def _parse_metadata_txt(metadata_path: Path) -> Dict[str, str]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.txt not found: {metadata_path}")

    in_general = False
    meta: Dict[str, str] = {}
    for raw_line in metadata_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower() == "[general]":
            in_general = True
            continue
        if not in_general:
            continue

        match = _KEYVAL_RE.match(line)
        if not match:
            # Ignore non key/value lines (defensive for messy metadata)
            continue

        key = match.group("key")
        val = match.group("val").strip()
        meta[key] = val

    return meta


def _require(meta: Dict[str, str], key: str) -> str:
    val = meta.get(key, "").strip()
    if not val:
        raise ValueError(f"Missing required metadata key '{key}' in metadata.txt")
    return val


def _infer_github_pages_base_url(git_remote: str, repo_path: str) -> Optional[str]:
    """Infer https://<owner>.github.io/<repo>/<repo_path>/ from a git remote.

    Supports:
    - git@github.com:OWNER/REPO.git
    - https://github.com/OWNER/REPO.git
    """

    owner_repo: Optional[Tuple[str, str]] = None

    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^\s/]+?)(?:\.git)?$", git_remote.strip())
    if m:
        owner_repo = (m.group("owner"), m.group("repo"))

    if not owner_repo:
        return None

    owner, repo = owner_repo
    repo = repo.removesuffix(".git")

    base = f"https://{owner.lower()}.github.io/{repo}/"
    if repo_path:
        base = base.rstrip("/") + "/" + repo_path.strip("/") + "/"
    return base


def _get_git_remote_origin() -> str:
    # No subprocess dependency; use environment if present, otherwise best-effort.
    # If git is available, user can pass --base-url explicitly.
    try:
        import subprocess

        completed = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except Exception:
        return ""


def _should_exclude(rel_posix: str, exclude_dirs: Tuple[str, ...]) -> bool:
    parts = rel_posix.split("/")

    # Exclude hidden top-level dirs and any __pycache__
    if parts and (parts[0].startswith(".") or parts[0] == "__pycache__"):
        return True

    # Exclude explicit dir prefixes
    for d in exclude_dirs:
        d = d.strip("/")
        if not d:
            continue
        if rel_posix == d or rel_posix.startswith(d + "/"):
            return True

    # Exclude common junk
    lower = rel_posix.lower()
    if lower.endswith((".pyc", ".pyo")):
        return True
    if lower.endswith((".log",)):
        return True
    if lower.endswith((".tmp", ".swp")):
        return True

    return False


def _iter_plugin_files(plugin_root: Path, exclude_dirs: Tuple[str, ...]) -> Iterator[Path]:
    for path in plugin_root.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(plugin_root).as_posix()
        if _should_exclude(rel, exclude_dirs=exclude_dirs):
            continue
        yield path


def _build_zip(plugin_root: Path, out_zip: Path, exclude_dirs: Tuple[str, ...]) -> None:
    folder_name = plugin_root.name

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in _iter_plugin_files(plugin_root, exclude_dirs=exclude_dirs):
            rel = file_path.relative_to(plugin_root).as_posix()
            arcname = f"{folder_name}/{rel}"
            zf.write(file_path, arcname=arcname)


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def _write_plugins_xml(meta: PluginMeta, out_path: Path, download_url: str, file_name: str, icon_url: Optional[str]) -> None:
    plugins = ET.Element("plugins")

    plugin_el = ET.SubElement(
        plugins,
        "pyqgis_plugin",
        {
            "name": meta.name,
            "version": meta.version,
        },
    )

    def add(tag: str, text: str) -> None:
        el = ET.SubElement(plugin_el, tag)
        el.text = text

    add("description", meta.description)
    add("about", meta.about)
    add("version", meta.version)
    add("qgis_minimum_version", meta.qgis_minimum_version)
    if meta.homepage:
        add("homepage", meta.homepage)
    add("file_name", file_name)
    add("download_url", download_url)
    if icon_url:
        add("icon", icon_url)
    if meta.author:
        add("author_name", meta.author)
    if meta.email:
        add("email", meta.email)
    if meta.tracker:
        add("tracker", meta.tracker)
    if meta.repository:
        add("repository", meta.repository)

    # Ensure these exist even if metadata omitted
    add("experimental", meta.experimental or "False")
    add("deprecated", meta.deprecated or "False")

    # Optional build timestamp for humans
    add("create_date", _dt.datetime.utcnow().strftime("%Y-%m-%d"))

    _indent_xml(plugins)
    tree = ET.ElementTree(plugins)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)


def _read_plugin_meta(plugin_root: Path) -> PluginMeta:
    metadata_path = plugin_root / "metadata.txt"
    meta = _parse_metadata_txt(metadata_path)

    # Required by Medium post (for plugin operation / PM metadata)
    name = _require(meta, "name")
    version = _require(meta, "version")
    qgis_min = _require(meta, "qgisMinimumVersion")

    # Recommended
    description = meta.get("description", "").strip() or name
    about = meta.get("about", "").strip() or description
    homepage = meta.get("homepage", "").strip()
    author = meta.get("author", "").strip()
    email = meta.get("email", "").strip()
    tracker = meta.get("tracker", "").strip()
    repository = meta.get("repository", "").strip()
    experimental = meta.get("experimental", "False").strip()
    deprecated = meta.get("deprecated", "False").strip()
    icon_path = meta.get("icon", "").strip() or None

    return PluginMeta(
        folder_name=plugin_root.name,
        name=name,
        description=description,
        about=about,
        version=version,
        qgis_minimum_version=qgis_min,
        homepage=homepage,
        author=author,
        email=email,
        tracker=tracker,
        repository=repository,
        experimental=experimental,
        deprecated=deprecated,
        icon_path=icon_path,
    )


def _copy_repo_icon(plugin_root: Path, meta: PluginMeta, out_dir: Path, repo_icon_name: str) -> Optional[Path]:
    if not meta.icon_path:
        return None

    src = (plugin_root / meta.icon_path).resolve()
    if not src.exists() or not src.is_file():
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / repo_icon_name
    dst.write_bytes(src.read_bytes())
    return dst


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build QGIS custom plugin repository artifacts (plugins.xml + zip).")
    parser.add_argument("--plugin-dir", default=".", help="Path to plugin root folder (contains metadata.txt)")
    parser.add_argument("--out", default="docs/qgis-repo", help="Output directory for plugins.xml and zip")
    parser.add_argument(
        "--base-url",
        default="",
        help="Base URL where the output directory is hosted (must end with '/'). Example: https://user.github.io/repo/qgis-repo/",
    )
    parser.add_argument(
        "--repo-path",
        default="qgis-repo",
        help="Used only when --base-url is not provided and origin remote is GitHub; appended to inferred Pages base.",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory prefix (relative to plugin root) to exclude from zip. Can be repeated.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    plugin_root = Path(args.plugin_dir).resolve()
    out_dir = Path(args.out).resolve()

    meta = _read_plugin_meta(plugin_root)

    # Default exclusions: keep runtime code/resources, drop dev/runtime noise.
    exclude_dirs: Tuple[str, ...] = tuple(
        [
            "docs",
            "reports",
            "tools",
            "__pycache__",
            "Logs/CrashLogs",
            "Logs/PythonLogs",
            "Logs/SwitchLogs",
            "vs-code-bpmn-io",
        ]
        + list(args.exclude_dir)
    )

    zip_name = f"{meta.folder_name}.{meta.version}.zip"
    zip_path = out_dir / zip_name

    # Determine base url
    base_url = args.base_url.strip()
    if base_url and not base_url.endswith("/"):
        base_url += "/"

    if not base_url:
        origin = _get_git_remote_origin()
        inferred = _infer_github_pages_base_url(origin, repo_path=args.repo_path)
        base_url = inferred or ""

    if not base_url:
        print("ERROR: Could not infer base URL. Provide --base-url explicitly.", file=sys.stderr)
        return 2

    download_url = base_url + zip_name

    # Copy a repo icon file for Plugin Manager (optional)
    repo_icon_name = f"{meta.folder_name}.png"
    icon_dst = _copy_repo_icon(plugin_root, meta, out_dir, repo_icon_name=repo_icon_name)
    icon_url = (base_url + repo_icon_name) if icon_dst else None

    _build_zip(plugin_root, zip_path, exclude_dirs=exclude_dirs)

    plugins_xml_path = out_dir / "plugins.xml"
    _write_plugins_xml(
        meta=meta,
        out_path=plugins_xml_path,
        download_url=download_url,
        file_name=zip_name,
        icon_url=icon_url,
    )

    print("Built:")
    print(f"- {plugins_xml_path}")
    print(f"- {zip_path}")
    if icon_dst:
        print(f"- {icon_dst}")

    print("\nRepository URL to add in QGIS Plugin Manager:")
    print(base_url + "plugins.xml")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
