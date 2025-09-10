# Layer Creation Engines and Mailabl Group Layers

## Introduction

The Mailabl QGIS plugin uses a robust layer management system to handle temporary and persistent geospatial data. This system revolves around QGIS's layer tree, where layers are organized into groups for better project organization. Key features include:

- **Dynamic Group Creation**: Groups are created on-demand using predefined names.
- **Memory Layers**: Temporary layers for staging data without immediate disk writes.
- **Persistence Options**: Export to GeoPackage (.gpkg) with styles, spatial indexes, and reloading capabilities.
- **Integration with Workflows**: Supports property syncing, importing, archiving, and UI responsiveness.

This guide explains the architecture, key classes, and methods, with examples for v2 development.

## Loading SHP Files from Maa-Amet

The plugin supports importing Shapefile (.shp) data from the Estonian Land Board (Maa-amet) as the main base layer for cadastral data. This process ensures the plugin has a valid base map for property-related operations.

### Process Overview
1. **User Initiation**: User clicks the "Load Shapefile" button in the main dialog.
2. **File Selection**: A file dialog opens, filtered to `.shp` files, allowing selection of the maa-amet Shapefile.
3. **Import as Memory Layer**: The selected file is imported into a memory layer to avoid locking the original file and enable fast operations.
4. **Group Organization**: The layer is added to the "Imporditavad kinnistud" (Imported Properties) group in the QGIS layer tree.
5. **Settings Persistence**: The layer name is saved in QGIS settings for future sessions.
6. **UI Update**: The dialog updates to show the loaded layer and enables property-related workflows.

### Key Classes and Methods

#### `SHPLayerLoader` Class (`processes/ImportProcesses/Import_shp_file.py`)
Handles the UI interaction and orchestration of the import process.

- **`load_shp_layer()`**:
  - Opens a `QFileDialog` with filter for `*.shp` files.
  - Extracts the layer name from the file path.
  - Ensures the "Imporditavad kinnistud" group exists or creates it.
  - Removes any existing layer with the same name from the group.
  - Calls `ShapefileImporter.import_shp_file_as_memory_layer()` to perform the import.
  - Shows a confirmation dialog with import details.
  - Saves the layer name to QGIS settings using `QgsSettings` with key `wild_code/target_cadastral_layer`.
  - Updates the UI to hide import controls and show property flow options.

#### `ShapefileImporter` Class (`processes/ImportProcesses/Import_shp_file.py`)
Performs the actual import into a memory layer.

- **`import_shp_file_as_memory_layer(file_path, group_layer, progress=None)`**:
  - Loads the Shapefile using `QgsVectorLayer(file_path, "shapefile_import", "ogr")`.
  - Validates the layer and extracts geometry type and CRS.
  - Creates a new memory layer with matching schema: `QgsVectorLayer(f"{geometry_type}?crs={crs.authid()}", shp_layer_name, "memory")`.
  - Uses `ProgressDialogModern` to show import progress and prevent UI freezing.
  - Copies features in batches (every 1000 features) to the memory layer, updating progress at quarters.
  - Commits changes, updates extents, and creates a spatial index.
  - Applies a predefined style from `Filepaths.get_style(FilesByNames().MaaAmet_import)`.
  - Adds the memory layer to the QGIS project and inserts it into the specified group.
  - Closes progress dialog and cleans up resources with `gc.collect()`.

#### Settings Persistence (Central QGIS Settings)
- **Target Cadastral Layer**: Saved to QGIS settings using `QgsSettings` with key `wild_code/target_cadastral_layer`.
- **Retrieval**: Layer name is retrieved using the central settings system in `RemapPropertiesLayer._get_target_cadastral_name()`.
- **Benefits**: Uses QGIS's native settings system for better integration and persistence across sessions.

### Usage Example
```python
# In the main dialog, when load button is clicked
loader = SHPLayerLoader(self)
loader.load_shp_layer()
# Result: User selects maa-amet .shp file, it's imported as memory layer in "Imporditavad kinnistud" group, name saved to settings.
```

### v2 Guidance
- **Validation**: Add checks for maa-amet specific field structures (e.g., using `Maa_amet_fields.py`).
- **Error Handling**: Handle invalid Shapefiles or CRS mismatches with user-friendly messages.
- **Performance**: For very large files, consider background processing or chunked loading.
- **Extensibility**: Support other formats (e.g., GeoPackage) or direct downloads from maa-amet API.
- **UI Improvements**: Show preview of layer attributes before import.

## Architecture Overview

### Core Concepts
- **QGIS Layer Tree**: The plugin interacts with `QgsProject.instance().layerTreeRoot()` to add/remove groups and layers.
- **Groups**: Defined in `MailablGroupFolders` (e.g., "Uued kinnistud" for new properties).
- **Memory Layers**: Created with `'memory'` provider for fast, temporary data handling.
- **Persistence**: Uses `QgsVectorFileWriter` to save to GeoPackage, then reloads into the project.

### Key Classes and Files
- **`layer_generator.py`**: Main file with `LayerCopier` and `LayerManager` classes.
- **`FolderHelper.py`**: Defines group names via `MailablGroupFolders`.
- **Dependencies**: Relies on QGIS core classes like `QgsVectorLayer`, `QgsLayerTreeGroup`, and utilities for styles/CRS.

## Key Classes and Methods

### 1. `LayerCopier` Class
Handles creating and saving memory layers.

#### `copy_virtual_layer_for_properties(new_layer_name, group_name)`
- **Purpose**: Creates a memory layer based on an existing layer (e.g., import layer), copies its fields/CRS, and adds it to a specified group.
- **Parameters**:
  - `new_layer_name`: Name for the new memory layer.
  - `group_name`: Target group (e.g., `MailablGroupFolders.NEW_PROPERTIES`).
- **Process**:
  - Removes any existing memory layer with the same name.
  - Creates a new `QgsVectorLayer` with `'memory'` provider.
  - Copies attributes, extent, and CRS from the base layer.
  - Loads a style from configured files.
  - Adds the layer to the project and inserts it into the group.
- **Usage Example**:
  ```python
  from Functions.layer_generator import LayerCopier
  memory_name = LayerCopier.copy_virtual_layer_for_properties("MyNewLayer", "Uued kinnistud")
  # Result: Memory layer added to "Uued kinnistud" group.
  ```
- **v2 Guidance**: Extend to support custom styles or multiple base layers. Ensure group exists before adding.

#### `StartSaving_virtual_Layer(memory_layer_name, new_layer_name, group_layer_name)`
- **Purpose**: Saves a memory layer to a user-selected GeoPackage file and reloads it into the project.
- **Parameters**:
  - `memory_layer_name`: Name of the memory layer to save.
  - `new_layer_name`: Name for the saved layer.
  - `group_layer_name`: Group to add the reloaded layer to.
- **Process**:
  - Prompts user for a save folder.
  - Writes the layer to `.gpkg` using `QgsVectorFileWriter.writeAsVectorFormat`.
  - Handles file conflicts (deletes existing if needed).
  - Reloads the `.gpkg` as a new layer, applies style, builds spatial index.
  - Adds to the project and specified group; removes the memory layer.
- **Usage Example**:
  ```python
  LayerCopier.StartSaving_virtual_Layer("MyMemoryLayer", "MySavedLayer", "Uued kinnistud")
  # Result: User selects folder, .gpkg saved, layer reloaded in group.
  ```
- **v2 Guidance**: Add options for different formats (e.g., Shapefile). Improve error handling for write failures.

### 2. `LayerManager` Class
Provides utilities for layer and group management.

#### `get_or_create_group(group_name)`
- **Purpose**: Retrieves or creates a group in the layer tree.
- **Parameters**: `group_name` (str).
- **Process**: Checks `root.findGroup()`, creates with `root.addGroup()` if missing.
- **Usage Example**:
  ```python
  from Functions.layer_generator import LayerManager
  group = LayerManager.get_or_create_group("MyGroup")
  # Result: Group exists or is created.
  ```
- **v2 Guidance**: Add support for nested subgroups.

#### `_create_memory_layer_by_coping_original_layer(new_layer_name, base_layer, is_archive)`
- **Purpose**: Creates a memory layer by copying an existing layer's schema.
- **Parameters**:
  - `new_layer_name`: Name for the new layer.
  - `base_layer`: Source `QgsVectorLayer`.
  - `is_archive`: If True, adds a "backup_date" field.
- **Process**: Mirrors fields, sets CRS/extent, registers with layer setups.
- **Usage Example**:
  ```python
  memory_layer = LayerManager._create_memory_layer_by_coping_original_layer("CopyLayer", base_layer, False)
  ```
- **v2 Guidance**: Integrate with `LayerCopier` for consistency.

#### `_add_layer_to_sandbox_group(layer, group)`
- **Purpose**: Adds a layer to a group (defaults to sandbox if none provided).
- **Parameters**: `layer` (QgsVectorLayer), `group` (str or QgsLayerTreeGroup).
- **Process**: Adds to project, inserts into group.
- **Usage Example**:
  ```python
  LayerManager._add_layer_to_sandbox_group(memory_layer, "Ajutised kihid")
  ```
- **v2 Guidance**: Make group parameter mandatory for clarity.

### 3. `MailablGroupFolders` Class
Defines standard group names.

- **Constants**:
  - `MAILABL_MAIN`: "Mailabl settings"
  - `NEW_PROPERTIES`: "Uued kinnistud"
  - `SANDBOXING`: "Ajutised kihid"
  - `ARCHIVE`: "Arhiiv"
  - Etc.
- **Usage**: Pass these to methods like `LayerCopier.copy_virtual_layer_for_properties`.
- **v2 Guidance**: Make extensible (e.g., allow custom groups via config).

## Workflow Examples

### Creating a New Properties Layer
1. Call `LayerCopier.copy_virtual_layer_for_properties("SyncLayer", MailablGroupFolders.NEW_PROPERTIES)`.
2. Populate with data (e.g., from GraphQL).
3. Optionally save: `LayerCopier.StartSaving_virtual_Layer("SyncLayer-memory", "SavedSync", MailablGroupFolders.NEW_PROPERTIES)`.

### Archiving a Layer
1. Use `LayerManager._create_memory_layer_by_coping_original_layer` with `is_archive=True`.
2. Append features via `ArchiveOptionBuilder.append_archive_items_to_layer`.
3. Save and reload into archive group.

## Best Practices for v2
- **Error Handling**: Add try-except for QGIS operations (e.g., layer creation failures).
- **Performance**: Use memory layers for large datasets; batch operations.
- **UI Integration**: Tie to progress dialogs (e.g., `ProgressDialogModern`) to avoid freezes.
- **Extensibility**: Support custom CRS/styles; add logging via `TracebackLogger`.
- **Testing**: Mock `QgsProject` for unit tests.
- **Dependencies**: Ensure QGIS core imports are handled gracefully.

This system provides a solid foundation for layer management—build on it by adding more automation and user options.
