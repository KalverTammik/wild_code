# Layer Creation Engine Documentation

## Overview

The Layer Creation Engine is a comprehensive service for managing geospatial layers in the Mailabl QGIS plugin. It provides functionality for creating memory layers, managing layer groups, and persisting layers to GeoPackage format.

## Architecture

### Core Components

1. **LayerCreationEngine** - Main engine class with all layer operations
2. **MailablGroupFolders** - Standard group name constants
3. **LayerCreationTestWidget** - GUI for testing layer operations
4. **Demo Script** - Examples of how to use the engine

### File Structure

```
engines/
├── LayerCreationEngine.py          # Main engine implementation

widgets/
├── LayerCreationTestWidget.py      # Test GUI widget

demo_layer_engine.py                # Usage examples
```

## Quick Start

### Basic Usage

```python
from engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders

# Get engine instance
engine = get_layer_engine()

# Create a memory layer
layer = engine.create_memory_layer_from_template("MyLayer", None, None, None, "Point")
if layer:
    # Add to group
    group = engine.get_or_create_group(MailablGroupFolders.SANDBOXING)
    group.addLayer(layer)
```

### Using the Test Widget

```python
from widgets.LayerCreationTestWidget import create_layer_test_widget

# Create and show test widget
widget = create_layer_test_widget()
widget.show()
```

## API Reference

### LayerCreationEngine Class

#### Core Methods

- `get_or_create_group(group_name)` - Get or create layer group
- `create_memory_layer_from_template(name, template, fields, crs, geometry_type)` - Create memory layer
- `copy_virtual_layer_for_properties(name, group, template)` - Copy virtual layer
- `save_memory_layer_to_geopackage(memory_name, new_name, group, directory)` - Save to GeoPackage

#### Convenience Methods

- `create_property_sync_layer()` - Create layer for property sync
- `create_archive_layer()` - Create layer for archiving
- `create_import_layer()` - Create layer for importing

#### Information Methods

- `get_available_groups()` - List all layer groups
- `get_layers_in_group(group_name)` - List layers in specific group

### MailablGroupFolders Constants

- `MAILABL_MAIN` - "Mailabl settings"
- `NEW_PROPERTIES` - "Uued kinnistud"
- `SANDBOXING` - "Ajutised kihid"
- `ARCHIVE` - "Arhiiv"
- `IMPORT` - "Import"
- `EXPORT` - "Eksport"
- `SYNC` - "Sünkroonimine"

## Usage Examples

### Example 1: Basic Memory Layer Creation

```python
from engines.LayerCreationEngine import get_layer_engine, MailablGroupFolders

engine = get_layer_engine()

# Create memory layer
layer = engine.create_memory_layer_from_template(
    "TestLayer",
    None,  # No template
    None,  # No custom fields
    None,  # Default CRS
    "Point"  # Geometry type
)

if layer:
    # Add to sandbox group
    group = engine.get_or_create_group(MailablGroupFolders.SANDBOXING)
    group.addLayer(layer)
    print("Layer created successfully!")
```

### Example 2: Virtual Layer Copying

```python
# Copy existing layer for property operations
result = engine.copy_virtual_layer_for_properties(
    "PropertyCopy",
    MailablGroupFolders.NEW_PROPERTIES,
    existing_layer  # Optional template layer
)

if result:
    print(f"Virtual layer '{result}' created")
```

### Example 3: Saving to GeoPackage

```python
# Save memory layer to file
success = engine.save_memory_layer_to_geopackage(
    "MyMemoryLayer",
    "MySavedLayer",
    MailablGroupFolders.ARCHIVE
)

if success:
    print("Layer saved to GeoPackage!")
```

## Integration with QGIS Plugin

### Adding to Main Dialog

```python
# In your main dialog class
from widgets.LayerCreationTestWidget import create_layer_test_widget

def show_layer_test_widget(self):
    """Show the layer creation test widget."""
    widget = create_layer_test_widget(self)
    widget.show()
```

### Using in Module Managers

```python
# In module management code
from engines.LayerCreationEngine import get_layer_engine

class PropertyModule:
    def __init__(self):
        self.engine = get_layer_engine()

    def create_working_layer(self):
        """Create working layer for property operations."""
        return self.engine.create_property_sync_layer()
```

## Testing

### Running the Demo

```python
# Run in QGIS Python console
exec(open('demo_layer_engine.py').read())
```

### Using the Test Widget

1. Import the test widget
2. Create and show it
3. Use the GUI buttons to test different operations
4. Check the QGIS layer tree for results

## Best Practices

### Error Handling

```python
try:
    layer = engine.create_memory_layer_from_template("Test", None, None, None, "Point")
    if layer:
        # Success - add to group
        group = engine.get_or_create_group("TestGroup")
        group.addLayer(layer)
    else:
        print("Failed to create layer")
except Exception as e:
    print(f"Error: {e}")
```

### Resource Management

```python
# Engine is singleton - get once, use everywhere
engine = get_layer_engine()

# Reuse groups
group = engine.get_or_create_group("MyGroup")

# Clean up memory layers when done
project = QgsProject.instance()
for layer in project.mapLayers().values():
    if layer.providerType() == 'memory' and layer.name().startswith('temp_'):
        project.removeMapLayer(layer.id())
```

### Naming Conventions

- Use descriptive layer names
- Include operation type in names (e.g., "Sync_PropertyLayer")
- Use consistent group names from MailablGroupFolders

## Troubleshooting

### Common Issues

1. **Layer not visible**: Check if added to correct group
2. **Memory layer lost**: Memory layers don't persist between sessions
3. **GeoPackage save fails**: Check write permissions on target directory
4. **Group not found**: Use `get_or_create_group()` instead of direct access

### Debug Information

```python
# Check available groups
groups = engine.get_available_groups()
print(f"Available groups: {groups}")

# Check layers in group
layers = engine.get_layers_in_group("TestGroup")
print(f"Layers in group: {[l.name() for l in layers]}")
```

## Future Enhancements

- Custom style support
- Batch operations
- Layer templates
- Undo/redo functionality
- Cloud storage integration

---

*Created: September 3, 2025*
*Version: 1.0*
*Engine Version: 1.0*</content>
<parameter name="filePath">c:\Users\Kalver\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\wild_code\Layer_Engine_README.md
