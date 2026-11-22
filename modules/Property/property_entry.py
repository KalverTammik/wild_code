"""Public interface of the Property module for other modules.

Other modules (today only Settings' property management card) import Property
features from here and nowhere else, so the Property internals can move without
touching them. Keep this file thin: it only forwards to the defining modules and
must never import other modules (modules/Settings etc.), or an import cycle appears.
"""
from .dialogs.AddUpdatePropertyDialog import AddPropertyDialog
from .FlowControllers.property_dialog_phase import PropertyDialogMode
from .FlowControllers.property_add_flow import MainAddPropertiesFlow
from .dialogs.delete_property_dialog import DeletePropertyUI
from .FlowControllers.property_remove_flow import PropertySelectionActionService
from .FlowControllers.property_shp_import_flow import SHPLayerLoader, SHPLoadResult, SHPLoadStatus

__all__ = [
    "PropertyDialogMode",
    "SHPLoadStatus",
    "load_property_layer_from_shp",
    "open_add_property_dialog",
    "open_remove_by_id_dialog",
    "start_remove_selected_flow",
]


def open_add_property_dialog(parent, mode) -> bool:
    """Open the add-property dialog in `mode` (a PropertyDialogMode value).

    Returns False when the archive layer preflight stops the flow before the dialog.
    """
    if not MainAddPropertiesFlow.preflight_archive_layer_before_dialog():
        return False
    AddPropertyDialog(parent, mode=mode)
    return True


def open_remove_by_id_dialog(parent):
    """Open the emergency delete-by-cadastral-id dialog."""
    return DeletePropertyUI(parent)


def start_remove_selected_flow(**kwargs):
    """Start the map-selection archive/unarchive/delete flow.

    Takes the keyword arguments of PropertySelectionActionService.start_settings_remove_flow
    and returns its selection controller, or None when selection could not start.
    """
    return PropertySelectionActionService.start_settings_remove_flow(**kwargs)


def load_property_layer_from_shp(parent) -> SHPLoadResult:
    """Ask for a Shapefile and load it as the property import layer.

    Shows the file pickers, the bootstrap questions, the progress window and the success
    message itself. Returns the result; on FAILED the caller shows error_title/error_message.
    """
    return SHPLayerLoader(parent).load_shp_layer()
