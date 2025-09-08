#!/usr/bin/env python3
"""
Simple Theme Showcase for UniversalStatusBar
Demonstrates dark and light themes
"""

import sys
import time
from PyQt5.QtWidgets import QApplication

# Add the utils directory to the path
import os
sys.path.append(os.path.dirname(__file__))
from UniversalStatusBar import UniversalStatusBar

def showcase_themes():
    """Showcase dark and light themes."""
    print("🎨 UniversalStatusBar Theme Showcase")
    print("=" * 40)

    # Create dark theme status bar
    print("🌙 Testing Dark Theme...")
    dark_status = UniversalStatusBar.create_simple("Dark Theme", 100, theme='dark')
    dark_status.update(
        value=75,
        purpose="Dark Theme Demo",
        text1="Progress bar text is WHITE",
        text2="Background is transparent"
    )
    time.sleep(3)

    # Create light theme status bar
    print("☀️  Testing Light Theme...")
    light_status = UniversalStatusBar.create_simple("Light Theme", 100, theme='light')
    light_status.update(
        value=75,
        purpose="Light Theme Demo",
        text1="Progress bar text is DARK",
        text2="Clean and readable"
    )
    time.sleep(3)

    # Clean up
    dark_status.close()
    light_status.close()

    print("✅ Theme showcase completed!")

if __name__ == "__main__":
    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        showcase_themes()
    except Exception as e:
        print(f"❌ Showcase failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        UniversalStatusBar.close_all()
        if app:
            app.quit()
