"""pytest conftest — _ATON_LAYER."""
import sys
import os

_layer  = os.path.dirname(os.path.abspath(__file__))
_hub    = os.path.dirname(_layer)

for p in [_hub, _layer]:
    if p not in sys.path:
        sys.path.insert(0, p)
