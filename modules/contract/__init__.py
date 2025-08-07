# Each module should provide this function in its __init__.py
# Example for modules/contract/__init__.py

def get_module_metadata():
    from .ContractModule import ContractModule
    return ContractModule()  # Return a ContractModule instance for registration
