from enum import Enum


class Module(Enum):
    PROJECT = "project"
    CONTRACT = "contract"
    COORDINATION = "coordination"
    LETTER = "letter"
    SPECIFICATION = "specification"
    EASEMENT = "easement"
    SUBMISSION = "submission"

    ASBUILT = "asbuilt"
    WORKS = "works"
    TASK = "task"

    USER = "user"

    PROPERTY = "property"
    SETTINGS = "settings"
    HOME = "home"

    STATUSES = "statuses"
    TYPES = "type"


class ModuleSupports(Enum):
    TAGS = "tags"
    STATUSES = "statuses"
    TYPES = "type"


# The plugin splits Kavitro tasks into sections (works, as-built, ...). Every section is the same Kavitro entity,
# so it is listed, read and saved as a task. A new section is added here and nowhere else.
TASK_SECTIONS = (Module.TASK, Module.WORKS, Module.ASBUILT)
TASK_SECTION_VALUES = frozenset(section.value for section in TASK_SECTIONS)


def backend_module(module) -> str:
    """The Kavitro entity behind a plugin module: a task section gives "task", any other module itself."""
    name = str(module or "").strip().lower()
    return Module.TASK.value if name in TASK_SECTION_VALUES else name
