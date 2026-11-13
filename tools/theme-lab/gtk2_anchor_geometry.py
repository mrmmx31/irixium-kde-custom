# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 anchoring foundation; capability stays guarded until full integration."""
from scene_anchor import anchor_origin
from scene_contract import integer


def requested_origin(record, natural):
    """Predict GtkFixed placement; explicit GTK2 requests replace natural size.

    This is only an initial prediction. Allocation remains authoritative:
    GTK2 can allocate a scrollbar below its natural requisition.
    """
    if not isinstance(natural, (tuple, list)) or len(natural) != 2:
        raise ValueError('Requisição nativa GTK2 ausente.')
    native_width = integer(natural[0], 1, 2048, 'native_width')
    native_height = integer(natural[1], 1, 2048, 'native_height')
    width = integer(record['width'], 0, 2048, 'width') or native_width
    height = integer(record['height'], 0, 2048, 'height') or native_height
    return anchor_origin(record, width, height)


def allocated_origin(record, widget):
    allocation = widget.get_allocation()
    width = integer(allocation.width, 1, 2048, 'allocated_width')
    height = integer(allocation.height, 1, 2048, 'allocated_height')
    return anchor_origin(record, width, height)
