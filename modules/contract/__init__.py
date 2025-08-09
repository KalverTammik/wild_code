# Each module should provide this function in its __init__.py
# Example for modules/contract/__init__.py

def get_module_metadata():
    from .ContractUi import ContractUi
    # Wrap ContractUi to look like a module to ModuleManager
    class _ContractWrap:
        def __init__(self):
            self.name = "ContractModule"
            self._w = ContractUi()
        def get_widget(self):
            return self._w
        def activate(self):
            pass
        def deactivate(self):
            pass
        def retheme_contract(self):
            if hasattr(self._w, 'retheme_contract'):
                self._w.retheme_contract()
    return _ContractWrap()
