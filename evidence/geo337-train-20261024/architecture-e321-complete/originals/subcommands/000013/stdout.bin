#!/usr/bin/env python3
"""Conservative, standard-library dependency gate for a reviewed source manifest.

This is not a production K/W/H manifest and does not certify arbitrary program
behavior. Call ``scan(root, manifest)`` or use ``--root ... --manifest ...``.
The caller must designate ALL product source roots, not just selected K files.
Every executable source below those roots needs one exact source entry or an
exact, justified, digest-locked exclusion. A dependency on an exclusion fails.
Vendor entries are individual, digest-locked files, never directory exemptions.

Manifest schema (all keys required; unknown keys rejected):
  schema: "geometry-architecture/1"
  sourceRoots: [repository-relative directory, ...]
  sourceFiles (optional): [repository-relative standalone executable file, ...]
  searchRoots: {c: [...], python: [...], javascript: [...]}
  sources: [{path, layer: K|W|H|vendor, language, purpose, [sha256]}]
  exclusions: [{path, reason, sha256, [hashMode: raw|lf]}]
  htmlScriptRoutes (optional): [{source, src, target, purpose}]
  javascriptImportRoutes (optional): [{source, specifier, target, purpose}]
  htmlEmbedRoutes (optional): [{source, elementId, driver, driverSha256,
    router, routerSha256, receiver, queryValue, srcPrefix, target, loadCount,
    resetCount, purpose}]
  trustedVendorBundles (optional): [{id, files, layers: [H], purpose}]
  policy: {
    cSystemHeaders: [exact include spelling, ...],
    pythonStdlib: [exact imported module, ...],
    javascriptBuiltins: [explicit node: builtin, ...],
    externalModules: [{language: c|python|javascript, name, purpose, layers: [H]}],
    forbiddenIdentifiers: [exact executable identifier, ...],
    forbiddenStrings: [exact decoded string value, ...],
    forbiddenModules: {c: [...], python: [...], javascript: [...]}}

K -> K; W -> K/W/vendor; H composes all layers; vendor -> vendor.
Reachability checks include package initializers and every local helper.
System/stdlib policy is explicit; K never reaches vendor, including through K
helpers. Non-host vendor is scanned normally. A trusted browser vendor bundle is
an explicit H-only boundary: every file is separately digest-locked, inventoried,
and listed exactly once. Its internal code/runtime dependencies are TRUSTED, NOT
statically verified; K/W/untrusted vendor cannot reach it. An optional exact
host import route permits only H's literal single-argument import() and adds a
normal dependency edge. Computed/unmapped imports still fail closed.
An exact H iframe route inventories a reviewed dynamic assignment and HTTP
router, both LF-digest locked. Only a same-origin root URL with one fixed query
key and about:blank resets are supported. This is an audited host route, not
general JavaScript alias/dataflow or HTTP-router verification.
The reviewed policy is a trust input, not proof
that a third-party binary or a system header has any particular behavior.

Supported dependency syntax: literal C includes (all conditional branches),
Python AST imports and regular packages, literal JS imports/re-exports/require,
and HTML script src/inline scripts/events/javascript URLs. C line splicing is
processed before comments; token boundaries and physical line numbers survive.
TS static ``import type`` is recognized. Namespace packages, computed imports,
import assertions, JSX/TSX markup and unsupported
loader syntax fail closed. JSX/TSX and C++ are inventoried but require a future
parser before owned source can pass. JS template interpolations are recursively
tokenized, including nested templates; display chunks are never executable tokens.
HTML host routes are exact source/src pairs pointing to an owned JS file; these
produce ordinary graph edges and do not exempt either endpoint from layer checks.
A lexical JS scan is not a full JS parser.

K/W/vendor forbid known dynamic Python loaders, reflection and path injection;
K/vendor also forbid browser/global JS loader escape names and known C dynamic
loaders. H may use Python host loaders, but arbitrary host runtime effects are
outside this static graph. Full no-template builds, runtime import blocking,
shared-algorithm mutants, and human responsibility review remain separate gates.
"""
from __future__ import annotations

import argparse
import ast
from collections import deque
from dataclasses import asdict, dataclass, field
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import parse_qsl, urlsplit


SCHEMA = "geometry-architecture/1"
LANGUAGES = {
    ".c": "c", ".h": "c", ".inc": "c",
    ".py": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".html": "html", ".htm": "html", ".ts": "typescript",
    ".jsx": "jsx", ".tsx": "tsx",
    ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".hh": "cpp",
}
JS_SUFFIXES = (".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx")
C_STRING_PREFIX = re.compile(r'(?:u8|[LuU])(?=["\'])')
IDENTIFIER = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
JS_NUMBER = re.compile(r"(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9_]+)?)(?:n)?")
JS_LINE_END = re.compile(r"[\n\u2028\u2029]")
ALLOWED = {"K": {"K"}, "W": {"K", "W", "vendor"},
           "H": {"K", "W", "H", "vendor"}, "vendor": {"vendor"}}
PY_LOADERS = {"importlib", "runpy", "pkgutil", "zipimport", "imp", "builtins"}
PY_DYNAMIC_NAMES = {"__import__", "__builtins__", "exec", "eval", "compile", "globals",
                    "locals", "vars", "getattr", "setattr", "delattr", "__dict__",
                    "__getattribute__", "__subclasses__"}
PY_PATH_FIELDS = {"path", "meta_path", "path_hooks", "path_importer_cache", "modules"}
JS_DYNAMIC_NAMES = {"eval", "Function", "importScripts", "createRequire", "__webpack_require__",
                    "globalThis", "global", "window", "document", "self", "Reflect", "Proxy"}
JS_REFLECTIVE_NAMES = {"eval", "Function", "constructor", "__proto__", "__lookupGetter__", "__lookupSetter__"}
JS_HTML_WRITER_NAMES = {"srcdoc", "innerHTML", "outerHTML", "insertAdjacentHTML", "setAttribute", "setAttributeNS"}
C_DYNAMIC_NAMES = {"dlopen", "dlsym", "LoadLibraryA", "LoadLibraryW", "GetProcAddress"}
C_STANDARD_HEADERS = {
    "assert.h", "complex.h", "ctype.h", "errno.h", "fenv.h", "float.h", "inttypes.h", "iso646.h",
    "limits.h", "locale.h", "math.h", "setjmp.h", "signal.h", "stdalign.h", "stdarg.h", "stdatomic.h",
    "stdbool.h", "stdckdint.h", "stdbit.h", "stddef.h", "stdint.h", "stdio.h", "stdlib.h", "stdnoreturn.h",
    "string.h", "tgmath.h", "threads.h", "time.h", "uchar.h", "wchar.h", "wctype.h",
}
NODE_BUILTINS = {
    "assert", "assert/strict", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "dns/promises", "domain",
    "events", "fs", "fs/promises", "http", "http2", "https", "inspector", "module", "net",
    "os", "path", "path/posix", "path/win32", "perf_hooks", "process", "punycode", "querystring",
    "readline", "readline/promises", "repl", "stream", "stream/consumers", "stream/promises",
    "stream/web", "string_decoder", "sys", "test", "test/reporters", "timers", "timers/promises",
    "tls", "trace_events", "tty", "url", "util", "util/types", "v8", "vm", "wasi", "worker_threads", "zlib",
}


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    line: int
    code: str
    message: str
    direction: str = ""
    chain: tuple[str, ...] = ()


class ContractError(Exception):
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic
        super().__init__(f"{diagnostic.path}:{diagnostic.line}: {diagnostic.code}: {diagnostic.message}")


def require(condition, code, path, line, message, direction="", chain=()):
    if not condition:
        raise ContractError(Diagnostic(path, max(1, line), code, message, direction, tuple(chain)))


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    target: str
    line: int


@dataclass
class ScanResult:
    diagnostics: list[Diagnostic] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    trusted_sources: list[str] = field(default_factory=list)

    @property
    def ok(self):
        return not self.diagnostics

    def to_dict(self):
        return {"ok": self.ok, "sources": self.sources,
                "trustedSourcesNotParsed": self.trusted_sources,
                "edges": [asdict(edge) for edge in self.edges],
                "diagnostics": [asdict(item) for item in self.diagnostics]}


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int


def within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def exact_keys(value, keys, context, optional=()):
    require(isinstance(value, dict) and set(keys) <= set(value) <= set(keys) | set(optional),
            "MANIFEST_SCHEMA", context, 1, f"expected keys {sorted(keys)}; optional {sorted(optional)}")


def strings(value, context):
    require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)
            and len(value) == len(set(value)), "MANIFEST_SCHEMA", context, 1,
            "expected a list of distinct, nonempty strings")
    return value


def portable_path(value, context, directory=False):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value,
            "ROOT_ESCAPE", context, 1, "paths must use repository-relative POSIX spelling")
    parts = value.split("/")
    require((directory and value == ".") or
            (not value.startswith("/") and all(part not in {"", ".", ".."} for part in parts)),
            "ROOT_ESCAPE", context, 1, "absolute, empty, dot and parent path components are forbidden")
    return value


def physical_lines(text, splice=False, javascript=False):
    """Return logical text and an original one-based line for every character."""
    output, lines = [], []
    index, line = 0, 1
    while index < len(text):
        if splice and text.startswith("\\\n", index):
            index += 2
            line += 1
            continue
        char = text[index]
        output.append(char)
        lines.append(line)
        line += char in ("\n\u2028\u2029" if javascript else "\n")
        index += 1
    return "".join(output), lines


def decode_literal(raw, path, line, *, c=False):
    result, index = [], 0
    simple = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "a": "\a",
              "\\": "\\", "\"": "\"", "'": "'", "`": "`", "/": "/"}
    while index < len(raw):
        char = raw[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue
        index += 1
        require(index < len(raw), "LEXICAL_SYNTAX", path, line, "unfinished literal escape")
        char = raw[index]
        if char in simple:
            result.append(simple[char])
            index += 1
        elif char == "\n" or (not c and char in "\u2028\u2029"):
            index += 1
        elif char in "01234567":
            match = re.match(r"[0-7]{1,3}", raw[index:])
            result.append(chr(int(match.group(), 8)))
            index += len(match.group())
        elif char in "xuU":
            digits = raw[index + 1:]
            pattern = {"x": r"[0-9a-fA-F]+" if c else r"[0-9a-fA-F]{2}",
                       "u": r"[0-9a-fA-F]{4}", "U": r"[0-9a-fA-F]{8}"}[char]
            match = re.match(pattern, digits)
            require(match is not None, "LEXICAL_SYNTAX", path, line, "unsupported literal escape")
            codepoint = int(match.group(), 16)
            require(codepoint <= 0x10FFFF, "LEXICAL_SYNTAX", path, line, "literal escape exceeds Unicode")
            result.append(chr(codepoint))
            index += len(match.group()) + 1
        else:
            require(not c, "LEXICAL_SYNTAX", path, line, f"unsupported literal escape \\{char}")
            result.append(char)  # JavaScript identity escape, including escaped ${.
            index += 1
    return "".join(result)


def lex_javascript(text, path, line_offset=0):
    """Conservative lexical goals; ambiguous slash contexts fail closed.

    Interpolations run the SAME scanner as ordinary source. Only literal chunks,
    strings, regex bodies and comments are opaque. In particular braces/comment
    markers inside regex character classes cannot conceal later executable code.
    This validates lexical nesting, not arbitrary JavaScript program semantics.
    """
    text, lines = physical_lines(text, javascript=True)
    size = len(text)
    controls = {"if", "while", "for", "with", "switch", "catch"}
    prefix_words = {"return", "throw", "case", "delete", "void", "typeof", "new", "in",
                    "instanceof", "else", "do", "const", "let", "var"}

    def line_at(index):
        return (lines[index] if index < size else (lines[-1] if lines else 1)) + line_offset

    def quoted(index):
        quote, start = text[index], index
        index += 1
        while index < size and text[index] != quote:
            require(text[index] not in "\n\u2028\u2029", "LEXICAL_SYNTAX", path, line_at(index), "unescaped line terminator in literal")
            index += 2 if text[index] == "\\" else 1
        require(index < size, "LEXICAL_SYNTAX", path, line_at(start), "unclosed string literal")
        return index + 1, Token("string", decode_literal(text[start + 1:index], path, line_at(start)), line_at(start))

    def regex(index):
        start, in_class = index, False
        index += 1
        while index < size:
            char = text[index]
            require(char not in "\n\u2028\u2029", "LEXICAL_SYNTAX", path, line_at(start), "unclosed regex literal")
            if char == "\\":
                require(index + 1 < size and text[index + 1] not in "\n\u2028\u2029", "LEXICAL_SYNTAX", path,
                        line_at(start), "unfinished regex escape")
                index += 2
                continue
            if char == "[":
                in_class = True
            elif char == "]":
                in_class = False
            elif char == "/" and not in_class:
                index += 1
                flag_start = index
                while index < size and text[index].isalpha():
                    index += 1
                flags = text[flag_start:index]
                require(set(flags) <= set("dgimsuy") and len(flags) == len(set(flags)),
                        "JS_REGEX_SYNTAX", path, line_at(start), "unsupported or duplicate regex flags")
                return index, Token("regex", text[start:index], line_at(start))
            index += 1
        require(False, "LEXICAL_SYNTAX", path, line_at(start), "unclosed regex literal")

    def template(index, depth):
        start = index
        index += 1
        chunk_start, pieces, interpolated = index, [], False
        while index < size:
            if text[index] == "\\":
                index += 2
                continue
            if text[index] == "`" or text.startswith("${", index):
                value = decode_literal(text[chunk_start:index], path, line_at(chunk_start))
                pieces.append(Token("template_chunk", value, line_at(chunk_start)))
                if text[index] == "`":
                    if not interpolated:
                        return index + 1, [Token("template", value, line_at(start))]
                    return index + 1, [Token("template_start", "`", line_at(start)), *pieces,
                                       Token("template_end", "`", line_at(index))]
                interpolated = True
                pieces.append(Token("template_expression_start", "${", line_at(index)))
                index, expression = code(index + 2, depth + 1, line_at(index))
                pieces.extend(expression)
                pieces.append(Token("template_expression_end", "}", line_at(index - 1)))
                chunk_start = index
                continue
            index += 1
        require(False, "LEXICAL_SYNTAX", path, line_at(start), "unclosed template literal")

    def code(index, depth=0, interpolation_line=None):
        require(depth <= 128, "LEXICAL_SYNTAX", path, line_at(index), "template nesting exceeds conservative limit")
        tokens, brackets = [], []
        # True = expression expected; False = expression ended; None = ambiguous
        # block/object close. A slash in the last case needs a full parser.
        regex_goal = True
        previous = ""
        previous_control = False
        while index < size:
            char, line = text[index], line_at(index)
            if char.isspace():
                index += 1
                continue
            if text.startswith("//", index):
                end = JS_LINE_END.search(text, index + 2)
                index = size if end is None else end.start()
                continue
            if text.startswith("/*", index):
                end = text.find("*/", index + 2)
                require(end != -1, "LEXICAL_SYNTAX", path, line, "unclosed block comment")
                index = end + 2
                continue
            if char in "\"'":
                index, token = quoted(index)
                tokens.append(token)
                regex_goal, previous = False, "<literal>"
                continue
            if char == "`":
                index, nested = template(index, depth)
                tokens.extend(nested)
                regex_goal, previous = False, "<literal>"
                continue
            if char == "/":
                require(regex_goal is not None, "JS_REGEX_SYNTAX", path, line,
                        "slash after a block/object close is ambiguous; parenthesize the expression")
                if regex_goal:
                    index, token = regex(index)
                    tokens.append(token)
                    regex_goal, previous = False, "<literal>"
                    continue
            require(char != "\\", "LEXICAL_SYNTAX", path, line,
                    "escaped identifiers outside literals are outside the supported lexical subset")
            require(ord(char) < 128, "JS_UNSUPPORTED_IDENTIFIER", path, line,
                    "non-ASCII executable tokens need a Unicode-aware JavaScript parser")
            match = IDENTIFIER.match(text, index)
            if match:
                value = match.group()
                tokens.append(Token("identifier", value, line))
                property_name = previous == "."
                previous_control = value in controls and not property_name
                regex_goal = (None if value in {"await", "yield"} else value in prefix_words) if not property_name else False
                previous = value
                index += len(value)
                continue
            if char.isdigit():
                # Numeric spelling cannot contain a loader name or a delimiter.
                match = JS_NUMBER.match(text, index)
                value = match.group()
                tokens.append(Token("number", value, line))
                index += len(value)
                regex_goal, previous = False, "<number>"
                continue
            token_kind = "punct"
            if char in "([{":
                if char == "[" and regex_goal is not True:
                    token_kind = "member_open"
                brackets.append((char, previous_control if char == "(" else False, line))
                regex_goal = True
            elif char in ")]}":
                if char == "}" and not brackets and interpolation_line is not None:
                    return index + 1, tokens
                require(bool(brackets) and brackets[-1][0] == {")": "(", "]": "[", "}": "{"}[char],
                        "LEXICAL_SYNTAX", path, line, "unmatched JavaScript delimiter")
                opening, control, _ = brackets.pop()
                regex_goal = control if char == ")" else (None if char == "}" else False)
            elif text[index:index + 2] in {"++", "--"}:
                value = text[index:index + 2]
                tokens.append(Token("punct", value, line))
                index += 2
                previous = value
                continue
            elif char == ".":
                regex_goal = False
            else:
                regex_goal = True
            tokens.append(Token(token_kind, char, line))
            previous = char
            previous_control = False
            index += 1
        require(interpolation_line is None, "LEXICAL_SYNTAX", path, interpolation_line or line_at(index),
                "unclosed template interpolation")
        require(not brackets, "LEXICAL_SYNTAX", path, brackets[-1][2] if brackets else line_at(index),
                "unclosed JavaScript delimiter")
        return index, tokens

    _, tokens = code(0)
    return text, lines, tokens


def javascript_numeric_index(tokens):
    """Accept a bounded primitive arithmetic key whose result is numeric.

    A bare identifier is unknown, never assumed numeric by its name. Arithmetic
    coercion such as +i, i - 1 or i | 0 proves the property key cannot be the
    string 'constructor'. Binary + needs numeric operands on BOTH sides.
    Calls, member lookups, comma/conditional expressions and string assembly
    deliberately require a future parser/type contract, rather than a guess.
    """
    position = 0
    precedence = {"|": 1, "^": 2, "&": 3, "<<": 4, ">>": 4, ">>>": 4,
                  "+": 5, "-": 5, "*": 6, "/": 6, "%": 6, "**": 7}

    def operator():
        for value in (">>>", "<<", ">>", "**", "|", "^", "&", "+", "-", "*", "/", "%"):
            parts = tokens[position:position + len(value)]
            if all(token.kind == "punct" for token in parts) and [token.value for token in parts] == list(value):
                return value
        return None

    def primary():
        nonlocal position
        if position >= len(tokens):
            return None
        token = tokens[position]
        position += 1
        if token.kind == "punct" and token.value in {"+", "-", "~", "++", "--"}:
            return True if primary() is not None else None
        if token.kind == "punct" and token.value == "(":
            numeric = expression(0)
            if position >= len(tokens) or tokens[position].kind != "punct" or tokens[position].value != ")":
                return None
            position += 1
        elif token.kind == "number":
            numeric = True
        elif token.kind == "identifier":
            numeric = False
        else:
            return None
        if position < len(tokens) and tokens[position].kind == "punct" and tokens[position].value in {"++", "--"}:
            position += 1
            numeric = True
        return numeric

    def expression(minimum):
        nonlocal position
        left = primary()
        if left is None:
            return None
        while position < len(tokens):
            op = operator()
            if op is None or precedence[op] < minimum:
                break
            position += len(op)
            right = expression(precedence[op] + (op != "**"))
            if right is None:
                return None
            left = left and right if op == "+" else True
        return left

    numeric = expression(0)
    return numeric is True and position == len(tokens)


def javascript_property_key_locations(tokens):
    """Locate member keys and explicit object/pattern/method property keys.

    A bracket after an expression is a member access. At a brace field boundary,
    a bracket closed immediately before ':' or '(' is an object/pattern/method
    key instead. Neither case is an ordinary array literal or ternary value.
    """
    computed = {offset for offset, token in enumerate(tokens) if token.kind == "member_open"}
    literal_keys, stack = set(), []
    for offset, token in enumerate(tokens):
        if token.kind in {"template_expression_start", "template_expression_end"}:
            continue
        before = tokens[offset - 1].value if offset else None
        after = tokens[offset + 1].value if offset + 1 < len(tokens) else None
        field_boundary = bool(stack) and stack[-1][0] == "{" and before in {"{", ","}
        if token.kind == "string" and field_boundary and after in {":", "("}:
            literal_keys.add(offset)
        if token.kind in {"punct", "member_open"} and token.value in {"(", "[", "{"}:
            stack.append((token.value, offset, token.value == "[" and field_boundary))
        elif token.kind == "punct" and token.value in {")", "]", "}"} and stack:
            opening, start, object_key = stack.pop()
            if opening == "[" and object_key and after in {":", "("}:
                computed.add(start)
    return computed, literal_keys


def lex(text, path, *, c=False, line_offset=0):
    if not c:
        return lex_javascript(text, path, line_offset)
    text, line_map = physical_lines(text, splice=c)
    masked, tokens = list(text), []
    index = 0
    while index < len(text):
        char = text[index]
        line = line_map[index] + line_offset
        if char.isspace():
            index += 1
            continue
        if text.startswith("//", index) or text.startswith("/*", index):
            if text.startswith("//", index):
                end = text.find("\n", index)
                end = len(text) if end == -1 else end
            else:
                end = text.find("*/", index + 2)
                require(end != -1, "LEXICAL_SYNTAX", path, line, "unclosed block comment")
                end += 2
            for position in range(index, end):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue
        prefix = C_STRING_PREFIX.match(text, index) if c else None
        if prefix:
            index += len(prefix.group())
            char = text[index]
        require(not text.startswith("%:", index), "C_UNSUPPORTED_PREPROCESSOR", path, line,
                "preprocessor digraphs need a dedicated preprocessing parser")
        if char in "\"'`":
            require(not c or char != "`", "LEXICAL_SYNTAX", path, line, "backticks are not C literals")
            quote, start = char, index
            index += 1
            while index < len(text) and text[index] != quote:
                require(text[index] != "\n" or quote == "`", "LEXICAL_SYNTAX", path, line,
                        "unescaped newline in literal")
                if text[index] == "\\":
                    index += 2
                else:
                    index += 1
            require(index < len(text), "LEXICAL_SYNTAX", path, line, "unclosed string or character literal")
            raw = text[start + 1:index]
            kind = "char" if c and quote == "'" else ("template" if quote == "`" else "string")
            tokens.append(Token(kind, decode_literal(raw, path, line, c=c), line))
            index += 1
            continue
        require(char != "\\", "LEXICAL_SYNTAX", path, line,
                "escaped identifiers outside literals are outside the supported lexical subset")
        match = IDENTIFIER.match(text, index)
        if match:
            value = match.group()
            tokens.append(Token("identifier", value, line))
            index += len(value)
        else:
            tokens.append(Token("punct", char, line))
            index += 1
    return "".join(masked), line_map, tokens


def named_js_clause(tokens, typescript=False):
    if len(tokens) < 2 or tokens[0].value != "{" or tokens[-1].value != "}":
        return False
    groups, group = [], []
    for token in tokens[1:-1]:
        if token.value == ",":
            if not group:
                return False
            groups.append(group)
            group = []
        else:
            group.append(token)
    if group:
        groups.append(group)
    for group in groups:
        if typescript and len(group) > 1 and group[0].value == "type":
            group = group[1:]
        if not (len(group) == 1 and group[0].kind == "identifier" or
                len(group) == 3 and group[0].kind == group[2].kind == "identifier" and group[1].value == "as"):
            return False
    return True


def static_js_clause(tokens, typescript=False):
    if typescript and tokens and tokens[0].value == "type":
        tokens = tokens[1:]
    if not tokens:
        return False
    if tokens[0].kind == "identifier":
        if len(tokens) == 1:
            return True
        if tokens[1].value != ",":
            return False
        tokens = tokens[2:]
    return (len(tokens) == 3 and [tokens[0].value, tokens[1].value] == ["*", "as"]
            and tokens[2].kind == "identifier") or named_js_clause(tokens, typescript)


class Scanner:
    def __init__(self, root, manifest):
        self.root = Path(root).resolve()
        self.manifest = manifest
        self.result = ScanResult()
        self.entries = {}
        self.exclusions = {}
        self.search = {}
        self.policy = {}
        self.html_routes = {}
        self.javascript_routes = {}
        self.html_embed_routes = {}
        self.trusted_vendor = set()

    def safe(self, relative, context=None):
        context = context or relative
        path = self.root / relative
        require(within(path.resolve(), self.root), "ROOT_ESCAPE", context, 1,
                "resolved path escapes the repository")
        cursor = self.root
        for part in PurePosixPath(relative).parts:
            cursor /= part
            require(not cursor.is_symlink(), "SOURCE_SYMLINK", context, 1,
                    "source aliases are not permitted; declare the real owned file")
        return path

    def validate_manifest(self):
        data = self.manifest
        exact_keys(data, {"schema", "sourceRoots", "searchRoots", "sources", "exclusions", "policy"}, "<manifest>",
                   {"htmlScriptRoutes", "javascriptImportRoutes", "htmlEmbedRoutes", "trustedVendorBundles", "sourceFiles"})
        require(data["schema"] == SCHEMA, "MANIFEST_SCHEMA", "<manifest>", 1, "unknown manifest schema")
        roots = strings(data["sourceRoots"], "sourceRoots")
        files = strings(data.get("sourceFiles", []), "sourceFiles")
        require(bool(roots or files), "MANIFEST_SCHEMA", "sourceRoots", 1, "at least one complete product root/file is required")
        for relative in roots:
            portable_path(relative, "sourceRoots", directory=True)
            require(self.safe(relative).is_dir(), "SOURCE_ROOT", relative, 1, "source root is not a directory")
        physical_roots = [self.safe(relative).resolve() for relative in roots]
        require(all(not within(a, b) for i, a in enumerate(physical_roots)
                    for j, b in enumerate(physical_roots) if i != j),
                "MANIFEST_SCHEMA", "sourceRoots", 1, "source roots must not overlap")
        physical_files = set()
        for relative in files:
            portable_path(relative, "sourceFiles")
            path = self.safe(relative)
            require(path.is_file() and path.suffix.lower() in LANGUAGES,
                    "SOURCE_ROOT", relative, 1, "standalone source must be an existing executable file")
            require(not any(within(path.resolve(), root) for root in physical_roots),
                    "MANIFEST_SCHEMA", relative, 1, "standalone source overlaps an inventoried root")
            require(path.resolve() not in physical_files, "SOURCE_DUPLICATE", relative, 1, "duplicate standalone source")
            physical_files.add(path.resolve())
        exact_keys(data["searchRoots"], {"c", "python", "javascript"}, "searchRoots")
        for language, directories in data["searchRoots"].items():
            self.search[language] = []
            for relative in strings(directories, "searchRoots." + language):
                portable_path(relative, "searchRoots." + language, directory=True)
                path = self.safe(relative)
                require(path.is_dir(), "SEARCH_ROOT", relative, 1, "declared search root is not a directory")
                self.search[language].append(path)
        require(isinstance(data["sources"], list) and isinstance(data["exclusions"], list),
                "MANIFEST_SCHEMA", "<manifest>", 1, "sources and exclusions must be lists")
        seen = set()
        for entry in data["sources"]:
            exact_keys(entry, {"path", "layer", "language", "purpose"}, "sources", {"sha256"})
            relative = portable_path(entry["path"], "sources")
            require(relative.casefold() not in seen, "SOURCE_DUPLICATE", relative, 1, "source appears more than once")
            seen.add(relative.casefold())
            require(isinstance(entry["layer"], str) and entry["layer"] in ALLOWED
                    and isinstance(entry["purpose"], str) and entry["purpose"].strip(),
                    "MANIFEST_SCHEMA", relative, 1, "source needs a known layer and explicit purpose")
            require(LANGUAGES.get(PurePosixPath(relative).suffix.lower()) == entry["language"],
                    "SOURCE_LANGUAGE", relative, 1, "extension and declared language disagree")
            path = self.safe(relative)
            require(path.is_file(), "SOURCE_MISSING", relative, 1, "declared source is missing")
            require(path.resolve() in physical_files or any(within(path.resolve(), root) for root in physical_roots),
                    "SOURCE_OUTSIDE_ROOTS", relative, 1, "source is outside the complete product roots")
            if entry["layer"] == "vendor":
                self.check_digest(path, entry.get("sha256"), "VENDOR_DIGEST")
            else:
                require("sha256" not in entry, "MANIFEST_SCHEMA", relative, 1, "only vendor entries use immutable source digests")
            self.entries[relative] = entry
        for entry in data["exclusions"]:
            exact_keys(entry, {"path", "reason", "sha256"}, "exclusions", {"hashMode"})
            relative = portable_path(entry["path"], "exclusions")
            require(relative.casefold() not in seen, "SOURCE_DUPLICATE", relative, 1, "source/exclusion appears more than once")
            seen.add(relative.casefold())
            require(isinstance(entry["reason"], str) and entry["reason"].strip(),
                    "MANIFEST_SCHEMA", relative, 1, "an exclusion needs a concrete reason")
            path = self.safe(relative)
            require(path.is_file() and path.suffix.lower() in LANGUAGES,
                    "SOURCE_MISSING", relative, 1, "exclusion must name an existing executable source")
            require(path.resolve() in physical_files or any(within(path.resolve(), root) for root in physical_roots),
                    "SOURCE_OUTSIDE_ROOTS", relative, 1, "exclusion is outside product roots")
            mode = entry.get("hashMode", "raw")
            require(isinstance(mode, str) and mode in {"raw", "lf"}, "EXCLUSION_HASH_MODE", relative, 1,
                    "exclusion hash mode must be raw or explicit CRLF-to-LF normalization")
            self.check_digest(path, entry["sha256"], "EXCLUSION_DIGEST", mode=mode)
            self.exclusions[relative] = entry
        discovered = {path.relative_to(self.root).as_posix() for path in physical_files}
        for directory in physical_roots:
            for current, directories, files in os.walk(directory, followlinks=False):
                directories.sort()
                for name in sorted(directories + files):
                    path = Path(current) / name
                    relative = path.relative_to(self.root).as_posix()
                    self.safe(relative)
                    if path.is_file() and path.suffix.lower() in LANGUAGES:
                        discovered.add(relative)
        require(len({name.casefold() for name in discovered}) == len(discovered),
                "SOURCE_CASE_COLLISION", "<inventory>", 1, "case-only source names are not portable")
        for relative in sorted(discovered):
            require(relative in self.entries or relative in self.exclusions,
                    "SOURCE_UNREGISTERED", relative, 1, "executable source omitted from the complete manifest")
        self.validate_policy(data["policy"])
        self.validate_html_routes(data.get("htmlScriptRoutes", []))
        self.validate_javascript_routes(data.get("javascriptImportRoutes", []))
        self.validate_html_embed_routes(data.get("htmlEmbedRoutes", []))
        self.validate_vendor_bundles(data.get("trustedVendorBundles", []))
        self.result.trusted_sources = sorted(self.trusted_vendor)
        self.result.sources = sorted(self.entries)

    def validate_html_routes(self, routes):
        require(isinstance(routes, list), "MANIFEST_SCHEMA", "htmlScriptRoutes", 1, "expected a route list")
        seen = set()
        for route in routes:
            exact_keys(route, {"source", "src", "target", "purpose"}, "htmlScriptRoutes")
            source = portable_path(route["source"], "htmlScriptRoutes.source")
            target = portable_path(route["target"], "htmlScriptRoutes.target")
            src = route["src"]
            require(isinstance(src, str) and src and not any(char in src for char in "\\:%?#")
                    and not src.startswith("//") and not any(char.isspace() for char in src),
                    "HTML_ROUTE_SYNTAX", source, 1, "route src must be an exact local URL path")
            portable_path(src[1:] if src.startswith("/") else src, "htmlScriptRoutes.src")
            require(isinstance(route["purpose"], str) and route["purpose"].strip(),
                    "MANIFEST_SCHEMA", source, 1, "host route needs an explicit purpose")
            key = (source, src)
            require(tuple(part.casefold() for part in key) not in seen, "HTML_ROUTE_DUPLICATE", source, 1,
                    "duplicate or case-ambiguous source/src route")
            seen.add(tuple(part.casefold() for part in key))
            require(source in self.entries and self.entries[source]["language"] == "html",
                    "HTML_ROUTE_SOURCE", source, 1, "route source must be one exact owned HTML source")
            require(target in self.entries and self.entries[target]["language"] == "javascript",
                    "HTML_ROUTE_TARGET", source, 1, "route target must be one exact owned JavaScript source")
            self.html_routes[key] = target

    def validate_javascript_routes(self, routes):
        require(isinstance(routes, list), "MANIFEST_SCHEMA", "javascriptImportRoutes", 1, "expected a route list")
        seen = set()
        for route in routes:
            exact_keys(route, {"source", "specifier", "target", "purpose"}, "javascriptImportRoutes")
            source = portable_path(route["source"], "javascriptImportRoutes.source")
            target = portable_path(route["target"], "javascriptImportRoutes.target")
            name = route["specifier"]
            require(isinstance(name, str) and name and not any(char in name for char in "\\:%?#")
                    and not name.startswith("//") and not any(char.isspace() for char in name),
                    "JS_ROUTE_SYNTAX", source, 1, "host import route must be an exact local URL path")
            portable_path(name[1:] if name.startswith("/") else name, "javascriptImportRoutes.specifier")
            require(isinstance(route["purpose"], str) and route["purpose"].strip(),
                    "MANIFEST_SCHEMA", source, 1, "host import route needs an explicit purpose")
            key = (source, name)
            folded = tuple(part.casefold() for part in key)
            require(folded not in seen, "JS_ROUTE_DUPLICATE", source, 1, "duplicate source/specifier route")
            seen.add(folded)
            require(source in self.entries and self.entries[source]["layer"] == "H"
                    and self.entries[source]["language"] in {"javascript", "typescript", "html"},
                    "JS_ROUTE_SOURCE", source, 1, "only exact owned host script sources may declare import routes")
            require(target in self.entries and self.entries[target]["language"] == "javascript",
                    "JS_ROUTE_TARGET", source, 1, "host import target must be one exact owned JavaScript source")
            self.javascript_routes[key] = target

    def validate_html_embed_routes(self, routes):
        require(isinstance(routes, list), "MANIFEST_SCHEMA", "htmlEmbedRoutes", 1, "expected an exact host embed route list")
        for route in routes:
            exact_keys(route, {"source", "elementId", "driver", "driverSha256", "router", "routerSha256",
                              "receiver", "queryValue", "srcPrefix", "target", "loadCount", "resetCount", "purpose"},
                       "htmlEmbedRoutes")
            for name, language in (("source", "html"), ("target", "html"), ("driver", "javascript"), ("router", "python")):
                relative = portable_path(route[name], "htmlEmbedRoutes." + name)
                require(relative in self.entries and self.entries[relative]["layer"] == "H"
                        and self.entries[relative]["language"] == language,
                        "HTML_EMBED_ROUTE_LAYER", relative, 1, "embed source, target, driver and router must be exact owned H sources")
            source = route["source"]
            require(isinstance(route["elementId"], str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", route["elementId"])
                    and isinstance(route["purpose"], str) and route["purpose"].strip(),
                    "HTML_EMBED_ROUTE_SYNTAX", source, 1, "embed route needs an exact element id and purpose")
            key = (source, route["elementId"])
            require(key not in self.html_embed_routes, "HTML_EMBED_ROUTE_DUPLICATE", source, 1, "duplicate embed element route")
            prefix = route["srcPrefix"]
            require(isinstance(prefix, str) and re.fullmatch(r"/\?[A-Za-z_][A-Za-z0-9_]*=", prefix),
                    "HTML_EMBED_ROUTE_SYNTAX", source, 1, "only a same-origin root path with one fixed query key is supported")
            require(isinstance(route["receiver"], str) and re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*\.[A-Za-z_$][A-Za-z0-9_$]*", route["receiver"])
                    and isinstance(route["queryValue"], str) and re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", route["queryValue"])
                    and type(route["loadCount"]) is int and route["loadCount"] > 0
                    and type(route["resetCount"]) is int and route["resetCount"] >= 0,
                    "HTML_EMBED_ROUTE_SYNTAX", source, 1, "embed assignment receiver, value and occurrence counts must be exact")
            for name in ("driver", "router"):
                self.check_digest(self.safe(route[name]), route[name + "Sha256"], "HTML_EMBED_ROUTE_DIGEST", mode="lf")
            text = self.safe(route["driver"]).read_text(encoding="utf-8")
            _, _, tokens = lex(text, route["driver"])
            values = [token.value for token in tokens]
            receiver = route["receiver"].split(".")
            lhs = [receiver[0], ".", receiver[1], ".", "src", "="]
            selector = [receiver[1], ":", "$", "(", route["elementId"], ")"]
            count_pattern = lambda pattern: sum(values[i:i + len(pattern)] == pattern for i in range(len(values)))
            require(count_pattern(selector) == 1, "HTML_EMBED_ASSIGNMENT", route["driver"], 1,
                    "reviewed driver must bind the exact frame element once")
            load = lhs + [prefix, "+", route["queryValue"], ";"]
            reset = lhs + ["about:blank", ";"]
            require(count_pattern(load) == route["loadCount"] and count_pattern(reset) == route["resetCount"]
                    and sum(token.value == "src" for token in tokens) == route["loadCount"] + route["resetCount"]
                    and all(token.value != "srcdoc" for token in tokens),
                    "HTML_EMBED_ASSIGNMENT", route["driver"], 1,
                    "driver src assignments must be exactly the reviewed root-query loads and blank resets")
            self.html_embed_routes[key] = route

    def html_embed_dependency(self, path, values, line):
        route = self.html_embed_routes.get((path, values.get("id")))
        require(route is not None, "HTML_EMBED_UNSUPPORTED", path, line,
                "iframe requires one exact reviewed H element/driver/router route")
        if "src" in values:
            src = values["src"]
            valid = src == "about:blank"
            if isinstance(src, str) and src.startswith(route["srcPrefix"]):
                url = urlsplit(src)
                query = parse_qsl(url.query, keep_blank_values=True)
                valid = (not any(char.isspace() or ord(char) < 32 for char in src)
                         and not url.scheme and not url.netloc and url.path == "/" and not url.fragment
                         and len(query) == 1 and query[0][0] == route["srcPrefix"][2:-1])
            require(valid, "HTML_EMBED_SOURCE", path, line, "iframe src must match its exact reviewed same-origin root-query route")
        self.owned(self.safe(route["target"]), path, line)
        self.owned(self.safe(route["driver"]), path, line)
        self.owned(self.safe(route["target"]), route["driver"], 1)

    def validate_vendor_bundles(self, bundles):
        require(isinstance(bundles, list), "MANIFEST_SCHEMA", "trustedVendorBundles", 1, "expected a bundle list")
        ids = set()
        for bundle in bundles:
            exact_keys(bundle, {"id", "files", "layers", "purpose"}, "trustedVendorBundles")
            require(isinstance(bundle["id"], str) and bundle["id"].strip() and bundle["id"] not in ids
                    and bundle["layers"] == ["H"] and isinstance(bundle["purpose"], str) and bundle["purpose"].strip(),
                    "VENDOR_TRUST_POLICY", "trustedVendorBundles", 1, "bundle needs a distinct id, purpose and H-only trust boundary")
            ids.add(bundle["id"])
            files = strings(bundle["files"], "trustedVendorBundles.files")
            require(bool(files), "VENDOR_TRUST_POLICY", bundle["id"], 1, "trusted bundle must list exact files")
            for relative in files:
                portable_path(relative, "trustedVendorBundles.files")
                require(relative not in self.trusted_vendor, "VENDOR_TRUST_DUPLICATE", relative, 1,
                        "trusted vendor file appears in multiple bundles")
                require(relative in self.entries and self.entries[relative]["layer"] == "vendor"
                        and self.entries[relative]["language"] == "javascript",
                        "VENDOR_TRUST_SOURCE", relative, 1, "trusted file must be an exact digest-locked browser vendor source")
                self.trusted_vendor.add(relative)
        if bundles:
            require(self.trusted_vendor == {path for path, entry in self.entries.items() if entry["layer"] == "vendor"},
                    "VENDOR_TRUST_UNDECLARED", "trustedVendorBundles", 1, "when host trust is used, every vendor file must be listed exactly once")

    def check_digest(self, path, digest, code, mode="raw"):
        raw = path.read_bytes()
        if mode == "lf":
            raw = raw.replace(b"\r\n", b"\n")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                and hashlib.sha256(raw).hexdigest() == digest,
                code, path.relative_to(self.root).as_posix(), 1, f"immutable {mode} digest is absent or mismatched")

    def validate_policy(self, policy):
        exact_keys(policy, {"cSystemHeaders", "pythonStdlib", "javascriptBuiltins", "externalModules",
                            "forbiddenIdentifiers", "forbiddenStrings", "forbiddenModules"}, "policy")
        for key in ("cSystemHeaders", "pythonStdlib", "javascriptBuiltins", "forbiddenIdentifiers", "forbiddenStrings"):
            strings(policy[key], "policy." + key)
        for name in policy["cSystemHeaders"]:
            require(name in C_STANDARD_HEADERS, "EXTERNAL_POLICY", name, 1,
                    "only known standard C headers are available to all layers; platform headers need an exact H-only external allowance")
        require(hasattr(sys, "stdlib_module_names"), "PYTHON_VERSION", "policy.pythonStdlib", 1,
                "Python 3.10+ is required for stdlib policy validation")
        for name in policy["pythonStdlib"]:
            require(name.split(".")[0] in sys.stdlib_module_names,
                    "EXTERNAL_POLICY", name, 1, "declared Python stdlib module is not a standard-library root")
        for name in policy["javascriptBuiltins"]:
            require(name.startswith("node:") and name[5:] in NODE_BUILTINS,
                    "EXTERNAL_POLICY", name, 1, "only explicit known node: builtins belong in this policy")
        exact_keys(policy["forbiddenModules"], {"c", "python", "javascript"}, "policy.forbiddenModules")
        for language, values in policy["forbiddenModules"].items():
            strings(values, "policy.forbiddenModules." + language)
        require(isinstance(policy["externalModules"], list), "MANIFEST_SCHEMA", "policy.externalModules", 1, "expected a list")
        external_seen = set()
        for entry in policy["externalModules"]:
            exact_keys(entry, {"language", "name", "layers", "purpose"}, "policy.externalModules")
            require(entry["language"] in {"c", "python", "javascript"} and isinstance(entry["name"], str)
                    and entry["name"].strip() and entry["layers"] == ["H"]
                    and isinstance(entry["purpose"], str) and entry["purpose"].strip(),
                    "EXTERNAL_POLICY", "policy.externalModules", 1,
                    "third-party external allowances must name one module, a purpose and only H")
            key = (entry["language"], entry["name"])
            require(key not in external_seen, "EXTERNAL_POLICY", entry["name"], 1, "duplicate external allowance")
            external_seen.add(key)
        self.policy = policy

    def core_tokens(self, path, identifiers, literals):
        if self.entries[path]["layer"] not in {"K", "vendor"}:
            return
        for name, line in identifiers:
            require(name not in self.policy["forbiddenIdentifiers"], "FORBIDDEN_IDENTIFIER", path, line,
                    f"concrete template identifier {name!r} in core", "K -> W", (path,))
        for value, line in literals:
            require(value not in self.policy["forbiddenStrings"], "FORBIDDEN_STRING", path, line,
                    f"concrete template string {value!r} in core", "K -> W", (path,))

    def module_policy(self, path, name, language, line):
        if self.entries[path]["layer"] not in {"K", "vendor"}:
            return
        separator = "." if language == "python" else "/"
        forbidden = self.policy["forbiddenModules"][language]
        require(not any(name == item or name.startswith(item + separator) for item in forbidden),
                "FORBIDDEN_MODULE", path, line, f"concrete template module {name!r} in core", "K -> W", (path, name))

    def external_allowed(self, path, name, language):
        key = {"c": "cSystemHeaders", "python": "pythonStdlib", "javascript": "javascriptBuiltins"}[language]
        if name in self.policy[key]:
            return True
        return any(entry["language"] == language and entry["name"] == name
                   and self.entries[path]["layer"] in entry["layers"] for entry in self.policy["externalModules"])

    def owned(self, target, source, line):
        require(within(target.resolve(), self.root), "ROOT_ESCAPE", source, line,
                "dependency resolves outside repository", chain=(source, str(target)))
        relative = target.relative_to(self.root).as_posix()
        self.safe(relative, source)
        require(relative not in self.exclusions, "DEPENDENCY_EXCLUDED", source, line,
                f"dependency {relative} is excluded from product source", chain=(source, relative))
        require(relative in self.entries, "DEPENDENCY_UNREGISTERED", source, line,
                f"dependency {relative} is not an owned manifest source", chain=(source, relative))
        self.result.edges.append(Edge(source, relative, line))

    def local(self, candidates, source, line, specifier):
        found, outside = [], False
        for candidate in candidates:
            resolved = candidate.resolve()
            if not within(resolved, self.root):
                outside = True
                require(not candidate.exists(), "ROOT_ESCAPE", source, line,
                        f"dependency {specifier!r} resolves outside the repository")
                continue
            if candidate.is_file() and resolved not in found:
                found.append(resolved)
        require(bool(found) or not outside, "ROOT_ESCAPE", source, line,
                f"dependency {specifier!r} leaves the repository without a declared local resolution")
        require(len(found) <= 1, "DEPENDENCY_AMBIGUOUS", source, line,
                f"{specifier!r} resolves to multiple declared candidates: "
                + ", ".join(x.relative_to(self.root).as_posix() for x in found))
        return found[0] if found else None

    def scan_c(self, path, text):
        embedded_bom = text.find("\ufeff", 1)
        require(embedded_bom == -1, "C_UNSUPPORTED_BOM", path,
                text.count("\n", 0, embedded_bom) + 1 if embedded_bom != -1 else 1,
                "only one initial UTF-8 BOM is supported; embedded BOM characters need explicit preprocessing support")
        text = text.removeprefix("\ufeff")
        trigraph = re.search(r"\?\?[=/'()!<>-]", text)
        require(trigraph is None, "C_UNSUPPORTED_TRIGRAPH", path,
                text.count("\n", 0, trigraph.start()) + 1 if trigraph else 1,
                "C trigraph replacement occurs before comments and is outside the supported preprocessing subset")
        masked, lines, tokens = lex(text, path, c=True)
        identifiers = [(token.value, token.line) for token in tokens if token.kind == "identifier"]
        literals = []
        index = 0
        while index < len(tokens):
            if tokens[index].kind == "string":
                start, value = tokens[index].line, tokens[index].value
                index += 1
                while index < len(tokens) and tokens[index].kind == "string":
                    value += tokens[index].value
                    index += 1
                literals.append((value, start))
            else:
                index += 1
        self.core_tokens(path, identifiers, literals)
        if self.entries[path]["layer"] in {"K", "vendor"}:
            for name, line in identifiers:
                require(name not in C_DYNAMIC_NAMES, "C_DYNAMIC_LOAD", path, line, "dynamic native loader in core")
            for index, token in enumerate(tokens[:-1]):
                require(not (token.value == tokens[index + 1].value == "#"), "C_TOKEN_PASTE", path, token.line,
                        "token-pasted core identifiers cannot be statically classified")
        for match in re.finditer(r"^[ \t\v\f]*#[ \t\v\f]*(include_next|include|import)\b([^\n]*)", masked, re.MULTILINE):
            line = lines[match.start()] if lines else 1
            require(match.group(1) == "include", "C_UNSUPPORTED_INCLUDE", path, line, "unsupported preprocessor loader")
            body = match.group(2).strip()
            literal = re.fullmatch(r'"([^"\n]+)"|<([^>\n]+)>', body)
            require(literal is not None, "C_DYNAMIC_INCLUDE", path, line, "include must name a literal file or system header")
            name = literal.group(1) or literal.group(2)
            require("\\" not in name, "C_INCLUDE_SYNTAX", path, line, "include paths must use portable forward slashes")
            self.module_policy(path, name, "c", line)
            roots = [self.root / PurePosixPath(path).parent] if literal.group(1) else []
            roots += self.search["c"]
            target = self.local([directory / name for directory in roots], path, line, name)
            if target is not None:
                self.owned(target, path, line)
            else:
                require(literal.group(2) is not None and self.external_allowed(path, name, "c"),
                        "DEPENDENCY_UNRESOLVED", path, line, f"unresolved C include {name!r}")

    def python_module(self, source, name, line, level=0):
        self.module_policy(source, name, "python", line)
        directories = self.search["python"]
        if level:
            file = self.root / source
            owners = [root for root in directories if within(file, root)
                      and all(part.isidentifier() for part in file.relative_to(root).parts[:-1])]
            require(len(owners) == 1, "PYTHON_PACKAGE", source, line, "relative import needs one declared package root")
            directory = owners[0]
            package = list(file.relative_to(directory).parts[:-1])
            require(level <= len(package), "ROOT_ESCAPE", source, line, "relative import leaves its declared package root")
            parts = package[:len(package) - level + 1] + (name.split(".") if name else [])
            name = ".".join(parts)
            directories = [directory]
        pieces = name.split(".") if name else []
        require(bool(pieces) and all(piece.isidentifier() for piece in pieces),
                "PYTHON_PACKAGE", source, line, "empty or unsupported module spelling")
        self.module_policy(source, name, "python", line)
        candidates = [candidate for directory in directories
                      for candidate in (directory.joinpath(*pieces).with_suffix(".py"), directory.joinpath(*pieces, "__init__.py"))]
        target = self.local(candidates, source, line, name)
        if target is None:
            require(not level and self.external_allowed(source, name, "python"),
                    "DEPENDENCY_UNRESOLVED", source, line, f"unresolved Python module {name!r}")
            return None
        owner = next(root for root in directories if within(target, root))
        for size in range(1, len(pieces)):
            initializer = owner.joinpath(*pieces[:size], "__init__.py")
            require(initializer.is_file(), "PYTHON_PACKAGE", source, line,
                    "namespace packages are outside this gate's declared import subset")
            self.owned(initializer, source, line)
        self.owned(target, source, line)
        return target

    def python_package_initializers(self, path):
        # Importing this source executes its regular-package initializers even
        # when its own body has no import. Attach the requirement to the module,
        # not only to whichever host happened to import it during this scan.
        file = self.root / path
        for root in self.search["python"]:
            if not within(file, root):
                continue
            parts = file.relative_to(root).parts[:-1]
            if not all(part.isidentifier() for part in parts):
                continue
            for size in range(1, len(parts) + 1):
                initializer = root.joinpath(*parts[:size], "__init__.py")
                if initializer.is_file() and initializer != file:
                    self.owned(initializer, path, 1)

    def scan_python(self, path, text):
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as error:
            require(False, "PYTHON_SYNTAX", path, error.lineno or 1, error.msg)
        self.python_package_initializers(path)
        nodes = sorted(ast.walk(tree), key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))
        identifiers, literals, aliases = [], [], {}
        strict = self.entries[path]["layer"] != "H"
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases.setdefault(alias.asname or alias.name.split(".")[0], set()).add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    aliases.setdefault(alias.asname or alias.name, set()).add((node.module or "") + "." + alias.name)
            if isinstance(node, ast.Name):
                identifiers.append((node.id, node.lineno))
            elif isinstance(node, ast.Attribute):
                identifiers.append((node.attr, node.lineno))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                identifiers.append((node.name, node.lineno))
            elif isinstance(node, ast.arg):
                identifiers.append((node.arg, node.lineno))
            elif isinstance(node, ast.alias):
                identifiers.extend((name, node.lineno) for name in node.name.split("."))
                if node.asname:
                    identifiers.append((node.asname, node.lineno))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.append((node.value, node.lineno))
        self.core_tokens(path, identifiers, literals)
        if strict:
            for name, line in identifiers:
                require(name not in PY_DYNAMIC_NAMES, "CORE_DYNAMIC_IMPORT", path, line,
                        f"reflective/dynamic Python entry point {name!r} is forbidden in K/W/vendor")
        def qualified(node):
            if isinstance(node, ast.Name):
                return aliases.get(node.id, {node.id})
            if isinstance(node, ast.Attribute):
                return {base + "." + node.attr for base in qualified(node.value)}
            if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                return set().union(*(qualified(item) for item in node.elts))
            if isinstance(node, ast.Dict):
                return set().union(*(qualified(item) for item in [*node.keys, *node.values] if item is not None))
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                values = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
                return set().union(*(qualified(item) for item in values))
            if isinstance(node, (ast.Starred, ast.Subscript, ast.NamedExpr)):
                return qualified(node.value)
            if isinstance(node, ast.IfExp):
                return qualified(node.body) | qualified(node.orelse)
            if isinstance(node, ast.BoolOp):
                return set().union(*(qualified(item) for item in node.values))
            return set()
        def assignment_names(target):
            if isinstance(target, ast.Name):
                return [target.id]
            if isinstance(target, (ast.Tuple, ast.List)):
                return [name for item in target.elts for name in assignment_names(item)]
            if isinstance(target, ast.Starred):
                return assignment_names(target.value)
            return []
        def supported_alias_target(target):
            if isinstance(target, ast.Name):
                return True
            if isinstance(target, (ast.Tuple, ast.List)):
                return all(supported_alias_target(item) for item in target.elts)
            if isinstance(target, ast.Starred):
                return supported_alias_target(target.value)
            return False
        # Conservative alias union: later shadowing cannot hide an earlier path
        # mutation. Container elements are deliberately over-approximated rather
        # than guessed to be neutral when unpacked or selected through an index.
        bindings = [(target, node.value) for node in nodes if isinstance(node, ast.Assign) for target in node.targets]
        bindings.extend((node.target, node.value) for node in nodes
                        if isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None)
        bindings.extend((node.target, node.iter) for node in nodes if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)))
        assignments = [(name, value) for target, value in bindings for name in assignment_names(target)]
        for _ in range(len(assignments) + 1):
            changed = False
            for name, value in assignments:
                incoming = qualified(value)
                previous = aliases.setdefault(name, set())
                if not incoming <= previous:
                    previous.update(incoming)
                    changed = True
            if not changed:
                break
        for target, value in bindings:
            require(not strict or supported_alias_target(target) or
                    not any(name == "sys" or name.startswith("sys.") for name in qualified(value)),
                    "CORE_SYS_ALIAS_TARGET", path, getattr(target, "lineno", 1),
                    "storing sys provenance through an attribute/subscript target is outside the supported alias subset")
        for node in nodes:
            if strict and isinstance(node, ast.Attribute):
                names = qualified(node)
                require(not any(name == "sys." + item or name.startswith("sys." + item + ".")
                                for name in names for item in PY_PATH_FIELDS),
                        "CORE_PATH_INJECTION", path, node.lineno, "sys import/path state is forbidden, including aliased access")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if strict:
                    require(not any(alias.name == "*" for alias in node.names), "CORE_DYNAMIC_IMPORT", path, node.lineno,
                            "wildcard imports obscure core/template symbol provenance")
                    for name in names:
                        require(name.split(".")[0] not in PY_LOADERS, "CORE_DYNAMIC_IMPORT", path, node.lineno,
                                f"loader module {name!r} is forbidden, including aliases")
                    if isinstance(node, ast.ImportFrom) and node.module == "sys":
                        require(not any(alias.name in PY_PATH_FIELDS for alias in node.names),
                                "CORE_PATH_INJECTION", path, node.lineno, "importing sys path/import state is forbidden")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.python_module(path, alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                target = self.python_module(path, node.module or "", node.lineno, node.level)
                if target is not None and target.name == "__init__.py":
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        child = self.local([target.parent / (alias.name + ".py"), target.parent / alias.name / "__init__.py"],
                                           path, node.lineno, alias.name)
                        if child is not None:
                            self.owned(child, path, node.lineno)

    def javascript_dependency(self, path, name, line):
        self.module_policy(path, name, "javascript", line)
        if self.entries[path]["layer"] != "H":
            require(name not in {"module", "node:module", "vm", "node:vm"}, "JS_DYNAMIC_IMPORT", path, line,
                    "JavaScript loader modules are forbidden in K/W/vendor")
        require("\\" not in name and "?" not in name and "#" not in name,
                "JS_IMPORT_SYNTAX", path, line, "ambiguous import URL/path syntax is unsupported")
        if ":" in name:
            require(self.external_allowed(path, name, "javascript"), "DEPENDENCY_UNRESOLVED", path, line,
                    f"unapproved external JavaScript module {name!r}")
            return
        if name.startswith("."):
            bases = [self.root / PurePosixPath(path).parent / name]
        else:
            bases = [root / name.lstrip("/") for root in self.search["javascript"]]
        candidates = []
        for base in bases:
            if base.suffix:
                candidates.append(base)
            else:
                candidates.extend(Path(str(base) + suffix) for suffix in JS_SUFFIXES)
                candidates.extend(base / ("index" + suffix) for suffix in JS_SUFFIXES)
        target = self.local(candidates, path, line, name)
        if target is not None:
            self.owned(target, path, line)
        else:
            require(not name.startswith((".", "/")) and self.external_allowed(path, name, "javascript"),
                    "DEPENDENCY_UNRESOLVED", path, line, f"unresolved JavaScript module {name!r}")

    def html_script_dependency(self, path, src, line):
        target = self.html_routes.get((path, src))
        if target is not None:
            self.module_policy(path, src, "javascript", line)
            self.module_policy(path, target, "javascript", line)
            self.owned(self.root / target, path, line)
            return
        require(not src.startswith("/"), "HTML_ROUTE_UNMAPPED", path, line,
                "root-absolute script src needs an exact reviewed source/src route")
        self.javascript_dependency(path, src if src.startswith(".") or ":" in src else "./" + src, line)

    def scan_javascript(self, path, text, line_offset=0):
        _, _, tokens = lex(text, path, line_offset=line_offset)
        computed_keys, literal_keys = javascript_property_key_locations(tokens)
        self.core_tokens(path, [(t.value, t.line) for t in tokens if t.kind == "identifier"],
                         [(t.value, t.line) for t in tokens if t.kind in {"string", "template"}])
        if self.entries[path]["layer"] != "H":
            for offset, token in enumerate(tokens):
                if offset not in computed_keys:
                    continue
                end, depth = offset + 1, 1
                while end < len(tokens) and depth:
                    if tokens[end].kind in {"punct", "member_open"} and tokens[end].value == "[":
                        depth += 1
                    elif tokens[end].kind == "punct" and tokens[end].value == "]":
                        depth -= 1
                    end += 1
                key = tokens[offset + 1:end - 1]
                require(depth == 0 and ((len(key) == 1 and key[0].kind in {"string", "template"})
                                       or javascript_numeric_index(key)),
                        "JS_COMPUTED_KEY_UNSUPPORTED", path, token.line,
                        "computed member keys need one literal string/template or bounded numeric arithmetic; unknown keys are not assumed numeric")
        if self.entries[path]["layer"] in {"K", "vendor"}:
            for offset, token in enumerate(tokens):
                require(token.kind != "identifier" or token.value not in JS_DYNAMIC_NAMES,
                        "JS_DYNAMIC_IMPORT", path, token.line, f"dynamic/global JS entry point {token.value!r} in core")
                require(not (token.kind in {"string", "template"} and token.value in {"require", "eval", "import", "Function"}
                             and (offset in literal_keys or (offset > 0 and offset - 1 in computed_keys))),
                        "JS_DYNAMIC_IMPORT", path, token.line, "computed access to a known JavaScript loader")
        if self.entries[path]["layer"] != "H":
            for offset, token in enumerate(tokens):
                require(not (token.value in JS_REFLECTIVE_NAMES and
                             (token.kind == "identifier" or
                              (token.kind in {"string", "template"} and
                               (offset in literal_keys or (offset > 0 and offset - 1 in computed_keys))))),
                        "JS_REFLECTIVE_LOADER", path, token.line,
                        "reflective function construction/prototype access is outside the static dependency subset")
                require(not (token.value in JS_HTML_WRITER_NAMES and
                             (token.kind == "identifier" or
                              (token.kind in {"string", "template"} and
                               (offset in literal_keys or (offset > 0 and offset - 1 in computed_keys))))),
                        "JS_HTML_WRITER_UNSUPPORTED", path, token.line,
                        "DOM string/attribute writers can create executable documents and are outside the non-host static subset")
        typescript = self.entries[path]["language"] == "typescript"
        index = 0
        while index < len(tokens):
            token = tokens[index]
            value = token.value
            if token.kind != "identifier":
                index += 1
                continue
            if value == "require":
                tail = tokens[index + 1:index + 5]
                require(len(tail) >= 3 and [tail[0].value, tail[2].value] == ["(", ")"]
                        and tail[1].kind == "string" and (index == 0 or tokens[index - 1].value != "."),
                        "JS_DYNAMIC_IMPORT", path, token.line, "require must be an unaliased literal single-argument call")
                self.javascript_dependency(path, tail[1].value, token.line)
                index += 4
                continue
            if value == "import":
                require(index + 1 < len(tokens), "JS_IMPORT_SYNTAX", path, token.line, "unfinished import")
                next_token = tokens[index + 1]
                if next_token.value == "(":
                    tail = tokens[index + 1:index + 4]
                    require(self.entries[path]["layer"] == "H" and len(tail) == 3
                            and tail[1].kind == "string" and tail[2].value == ")"
                            and (path, tail[1].value) in self.javascript_routes,
                            "JS_DYNAMIC_IMPORT", path, token.line,
                            "import() requires an exact H-only route and one literal argument")
                    self.owned(self.root / self.javascript_routes[(path, tail[1].value)], path, token.line)
                    index += 4
                    continue
                require(next_token.value not in {"(", "."}, "JS_DYNAMIC_IMPORT", path, token.line,
                        "dynamic import/import.meta is outside the static dependency subset")
                if next_token.kind == "string":
                    end = index + 2
                    name = next_token.value
                else:
                    end = index + 1
                    while end < len(tokens) and tokens[end].value not in {"from", ";", "="}:
                        require(tokens[end].kind == "identifier" or tokens[end].value in {"{", "}", ",", "*"},
                                "JS_IMPORT_SYNTAX", path, tokens[end].line, "unsupported static import clause")
                        end += 1
                    require(end + 1 < len(tokens) and tokens[end].value == "from" and tokens[end + 1].kind == "string",
                            "JS_IMPORT_SYNTAX", path, token.line, "static import requires a literal from source")
                    require(static_js_clause(tokens[index + 1:end], typescript),
                            "JS_IMPORT_SYNTAX", path, token.line, "unsupported static import bindings")
                    name, end = tokens[end + 1].value, end + 2
                require(end == len(tokens) or (tokens[end].value not in {"with", "assert"}
                        and (tokens[end].value == ";" or tokens[end].line > tokens[end - 1].line)),
                        "JS_IMPORT_SYNTAX", path, token.line, "import attributes/assertions or trailing syntax need a parser")
                self.javascript_dependency(path, name, token.line)
                index = end
                continue
            export_start = index + 1
            if typescript and export_start < len(tokens) and tokens[export_start].value == "type":
                export_start += 1
            if value == "export" and export_start < len(tokens) and tokens[export_start].value in {"*", "{"}:
                end = export_start + 1
                if tokens[export_start].value == "{":
                    while end < len(tokens) and tokens[end].value != "}":
                        require(tokens[end].kind == "identifier" or tokens[end].value == ",",
                                "JS_IMPORT_SYNTAX", path, tokens[end].line, "unsupported re-export clause")
                        end += 1
                    require(end < len(tokens), "JS_IMPORT_SYNTAX", path, token.line, "unfinished re-export")
                    end += 1
                    require(named_js_clause(tokens[export_start:end], typescript),
                            "JS_IMPORT_SYNTAX", path, token.line, "unsupported re-export bindings")
                elif end < len(tokens) and tokens[end].value == "as":
                    require(end + 1 < len(tokens) and tokens[end + 1].kind == "identifier",
                            "JS_IMPORT_SYNTAX", path, token.line, "star re-export alias must be an identifier")
                    end += 2
                if end < len(tokens) and tokens[end].value == "from":
                    require(end + 1 < len(tokens) and tokens[end + 1].kind == "string",
                            "JS_IMPORT_SYNTAX", path, token.line, "re-export source must be literal")
                    self.javascript_dependency(path, tokens[end + 1].value, token.line)
                    end += 2
                else:
                    require(tokens[export_start].value == "{", "JS_IMPORT_SYNTAX", path, token.line, "star export needs from")
                require(end == len(tokens) or (tokens[end].value not in {"with", "assert"}
                        and (tokens[end].value == ";" or tokens[end].line > tokens[end - 1].line)),
                        "JS_IMPORT_SYNTAX", path, token.line, "unsupported trailing re-export syntax")
                index = end
                continue
            index += 1

    def scan_html(self, path, text):
        scanner = self
        class Scripts(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.script = None
                self.embeds = set()
            def handle_starttag(self, tag, attrs):
                line = self.getpos()[0]
                names = [key for key, _ in attrs]
                require(len(names) == len(set(names)), "HTML_SCRIPT_SYNTAX", path, line, "duplicate attributes are ambiguous")
                values = dict(attrs)
                require(tag != "base" or "href" not in values, "HTML_BASE_URL_UNSUPPORTED", path, line,
                        "base href changes dependency resolution and is outside the static HTML subset")
                require("srcdoc" not in values, "HTML_SRCDOC_UNSUPPORTED", path, line,
                        "srcdoc embeds a separately parsed executable document and is outside the static HTML subset")
                require(tag not in {"frame", "object", "embed"}, "HTML_EMBED_UNSUPPORTED", path, line,
                        "embedded document/plugin elements require a separate source and execution context parser")
                if tag == "iframe":
                    scanner.html_embed_dependency(path, values, line)
                    require(values["id"] not in self.embeds, "HTML_EMBED_ROUTE_DUPLICATE", path, line, "duplicate routed iframe id")
                    self.embeds.add(values["id"])
                for key, value in attrs:
                    if key.startswith("on") and value:
                        scanner.scan_javascript(path, value, line - 1)
                    elif value:
                        # Browser URL preprocessing removes embedded ASCII tab /
                        # CR / LF and trims leading/trailing C0 controls + space.
                        url_value = value.translate({9: None, 10: None, 13: None}).strip("".join(map(chr, range(33))))
                        if url_value.lower().startswith("javascript:"):
                            scanner.scan_javascript(path, url_value.split(":", 1)[1], line - 1)
                if tag != "script":
                    return
                require(self.script is None, "HTML_SCRIPT_SYNTAX", path, line, "nested script tag")
                kind = (values.get("type") or "").strip().lower()
                executable = kind in {"", "module", "text/javascript", "application/javascript"}
                require(executable or kind in {"application/json", "application/ld+json"},
                        "HTML_SCRIPT_TYPE", path, line, "unsupported script type/import map")
                src = values.get("src")
                if executable and "src" in values:
                    require(isinstance(src, str) and bool(src), "HTML_SCRIPT_SYNTAX", path, line, "empty script src")
                    scanner.html_script_dependency(path, src, line)
                self.script = {"executable": executable, "src": src, "line": line, "data": []}
            def handle_data(self, data):
                if self.script is not None:
                    self.script["data"].append((self.getpos()[0], data))
            def handle_endtag(self, tag):
                if tag != "script" or self.script is None:
                    return
                script, self.script = self.script, None
                if script["executable"]:
                    body = "".join(value for _, value in script["data"])
                    require(not script["src"] or not body.strip(), "HTML_SCRIPT_SYNTAX", path, script["line"],
                            "src plus inline code is ambiguous for this gate")
                    if not script["src"] and script["data"]:
                        scanner.scan_javascript(path, body, script["data"][0][0] - 1)
        parser = Scripts()
        parser.feed(text)
        parser.close()
        require(parser.embeds == {element for source, element in self.html_embed_routes if source == path},
                "HTML_EMBED_ROUTE_MISSING", path, 1, "declared iframe route must match exactly one actual element")
        require(parser.script is None, "HTML_SCRIPT_SYNTAX", path, parser.script["line"] if parser.script else 1,
                "unclosed script element")

    def directions(self):
        outgoing = {}
        for edge in sorted(set(self.result.edges)):
            outgoing.setdefault(edge.source, []).append(edge)
        for origin in sorted(self.entries):
            origin_layer = self.entries[origin]["layer"]
            if origin_layer == "H":
                continue
            queue, seen = deque([(origin, (origin,))]), {origin}
            try:
                while queue:
                    source, chain = queue.popleft()
                    for edge in outgoing.get(source, []):
                        layer = self.entries[edge.target]["layer"]
                        require(layer in ALLOWED[origin_layer]
                                and (edge.target not in self.trusted_vendor or origin_layer == "H"),
                                "LAYER_DIRECTION", edge.source, edge.line,
                                f"{origin_layer} source reaches {layer} through a local dependency",
                                f"{origin_layer} -> {layer}", chain + (edge.target,))
                        if edge.target not in seen:
                            seen.add(edge.target)
                            queue.append((edge.target, chain + (edge.target,)))
            except ContractError as error:
                self.result.diagnostics.append(error.diagnostic)

    def run(self):
        try:
            self.validate_manifest()
        except ContractError as error:
            self.result.diagnostics.append(error.diagnostic)
            return self.result
        for path in sorted(self.entries):
            try:
                raw = self.safe(path).read_bytes()
                require(b"\x00" not in raw, "SOURCE_ENCODING", path, 1, "NUL bytes are not silently truncated")
                text = raw.replace(b"\r\n", b"\n").decode("utf-8")
                require("\r" not in text, "SOURCE_ENCODING", path, 1, "unsupported bare CR line endings")
                if path in self.trusted_vendor:
                    continue  # Explicit H-only, per-file digest-locked trust boundary; never a parse claim.
                language = self.entries[path]["language"]
                require(language not in {"jsx", "tsx", "cpp"}, "UNSUPPORTED_LANGUAGE", path, 1,
                        f"{language} source was inventoried but needs a dedicated parser")
                if language == "c":
                    self.scan_c(path, text)
                elif language == "python":
                    self.scan_python(path, text)
                elif language in {"javascript", "typescript"}:
                    self.scan_javascript(path, text)
                elif language == "html":
                    self.scan_html(path, text)
            except ContractError as error:
                self.result.diagnostics.append(error.diagnostic)
            except (OSError, UnicodeError) as error:
                self.result.diagnostics.append(Diagnostic(path, 1, "SOURCE_READ", str(error)))
        self.directions()
        self.result.edges = sorted(set(self.result.edges))
        self.result.diagnostics = sorted(set(self.result.diagnostics))
        return self.result


def scan(root, manifest):
    """Read a real file tree; never import, execute, compile or write its source."""
    return Scanner(root, manifest).run()


def load_manifest(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "MANIFEST_DUPLICATE_KEY", str(path), 1, f"duplicate JSON key {key!r}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = scan(args.root, load_manifest(args.manifest))
    except ContractError as error:
        result = ScanResult(diagnostics=[error.diagnostic])
    except (OSError, ValueError) as error:
        result = ScanResult(diagnostics=[Diagnostic(str(args.manifest), 1, "MANIFEST_READ", str(error))])
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
