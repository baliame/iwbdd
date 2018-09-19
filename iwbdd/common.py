def is_reader_stream(s):
    if callable(getattr(s, "read", None)):
        return True
    return False


def eofc_read(reader, expected):
    data = reader.read(expected)
    if len(data) < expected:
        raise RuntimeError("Unexpected EOF")
    return data
