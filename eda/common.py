from dataclasses import fields, is_dataclass
from typing import Pattern, Type

def from_string(r: Pattern):
    """
    Adds a `from_string()` function to dataclass, the string is parsed
    by the given regex `r`.
    """
    def wrap(t: Type) -> None:
        assert(is_dataclass(t))
        def _from_string(s: str):
            m = r.match(s)
            if m is None:
                raise ValueError("given string does not match the pattern")
            m = m.groupdict()
            d = {}
            for field in fields(t):
                if hasattr(field.type, "from_string"):
                    d[field.name] = field.type.from_string(m[field.name])
                else:
                    d[field.name] = field.type(m[field.name])
            return t(**d)
        t.from_string = _from_string
        return t
    return wrap
