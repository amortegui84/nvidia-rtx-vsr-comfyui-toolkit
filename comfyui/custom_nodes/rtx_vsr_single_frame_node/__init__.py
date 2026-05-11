"""
RTX VSR Single Frame Node — ComfyUI custom node package init.

Registers the node with ComfyUI's node discovery system.
ComfyUI imports __init__.py from each folder inside custom_nodes/.
"""

from .rtx_vsr_single_frame_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
