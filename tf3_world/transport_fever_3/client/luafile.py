"""Read and write the Lua data files TF3 exchanges with the mod.

Format: ``function data()\\nreturn <table>\\nend``. Only a small subset of Lua is understood
(tables, double-quoted strings, numbers, booleans); the text is parsed, never executed.
An empty table reads back as an empty list.
"""
import re
from typing import Any, NoReturn


class LuaFormatError(ValueError):
    pass


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
_NUMBER = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


def dumps(value: dict) -> str:
    return "function data()\nreturn " + _dump(value, 0) + "\nend\n"


def _dump_string(text: str) -> str:
    out = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return f'"{out}"'


def _dump(value: Any, depth: int) -> str:
    pad = "\t" * (depth + 1)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return _dump_string(value)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for key, item in value.items():
            name = key if _IDENT.match(key) else f"[{_dump_string(key)}]"
            lines.append(f"{pad}{name} = {_dump(item, depth + 1)},")
        return "{\n" + "\n".join(lines) + "\n" + "\t" * depth + "}"
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value) if isinstance(value, (set, frozenset)) else list(value)
        if not items:
            return "{}"
        lines = [f"{pad}{_dump(item, depth + 1)}," for item in items]
        return "{\n" + "\n".join(lines) + "\n" + "\t" * depth + "}"
    raise TypeError(f"cannot write {type(value).__name__} to a Lua file")


def loads(text: str) -> dict:
    parser = _Parser(text)
    parser.expect_word("function")
    parser.expect_word("data")
    parser.expect_symbol("(")
    parser.expect_symbol(")")
    parser.expect_word("return")
    value = parser.value()
    parser.expect_word("end")
    parser.skip_space()
    if parser.pos != len(text):
        raise LuaFormatError("unexpected text after 'end'")
    if not isinstance(value, dict):
        # an empty table reads as []; the file's top level is always a table of named fields
        if value == []:
            return {}
        raise LuaFormatError("top-level value must be a table of named fields")
    return value


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def skip_space(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def fail(self, message: str) -> NoReturn:
        raise LuaFormatError(f"{message} at offset {self.pos}")

    def expect_word(self, word: str) -> None:
        self.skip_space()
        end = self.pos + len(word)
        continues = end < len(self.text) and (self.text[end].isalnum() or self.text[end] == "_")
        if self.text[self.pos:end] != word or continues:
            self.fail(f"expected '{word}'")
        self.pos = end

    def expect_symbol(self, symbol: str) -> None:
        self.skip_space()
        if self.text[self.pos:self.pos + len(symbol)] != symbol:
            self.fail(f"expected '{symbol}'")
        self.pos += len(symbol)

    def peek(self) -> str:
        self.skip_space()
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def value(self) -> Any:
        char = self.peek()
        if char == "{":
            return self.table()
        if char == '"':
            return self.string()
        if char == "":
            self.fail("unexpected end of text")
        match = _NUMBER.match(self.text, self.pos)
        if match:
            self.pos = match.end()
            token = match.group(0)
            return float(token) if ("." in token or "e" in token or "E" in token) else int(token)
        for word, result in (("true", True), ("false", False)):
            if self.text.startswith(word, self.pos):
                self.pos += len(word)
                return result
        self.fail("unsupported value")

    def string(self) -> str:
        self.pos += 1  # opening quote
        out = []
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char == '"':
                self.pos += 1
                return "".join(out)
            if char == "\\":
                self.pos += 1
                escaped = self.text[self.pos:self.pos + 1]
                if escaped not in _ESCAPES:
                    self.fail("unsupported escape")
                out.append(_ESCAPES[escaped])
            else:
                out.append(char)
            self.pos += 1
        self.fail("unterminated string")

    def key(self) -> str | None:
        """Return a field name if the next tokens are 'name =' or '["name"] =', else None."""
        start = self.pos
        self.skip_space()
        if self.peek() == "[":
            self.pos += 1
            name = self.string() if self.peek() == '"' else self.fail("expected string key")
            self.expect_symbol("]")
            self.expect_symbol("=")
            return name
        match = re.compile(r"[A-Za-z_][A-Za-z0-9_]*").match(self.text, self.pos)
        if match:
            probe = match.end()
            while probe < len(self.text) and self.text[probe].isspace():
                probe += 1
            if self.text[probe:probe + 1] == "=" and self.text[probe:probe + 2] != "==":
                self.pos = probe + 1
                return match.group(0)
        self.pos = start
        return None

    def table(self) -> Any:
        self.pos += 1  # opening brace
        fields: dict = {}
        items: list = []
        while True:
            if self.peek() == "}":
                self.pos += 1
                break
            if self.peek() == "":
                self.fail("unterminated table")
            name = self.key()
            item = self.value()
            if name is None:
                items.append(item)
            else:
                fields[name] = item
            if self.peek() == ",":
                self.pos += 1
        if fields and items:
            self.fail("mixed table")
        return fields if fields else items
