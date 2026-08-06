"""
FILE:     tools/__init__.py
ROLE:     Tools package marker  -  enables the shared `tools._toolkit` import.
DOMAIN:   tool
DOES:     Makes tools/ an importable package so tool CLIs can `from tools._toolkit import ...`.
          The invoke() seam puts the project root on the child PYTHONPATH so this resolves.
"""
