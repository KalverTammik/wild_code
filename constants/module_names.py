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
