# Architecture dependency manifest

`architecture_contract.py` is a read-only source inventory and dependency gate.
It never imports, executes, builds, or rewrites the product sources it inspects.
Run it against a reviewed manifest and a frozen product checkout:

```text
python -B tests/architecture_contract.py --root <checkout> --manifest <manifest.json>
python -B tests/test_architecture_contract.py
```

The CLI emits JSON and exits 0 only when the declared inventory, source checks,
and dependency directions pass. A passing synthetic test suite is not evidence
that a particular product manifest passes. A passing product scan is not proof
of arbitrary runtime behavior, correct owner assignments, complete extraction,
shared algorithm reuse, or a successful build without a template.

## Inventory and routes

The schema is `geometry-architecture/1`. The module docstring lists its exact
keys. Unknown keys and duplicate JSON keys are rejected.

- `sourceRoots` inventories complete directories recursively. `sourceFiles`
  optionally inventories exact standalone files without pulling their siblings
  into the product. A file cannot overlap a root. This permits explicit runtime
  dependencies such as a helper physically located under `tests/`.
- Every executable source needs one exact `sources` entry with `path`, `layer`,
  `language`, and `purpose`, or one exact `exclusions` entry with `path`, `reason`,
  and its current `sha256`. Importing an exclusion is an error.
- Exclusions default to raw-byte hashing. An explicit `hashMode: "lf"` permits
  only CRLF-to-LF normalization before hashing, so the same excluded text can
  be checked out on Windows and Linux. Bare CR bytes, all other whitespace,
  and every content character remain significant. Unknown modes are rejected.
- Every `vendor` source also requires its own current raw-byte `sha256`.
  Vendor entries cannot declare any `hashMode`; vendor bytes are always exact.
  Directory-wide vendor or exclusion exemptions do not exist.
- Paths are repository-relative POSIX paths. Escapes, source symlinks, missing
  sources, duplicate or case-colliding ownership, and unregistered source files
  are rejected. Search roots do not grant ownership.
- `htmlScriptRoutes` contains exact `{source, src, target, purpose}` entries.
  `source` is one owned HTML file and `target` one owned JavaScript file. The
  `(source, src)` pair takes precedence over ordinary relative file resolution.
  Unmapped root-absolute script URLs fail. Routes produce normal graph edges.
- `javascriptImportRoutes` contains exact
  `{source, specifier, target, purpose}` entries. Only an owned H source can
  declare one. It permits that source's single-literal-argument `import()` and
  produces a normal graph edge. Unmapped imports, computed strings, template
  arguments, and import options remain rejected. The same URL in another
  source does not inherit this allowance.

## Layer checks and trusted browser libraries

| Origin | Reachable owned sources |
| --- | --- |
| K | K only |
| W | K, W, ordinary scanned vendor |
| H | K, W, H, vendor |
| Ordinary scanned vendor | Ordinary scanned vendor only |

The gate checks transitive reachability from every non-host origin. Diagnostics
identify the source line, direction, and complete dependency chain. K cannot
reach even an immutable vendor file. A K helper does not hide that dependency.

`trustedVendorBundles` is an explicit exception to parsing third-party browser
code, not an exception to ownership, hashing, or layer boundaries. Each entry
has a distinct `id`, a concrete `purpose`, exact `files`, and `layers: ["H"]`.
Every file must already be an owned, digest-locked JavaScript vendor source.
When this option is used, every vendor file must occur in exactly one bundle.
New files still require inventory entries; omitted, duplicate, missing, changed,
or unlocked vendor files fail validation.

These bundles are **only reachable from H**. W, K, their helpers, and untrusted
vendor cannot reach them. Their internal code, loading behavior, and runtime
dependencies are trusted and are **not statically proved by this scanner**.
The JSON result lists them under `trustedSourcesNotParsed`; an empty diagnostics
array must not be presented as a successful parse of those files. The reviewed
bundle inventory, raw digests, and H-only integration are the trust boundary.

## External policy and parsing limits

`policy.cSystemHeaders` can contain only names from the scanner's built-in
standard C header set. A manifest cannot promote `windows.h`, an arbitrary
vendor header, or a platform SDK to a core standard library. Platform/compiler
headers can be listed individually in `externalModules` with `language: "c"`,
`layers: ["H"]`, and a concrete purpose. This allowance is exact and cannot be
used by K or its helpers. Python standard-library roots and explicit `node:`
builtins are likewise validated. Third-party external modules are H-only.

C includes in all conditional branches are followed. Macro includes and other
unsupported loaders fail closed. Python uses AST imports, regular package
initializers, and conservative loader/path-injection checks. JavaScript uses a
conservative lexer: template interpolations are scanned recursively, while
literal display chunks, strings, regex bodies, and comments are not executable
identifiers. Their delimiters cannot end an interpolation. Unsupported lexical
forms, ambiguous slash contexts, unfinished nesting, import assertions, and
unapproved loaders fail closed. JSX/TSX and C++ are inventoried but need a
dedicated parser before ordinary ownership can pass.

C directive whitespace includes form feed and vertical tab. Executable `%:`
preprocessor digraphs, including digraph token pasting, are explicitly rejected;
their appearances in comments or string literals are display text. A Python
module has dependency edges to its own regular-package initializers even if
only H imports that module or the module body contains no import. Simple,
annotated, and named-expression assignments preserve imported alias provenance.
C trigraphs are rejected before any comment/literal processing, including when
they appear in comments or strings: C replaces them in an earlier translation
phase. Python tuple/list/starred unpacking, container values, indexed container
selection, and loop bindings conservatively retain all possible imported alias
provenance. Assigning `sys` provenance through an attribute/subscript target is
explicitly unsupported. This is bounded syntax handling with a
conservative alias union, not a proof of arbitrary Python dataflow.

JavaScript executable identifiers currently use the ASCII subset. Non-ASCII
executable tokens are rejected by name rather than guessed to be punctuation;
Unicode comments, literal strings, template display chunks, and regex content
remain supported. U+2028 and U+2029 terminate line comments and contribute to
reported line numbers. Known reflective function/prototype entry points,
including direct and literal-computed `constructor` access, are rejected in
K, W, and ordinary vendor sources. These checks do not prove arbitrary dynamic
program semantics or replace the separately required runtime isolation gate.

For K/W/ordinary vendor JavaScript, a computed member key must be either one
literal string, one non-interpolated template, or a bounded numeric expression.
Normal array literals, array defaults, destructuring parameters, and numeric
indices such as `[0]` remain distinct from computed property selection. The
numeric grammar supports numeric literals, parentheses, unary `+/-/~`, numeric
increments, `- * / % **`, and bitwise operations. Binary `+` requires both
operands to be numeric: `[+i + 1]`, `[i - 1]` and `[i | 0]` are supported, while
bare `[i]` is not presumed numeric and `[i + 1]` remains unknown. Calls, comma
operators, conditionals, interpolated keys, string assembly, and parenthesized
string keys are explicitly unsupported. Unknown keys produce
`JS_COMPUTED_KEY_UNSUPPORTED`; they are not mislabeled as known reflection.
H retains its documented host runtime boundary; this restriction does not
claim to statically verify arbitrary host effects.

HTML `<base href>` is explicitly unsupported because it changes relative URL
resolution, including URLs used by inline code. An exact script route does not
exempt it. URL attributes use browser-style ASCII tab/CR/LF removal and C0/space
trimming before `javascript:` detection, then scan the normalized script body.
An HTML `srcdoc` attribute is unsupported even when empty or on an H source,
because its document needs a separate parsing/resolution context. K/W/ordinary
vendor JavaScript also rejects the known DOM writers `srcdoc`, `innerHTML`,
`outerHTML`, `insertAdjacentHTML`, `setAttribute`, and `setAttributeNS`, including
literal-computed member names. This deliberately includes attribute setters
whose arguments could install `srcdoc`; display strings remain permitted.

The policy's exact forbidden identifiers and strings still need responsibility
review against the actual template APIs and specification keys. Common neutral
geometry words must not be banned merely because a template also uses them.
All source roots, exclusions, ownership decisions, external allowances, and
trusted bundles are review inputs, not facts inferred from a green scan.
