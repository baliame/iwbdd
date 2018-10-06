def is_reader_stream(s):
    if callable(getattr(s, "read", None)):
        return True
    return False


def eofc_read(reader, expected):
    data = reader.read(expected)
    if len(data) < expected:
        raise RuntimeError("Unexpected EOF")
    return data


def mousebox(x, y, x0, y0, w, h):
    return x >= x0 and y >= y0 and x < x0 + w and y < y0 + h
