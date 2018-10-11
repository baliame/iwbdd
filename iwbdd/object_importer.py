from .object import Object
from . import moving_platform, pickups, lens
import struct
from .common import eofc_read


# Object name length (2 bytes)
# Object name (n bytes)
# pass to object to read
def read_object(reader, screen):
    name_len = struct.unpack("<H", eofc_read(reader, 2))[0]
    name = eofc_read(reader, name_len).decode('ascii')
    cl = None
    for obj in Object.object_editor_items:
        if obj.__name__ == name:
            cl = obj
            break
    if cl is None:
        raise TypeError("Unknown class: {0}".format(name))
    return cl.create_from_reader(reader, screen)
