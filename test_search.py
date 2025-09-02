import sys
import os
sys.path.append('.')

# Set up environment
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication
from widgets.HeaderWidget import HeaderWidget

def dummy_callback():
    pass

if __name__ == "__main__":
    app = QApplication([])
    widget = HeaderWidget('Test', dummy_callback, dummy_callback)
    widget.searchEdit.setText('pakk')
    widget._perform_search()
    print("Search test completed")
