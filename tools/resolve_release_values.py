from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Mapping, Tuple


VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z]+)*$"
)
TAG_PATTERN = re.compile(
    r"^[vV]?[0-9]+\.[0-9]+\.[0-9]+(?:[.-][0-9A-Za-z]+)*$"
)


class ReleaseValueError(ValueError):
    """Raised when release event data is missing or outside the safe format."""


def normalize_release_version(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if value.startswith("."):
        value = value[1:]
    if value.startswith(("v", "V")):
        value = value[1:]

    if re.fullmatch(r"[0-9]+", value):
        value = f"{value}.0.0"
    elif re.fullmatch(r"[0-9]+\.[0-9]+", value):
        value = f"{value}.0"

    if not VERSION_PATTERN.fullmatch(value):
        raise ReleaseValueError(
            "release version must use x.y.z with an optional alphanumeric prerelease suffix"
        )
    return value


def validate_release_tag(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    if not TAG_PATTERN.fullmatch(value):
        raise ReleaseValueError(
            "release tag must use vX.Y.Z or X.Y.Z with an optional alphanumeric prerelease suffix"
        )
    return value


def resolve_release_values(environment: Mapping[str, str]) -> Tuple[str, str]:
    event_name = str(environment.get("GITHUB_EVENT_NAME", "") or "").strip()

    if event_name == "release":
        release_tag = validate_release_tag(
            environment.get("PLUGIN_RELEASE_EVENT_TAG", "")
        )
        release_version = normalize_release_version(release_tag)
    elif event_name == "workflow_dispatch":
        release_version = normalize_release_version(
            environment.get("PLUGIN_INPUT_RELEASE_VERSION", "")
        )
        requested_tag = str(
            environment.get("PLUGIN_INPUT_RELEASE_TAG", "") or ""
        ).strip()
        release_tag = validate_release_tag(requested_tag or f"v{release_version}")
    else:
        raise ReleaseValueError("unsupported release event")

    return release_version, release_tag


def write_github_outputs(output_path: str, release_version: str, release_tag: str) -> None:
    if not output_path:
        raise ReleaseValueError("GITHUB_OUTPUT is unavailable")

    # Both values have already passed single-line allowlists. Write them without
    # shell interpolation so workflow-command syntax cannot be injected.
    with Path(output_path).open("a", encoding="utf-8", newline="\n") as output:
        output.write(f"release_version={release_version}\n")
        output.write(f"release_tag={release_tag}\n")


def main() -> int:
    try:
        release_version, release_tag = resolve_release_values(os.environ)
        write_github_outputs(
            os.environ.get("GITHUB_OUTPUT", ""),
            release_version,
            release_tag,
        )
    except (OSError, ReleaseValueError) as exc:
        # Validation errors deliberately omit the rejected raw value.
        print(f"Release value validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Resolved release version {release_version} with tag {release_tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
