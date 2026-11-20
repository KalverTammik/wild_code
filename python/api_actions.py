"""The one entry point for the module actions; callers import APIModuleActions from here.

Every domain lives in python/actions/ as a class of static methods, and APIModuleActions
inherits them all, so this module holds no action code of its own.
"""
from .actions.file_actions import FileActions
from .actions.geometry_actions import GeometryActions
from .actions.property_link_actions import PropertyLinkActions
from .actions.status_actions import StatusActions
from .actions.task_actions import TaskActions
from .actions.user_actions import UserActions


class APIModuleActions(FileActions, PropertyLinkActions, StatusActions, UserActions, TaskActions, GeometryActions):
    """Entry point for the module actions; the file, property-link, status, user, task and geometry domains live in python/actions/."""
