"""The tags of one module as Kavitro files them: in groups, or in none. No Qt here."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(frozen=True)
class Tag:
    id: str
    name: str
    group_id: str = ""


@dataclass(frozen=True)
class TagGroup:
    id: str
    name: str


def _by_name(item) -> tuple[str, str]:
    return item.name.casefold(), item.id


@dataclass(frozen=True)
class TagCatalog:
    """Only groups that hold a tag; groups and tags are in name order, ungrouped tags come last."""

    groups: tuple[tuple[TagGroup, tuple[Tag, ...]], ...] = ()
    ungrouped: tuple[Tag, ...] = ()

    @classmethod
    def from_nodes(cls, nodes: Iterable[dict]) -> "TagCatalog":
        """From the `tags` query nodes. A node without an id or a name is left out; a repeated id counts once."""
        groups: dict[str, TagGroup] = {}
        members: dict[str, list[Tag]] = {}
        seen: set[str] = set()
        for node in nodes or []:
            tag_id = str((node or {}).get("id") or "").strip()
            name = str((node or {}).get("name") or "").strip()  # Kavitro keeps stray spaces
            if not tag_id or not name or tag_id in seen:
                continue
            seen.add(tag_id)
            group = node.get("group") or {}
            group_id = str(group.get("id") or "").strip()
            group_name = str(group.get("name") or "").strip()
            if not group_id or not group_name:
                group_id = ""
            else:
                groups.setdefault(group_id, TagGroup(group_id, group_name))
            members.setdefault(group_id, []).append(Tag(tag_id, name, group_id))
        return cls(
            groups=tuple(
                (group, tuple(sorted(members[group.id], key=_by_name)))
                for group in sorted(groups.values(), key=_by_name)
            ),
            ungrouped=tuple(sorted(members.get("", []), key=_by_name)),
        )

    def tags(self) -> Iterator[Tag]:
        """Every tag in the order it is listed."""
        for _group, tags in self.groups:
            yield from tags
        yield from self.ungrouped

    def __len__(self) -> int:
        return sum(len(tags) for _group, tags in self.groups) + len(self.ungrouped)
