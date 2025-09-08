# UniversalStatusBar with Theme Support

A modern, themeable status bar component for QGIS plugins built with PyQt5.

## Features

- 🎨 **Theme Support**: Dark and light themes with easy switching
- 🔄 **Dynamic Theme Changes**: Change themes at runtime without restarting
- 📊 **Progress Indication**: Visual progress bars with customizable ranges
- 💬 **Rich Messaging**: Multiple text fields for detailed status updates
- 🖱️ **Drag Functionality**: Move status bars around the screen
- 🔧 **Programmatic UI**: Built entirely in code, no external UI files needed
- 🎯 **Factory Methods**: Easy creation with sensible defaults

## Quick Start

```python
from UniversalStatusBar import UniversalStatusBar

# Create a simple status bar with dark theme
status = UniversalStatusBar.create_simple("Loading Data", theme='dark')

# Update progress and messages
status.update(
    value=50,
    purpose="Processing records...",
    text1="Current: record_123.txt",
    text2="ETA: 30 seconds"
)

# Change theme dynamically
status.set_theme('light')

# Clean up when done
status.close()
```

## Themes

### Available Themes

- **Dark Theme**: Modern dark styling with transparency, perfect for dark QGIS themes
- **Light Theme**: Clean light styling for bright environments

### Theme Management

```python
# Get available themes
themes = UniversalStatusBar.get_available_themes()
print(themes)  # ['dark', 'light']

# Create with specific theme
status = UniversalStatusBar.create_simple("Task", theme='dark')

# Change theme dynamically
status.set_theme('light')

# Get current theme
current = status.get_current_theme()
```

## API Reference

### UniversalStatusBar Class

#### Constructor
```python
UniversalStatusBar(
    title: str = "Processing...",
    initial_value: int = 0,
    maximum: int = 100,
    stay_on_top: bool = True,
    width: int = 400,
    height: int = 150,
    theme: str = 'dark'
)
```

#### Methods

- `update(value=None, maximum=None, purpose=None, text1=None, text2=None)`: Update progress and messages
- `set_theme(theme: str)`: Change theme dynamically
- `get_current_theme() -> str`: Get current theme name
- `close()`: Close the status bar

#### Static Methods

- `get_available_themes() -> list`: Get list of available theme names
- `close_all()`: Close all active status bars

#### Factory Methods

- `create_simple(title, maximum, theme) -> UniversalStatusBar`: Simple status bar
- `create_with_message(title, message, maximum, theme) -> UniversalStatusBar`: Status bar with initial message

## Usage Examples

### Basic Progress Tracking

```python
status = UniversalStatusBar.create_simple("Importing Data", 100, theme='dark')

for i in range(101):
    status.update(
        value=i,
        purpose=f"Processing record {i}/100"
    )
    time.sleep(0.1)

status.close()
```

### Multiple Status Bars

```python
# Create multiple status bars with different themes
task1 = UniversalStatusBar.create_with_message("Task 1", "Loading files...", theme='dark')
task2 = UniversalStatusBar.create_with_message("Task 2", "Analyzing data...", theme='light')

# Update both simultaneously
task1.update(value=50, purpose="Halfway through Task 1")
task2.update(value=75, purpose="Most of Task 2 complete")

# Clean up
UniversalStatusBar.close_all()
```

### Theme Switching

```python
status = UniversalStatusBar.create_simple("Dynamic Theme Demo", theme='dark')

# Work with dark theme
status.update(purpose="Working in dark theme")

# Switch to light theme
status.set_theme('light')
status.update(purpose="Now in light theme")

# Switch back
status.set_theme('dark')
status.update(purpose="Back to dark theme")
```

## Integration with QGIS

This component is designed to work seamlessly with QGIS plugins:

1. **Theme Consistency**: Automatically matches QGIS theme preferences
2. **Transparency Support**: Works with QGIS's transparent window styling
3. **PyQt5 Integration**: Uses standard QGIS/PyQt5 components
4. **Thread Safety**: Safe to use from background threads

## Testing

Run the test suite:

```bash
cd utils/
python test_universal_status_bar.py
```

Run the theme demo:

```bash
cd utils/
python demo_themes.py
```

## Dependencies

- PyQt5
- Python 3.6+

## Files

- `UniversalStatusBar.py`: Main status bar component
- `ThemeManager.py`: Theme management system
- `test_universal_status_bar.py`: Comprehensive test suite
- `demo_themes.py`: Theme demonstration script

## License

This component is part of the QGIS plugin project and follows the same licensing terms.
