"""GitHub Actions expression 的最小求值器（重演用）。

支援：字面值（'str'、數字、true/false/null）、屬性存取 a.b.c 與 a['b'] / a[0]、
!、==、!=、<、<=、>、>=、&&、||、括號，以及 format、contains、startsWith、endsWith、
fromJSON、toJSON、join、always、cancelled、success、failure。
比較規則照 GitHub 文件：字串比較不分大小寫；型別不同時轉成數字（null→0、bool→1/0、字串→數字或 NaN）。
"""
import json
import math
import re

TOKEN = re.compile(r"\s*(?:(?P<num>-?\d+(?:\.\d+)?)|(?P<str>'(?:[^']|'')*')|(?P<op>==|!=|<=|>=|&&|\|\||[!<>()\[\],.*])|(?P<id>[A-Za-z_][A-Za-z0-9_-]*))")


def tokenize(s):
    pos, out = 0, []
    s = s.strip()
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise ValueError(f"無法解析：{s[pos:pos+30]!r}")
        pos = m.end()
        for k in ("num", "str", "op", "id"):
            if m.group(k) is not None:
                out.append((k, m.group(k)))
                break
    return out


def to_num(v):
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        if v.strip() == "":
            return 0.0
        try:
            return float(v)
        except ValueError:
            return math.nan
    return math.nan


def truthy(v):
    if v is None or v is False:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return not (v == 0 or math.isnan(v))
    if isinstance(v, str):
        return v != ""
    return True


def eq(a, b):
    if isinstance(a, str) and isinstance(b, str):
        return a.lower() == b.lower()
    if type(a) is type(b) and not isinstance(a, (str, int, float, bool)) and a is not None:
        return a is b
    x, y = to_num(a), to_num(b)
    return x == y


def to_str(v):
    if v is None:
        return ""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (dict, list)):
        return "Object" if isinstance(v, dict) else "Array"
    return str(v)


class Ctx:
    def __init__(self, data, status=None):
        self.data = data            # 頂層 context：github、inputs、needs、steps…
        self.status = status or {}  # always/cancelled/success/failure 的依據


class Parser:
    def __init__(self, toks, ctx):
        self.t, self.i, self.ctx = toks, 0, ctx

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, val=None):
        tok = self.peek()
        if val is not None and tok[1] != val:
            raise ValueError(f"預期 {val}，得到 {tok}")
        self.i += 1
        return tok

    def parse(self):
        v = self.or_()
        if self.i != len(self.t):
            raise ValueError(f"多餘的 token：{self.t[self.i:]}")
        return v

    def or_(self):
        v = self.and_()
        while self.peek()[1] == "||":
            self.take()
            r = self.and_()
            v = v if truthy(v) else r
        return v

    def and_(self):
        v = self.cmp()
        while self.peek()[1] == "&&":
            self.take()
            r = self.cmp()
            v = r if truthy(v) else v
        return v

    def cmp(self):
        v = self.unary()
        while self.peek()[1] in ("==", "!=", "<", "<=", ">", ">="):
            op = self.take()[1]
            r = self.unary()
            if op == "==":
                v = eq(v, r)
            elif op == "!=":
                v = not eq(v, r)
            else:
                x, y = to_num(v), to_num(r)
                v = {"<": x < y, "<=": x <= y, ">": x > y, ">=": x >= y}[op]
        return v

    def unary(self):
        if self.peek()[1] == "!":
            self.take()
            return not truthy(self.unary())
        return self.postfix()

    def postfix(self):
        v = self.primary()
        while True:
            k, val = self.peek()
            if val == ".":
                self.take()
                name = self.take()
                if name[1] == "*":
                    v = list(v.values()) if isinstance(v, dict) else []
                else:
                    v = prop(v, name[1])
            elif val == "[":
                self.take()
                key = self.or_()
                self.take("]")
                if isinstance(v, list):
                    idx = int(to_num(key))
                    v = v[idx] if 0 <= idx < len(v) else None
                else:
                    v = prop(v, to_str(key))
            else:
                return v

    def primary(self):
        k, val = self.take()
        if k == "num":
            return float(val)
        if k == "str":
            return val[1:-1].replace("''", "'")
        if val == "(":
            v = self.or_()
            self.take(")")
            return v
        if k == "id":
            low = val.lower()
            if low == "true":
                return True
            if low == "false":
                return False
            if low == "null":
                return None
            if self.peek()[1] == "(":
                self.take()
                args = []
                if self.peek()[1] != ")":
                    args.append(self.or_())
                    while self.peek()[1] == ",":
                        self.take()
                        args.append(self.or_())
                self.take(")")
                return call(low, args, self.ctx)
            return self.ctx.data.get(val)
        raise ValueError(f"非預期的 token {val!r}")


def prop(v, name):
    if isinstance(v, dict):
        for k in v:
            if k.lower() == name.lower():
                return v[k]
        return None
    if isinstance(v, list):  # 物件篩選後的屬性存取
        return [prop(x, name) for x in v]
    return None


def call(name, args, ctx):
    st = ctx.status
    if name == "always":
        return True
    if name == "cancelled":
        return bool(st.get("cancelled"))
    if name == "success":
        return not st.get("cancelled") and all(r == "success" for r in st.get("needs", []))
    if name == "failure":
        return any(r == "failure" for r in st.get("needs", []))
    if name == "format":
        fmt = to_str(args[0])
        return re.sub(r"\{(\d+)\}", lambda m: to_str(args[int(m.group(1)) + 1]), fmt.replace("{{", "\0").replace("}}", "\1")).replace("\0", "{").replace("\1", "}")
    if name == "contains":
        hay, needle = args
        if isinstance(hay, list):
            return any(eq(x, needle) for x in hay)
        return to_str(needle).lower() in to_str(hay).lower()
    if name == "startswith":
        return to_str(args[0]).lower().startswith(to_str(args[1]).lower())
    if name == "endswith":
        return to_str(args[0]).lower().endswith(to_str(args[1]).lower())
    if name == "fromjson":
        return json.loads(to_str(args[0]))
    if name == "tojson":
        return json.dumps(args[0])
    if name == "join":
        sep = to_str(args[1]) if len(args) > 1 else ","
        return sep.join(to_str(x) for x in (args[0] if isinstance(args[0], list) else [args[0]]))
    raise ValueError(f"不支援的函式 {name}")


def evaluate(expr, ctx):
    return Parser(tokenize(expr), ctx).parse()


def uses_status(expr):
    return bool(re.search(r"\b(always|cancelled|success|failure)\s*\(", expr))


def eval_if(expr, ctx):
    """job／step 的 if：沒有狀態函式時隱含 success() &&。"""
    if expr is None:
        return call("success", [], ctx)
    expr = str(expr).strip()
    if expr.startswith("${{") and expr.endswith("}}"):
        expr = expr[3:-2]
    v = evaluate(expr, ctx)
    if not uses_status(expr):
        return call("success", [], ctx) and truthy(v)
    return truthy(v)


def render(s, ctx):
    """把字串裡的 ${{ … }} 換成求值結果（env、with、outputs 用）。"""
    if not isinstance(s, str):
        return to_str(s) if not isinstance(s, (dict, list)) else s
    return re.sub(r"\$\{\{(.*?)\}\}", lambda m: to_str(evaluate(m.group(1), ctx)), s, flags=re.S)
