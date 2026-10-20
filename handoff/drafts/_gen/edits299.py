# -*- coding: utf-8 -*-
"""Edits for issue #299 (I22 W: V_EXTENSION names the locating edge and the exceeded interval)."""
import re

NATIVE = "geometry-templates/woodworking/native/"


def pyq(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"


CONTACTS_OLD = '''bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
)
{
    if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&
        (span_lo < edge_lo || span_hi > edge_hi)) {
        if (err != NULL) {
            snprintf(err, err_cap,
                     "V_EXTENSION：非 boundary 角材（%u）的 "
                     "footprint 超出定位邊範圍", (unsigned)self->id);
        }
        return false;
    }
    return true;
}
'''

# NOTE: no comment may sit inside this function: tests/test_geo261_wood_contacts.py compares the
# comment-stripped definition against the original source text (mutant()).
CONTACTS_NEW = '''/* I22 (W): a non-boundary member must stay inside its locating edge. The refusal keeps the
 * original wording as an exact prefix and then names the locating edge ("e<edge_index>" and its
 * interval on the length axis) and each exceeded interval: the low end [span_lo,edge_lo] and/or
 * the high end [edge_hi,span_hi], all in mm. Capacity, truncation and err==NULL behave as before. */
bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge, int edge_index,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
)
{
    if (has_edge && self->role != WOOD_MEMBER_ROLE_BOUNDARY &&
        (span_lo < edge_lo || span_hi > edge_hi)) {
        if (err != NULL) {
            char low_note[64] = "", high_note[64] = "";
            if (edge_lo > span_lo) {
                snprintf(low_note, sizeof low_note, "，低端超出 [%lld,%lld] mm",
                         (long long)span_lo, (long long)edge_lo);
            }
            if (edge_hi < span_hi) {
                snprintf(high_note, sizeof high_note, "，高端超出 [%lld,%lld] mm",
                         (long long)edge_hi, (long long)span_hi);
            }
            snprintf(err, err_cap,
                     "V_EXTENSION：非 boundary 角材（%u）的 "
                     "footprint 超出定位邊範圍"
                     "——定位邊 e%d [%lld,%lld] mm%s%s",
                     (unsigned)self->id, edge_index,
                     (long long)edge_lo, (long long)edge_hi, low_note, high_note);
        }
        return false;
    }
    return true;
}
'''

HARNESS_SPAN_OLD_CONST = '''static const char SPAN_ERROR[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍";
'''
HARNESS_SPAN_NEW_CONST = '''#define EDGE 5
static const char SPAN_LEGACY_PREFIX[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍";
static const char SPAN_ERROR[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e5 [0,100] mm，低端超出 [-1,0] mm";
static const char SPAN_HIGH_ERROR[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e5 [0,100] mm，高端超出 [100,101] mm";
static const char SPAN_BOTH_ERROR[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e5 [0,100] mm，低端超出 [-3,0] mm，高端超出 [100,104] mm";
'''

HARNESS_SPAN_FN_NEW = '''static int span(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    char err[512] = "unchanged";
    CHECK("span-no-edge", wood_member_span_extension_check(&self,false,EDGE,-1,101,0,100,err,sizeof err));
    CHECK("span-accept-output-unchanged", !strcmp(err,"unchanged"));
    self.role = WOOD_MEMBER_ROLE_BOUNDARY;
    CHECK("span-boundary-extension", wood_member_span_extension_check(&self,true,EDGE,-1,101,0,100,err,sizeof err));
    self.role = WOOD_MEMBER_ROLE_PRIMARY;
    CHECK("span-touch-equality", wood_member_span_extension_check(&self,true,EDGE,0,100,0,100,err,sizeof err));
    CHECK("span-contained", wood_member_span_extension_check(&self,true,EDGE,1,99,0,100,err,sizeof err));
    CHECK("span-low-refusal", !wood_member_span_extension_check(&self,true,EDGE,-1,100,0,100,err,sizeof err));
    CHECK("span-error-exact", !strcmp(err,SPAN_ERROR));
    CHECK("span-legacy-prefix", !strncmp(err,SPAN_LEGACY_PREFIX,strlen(SPAN_LEGACY_PREFIX)));
    CHECK("span-high-refusal", !wood_member_span_extension_check(&self,true,EDGE,0,101,0,100,NULL,0));
    CHECK("span-high-refusal-message", !wood_member_span_extension_check(&self,true,EDGE,0,101,0,100,err,sizeof err));
    CHECK("span-high-error-exact", !strcmp(err,SPAN_HIGH_ERROR));
    CHECK("span-both-refusal", !wood_member_span_extension_check(&self,true,EDGE,-3,104,0,100,err,sizeof err));
    CHECK("span-both-error-exact", !strcmp(err,SPAN_BOTH_ERROR));
    self.role = (WoodMemberRole)-7;
    CHECK("span-unknown-role-not-boundary", !wood_member_span_extension_check(&self,true,EDGE,0,101,0,100,NULL,0));
    return 0;
}
'''

HARNESS_EQ_OLD = '''        a = wood_member_span_extension_check(&self,has_edge,lo,hi,0,20,actual,cap);
        e = frozen_span_extension_check(&self,has_edge,lo,hi,0,20,expected,cap);
        CHECK("frozen-span-verdict-and-bytes", a == e && !memcmp(actual,expected,sizeof actual));
'''
HARNESS_EQ_NEW = '''        a = wood_member_span_extension_check(&self,has_edge,EDGE,lo,hi,0,20,actual,cap);
        e = frozen_span_extension_check(&self,has_edge,lo,hi,0,20,expected,cap);
        /* #299 appends the locating edge and the exceeded interval(s) to the frozen wording: the verdict
         * is identical, a truncating capacity cuts both texts at the same byte, and a full-size refusal
         * keeps the frozen text as an exact, strictly shorter prefix. */
        if (a == e && !a && cap == sizeof actual) {
            CHECK("frozen-span-verdict-and-prefix", !strncmp(actual,expected,strlen(expected)) && strlen(actual) > strlen(expected));
        } else {
            CHECK("frozen-span-verdict-and-bytes", a == e && !memcmp(actual,expected,sizeof actual));
        }
'''

MUTANT_SOURCE = NATIVE + "contacts.c"


def mutants299(contacts_new):
    """(id, desc, file, old, new) for M89-M96. Anchors are cut from the real new text."""
    fmt_line = '"——定位邊 e%d [%lld,%lld] mm%s%s",\n                     (unsigned)self->id, edge_index,'
    assert contacts_new.count(fmt_line) == 1
    all_args = fmt_line + '\n                     (long long)edge_lo, (long long)edge_hi, low_note, high_note);'
    assert contacts_new.count(all_args) == 1
    return [
        ("M89", "I22/#299：V_EXTENSION 訊息的料件欄位拿掉(角材編號固定印成 0)；p8、p8b、_role_priority_mutant 必轉紅",
         MUTANT_SOURCE, "(unsigned)self->id, edge_index,", "0u, edge_index,"),
        ("M90", "I22/#299：V_EXTENSION 訊息拿掉定位邊編號 e<i>；p8、p8b 必轉紅",
         MUTANT_SOURCE, fmt_line,
         '"——定位邊 [%lld,%lld] mm%s%s",\n                     (unsigned)self->id,'),
        ("M91", "I22/#299：V_EXTENSION 訊息拿掉定位邊區間 [edge_lo,edge_hi] mm；p8、p8b 必轉紅",
         MUTANT_SOURCE, all_args,
         '"——定位邊 e%d%s%s",\n                     (unsigned)self->id, edge_index,\n                     low_note, high_note);'),
        ("M92", "I22/#299：V_EXTENSION 訊息拿掉「低端超出」區間；凹角在定位邊低端的 _s1_p8 必轉紅",
         MUTANT_SOURCE, "if (edge_lo > span_lo) {", "if (0) {"),
        ("M93", "I22/#299：V_EXTENSION 訊息拿掉「高端超出」區間；凹角在定位邊高端的 _s1_p8b 必轉紅",
         MUTANT_SOURCE, "if (edge_hi < span_hi) {", "if (0) {"),
        ("M94", "I22/#299：V_EXTENSION 訊息的「低端超出」不論有沒有超出都印(多印一段假區間)；_s1_p8b 的 error_not 必轉紅",
         MUTANT_SOURCE, "if (edge_lo > span_lo) {", "if (1) {"),
        ("M95", "I22/#299：V_EXTENSION 訊息的「高端超出」不論有沒有超出都印(多印一段假區間)；_s1_p8 的 error_not 必轉紅",
         MUTANT_SOURCE, "if (edge_hi < span_hi) {", "if (1) {"),
        ("M96", "I22/#299：W 的 wood_contact_boundary_edge 不回報定位邊編號(訊息印成 e-1)；p8、p8b 必轉紅",
         NATIVE + "contact_world.c", "if(out_edge)*out_edge=edge;", "(void)edge;"),
    ]


def render_mutants(items):
    out = ["    # I22/#299：V_EXTENSION 訊息逐欄位的牙齒。contacts.c 的 snprintf 與兩段 clause 各拿掉一個欄位，\n",
           "    # contact_world.c 的定位邊編號回報一個；判定在 run_tests.py 的 p8、p8b(error 清單 + error_not)。\n"]
    for mid, desc, file, old, new in items:
        out.append('    dict(id="%s", desc="%s",\n' % (mid, desc))
        out.append('         file="%s",\n' % file)
        out.append("         old=%s,\n" % pyq(old))
        out.append("         new=%s),\n" % pyq(new))
    return "".join(out)


def e299(t):
    # ---- W: contacts ------------------------------------------------------------------------
    t.sub(NATIVE + "contacts.c", CONTACTS_OLD, CONTACTS_NEW)
    t.sub(NATIVE + "contacts.h", '''/* self is the same non-null member supplied to the original placement check.
 * Acceptance leaves err unchanged; refusal preserves the existing wording,
 * truncation and optional err==NULL behavior. */
bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
);
''', '''/* self is the same non-null member supplied to the original placement check.
 * Acceptance leaves err unchanged. Refusal keeps the original wording as an
 * exact prefix and then names the locating edge ("e<edge_index>" plus its
 * interval [edge_lo,edge_hi] on the length axis) and each exceeded interval,
 * the low end [span_lo,edge_lo] and/or the high end [edge_hi,span_hi], in mm
 * (I22 W). edge_index is the outline edge id that located the member and is
 * only read when has_edge. Truncation and optional err==NULL behavior are
 * unchanged. */
bool wood_member_span_extension_check(
    const WoodMember *self, bool has_edge, int edge_index,
    GeoCoord span_lo, GeoCoord span_hi, GeoCoord edge_lo, GeoCoord edge_hi,
    char *err, size_t err_cap
);
''')
    # ---- W: contact world -------------------------------------------------------------------
    t.sub(NATIVE + "contact_world.h",
          "bool wood_contact_boundary_interval(const WoodBoundaryRegion *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,GeoCoord *,GeoCoord *);\n",
          "/* The positioning edge of a footprint: its interval on the length axis and its outline edge id (\"e<i>\",\n"
          " * index into the outer loop of the role boundary). out_edge may be NULL; no output is written when no\n"
          " * positioning edge is found. wood_contact_boundary_interval is the same without the id. */\n"
          "bool wood_contact_boundary_edge(const WoodBoundaryRegion *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,GeoCoord *,GeoCoord *,int *);\n"
          "bool wood_contact_boundary_interval(const WoodBoundaryRegion *,bool,GeoCoord,GeoCoord,GeoCoord,GeoCoord,GeoCoord *,GeoCoord *);\n")
    cw = NATIVE + "contact_world.c"
    t.sub(cw, '''bool wood_contact_boundary_interval(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi)
{
    GeoRect2 rect=''', '''bool wood_contact_boundary_edge(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi,int *out_edge)
{
    GeoRect2 rect=''')
    t.sub(cw, '''    *out_hi=along_v?contact_max(a.v,b.v):contact_max(a.u,b.u);return true;
}
''', '''    *out_hi=along_v?contact_max(a.v,b.v):contact_max(a.u,b.u);if(out_edge)*out_edge=edge;return true;
}
bool wood_contact_boundary_interval(const WoodBoundaryRegion *boundary,bool along_v,
    GeoCoord span_lo,GeoCoord span_hi,GeoCoord cross_lo,GeoCoord cross_hi,GeoCoord *out_lo,GeoCoord *out_hi)
{return wood_contact_boundary_edge(boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,out_lo,out_hi,NULL);}
''')
    t.sub(cw, '''    GeoCoord edge_lo=0,edge_hi=0;bool has_edge=wood_contact_boundary_interval(world->role_boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,&edge_lo,&edge_hi);
    if(!wood_member_span_extension_check(self,has_edge,span_lo,span_hi,edge_lo,edge_hi,error,cap))return false;
''', '''    GeoCoord edge_lo=0,edge_hi=0;int edge_index=-1;
    bool has_edge=wood_contact_boundary_edge(world->role_boundary,along_v,span_lo,span_hi,cross_lo,cross_hi,&edge_lo,&edge_hi,&edge_index);
    if(!wood_member_span_extension_check(self,has_edge,edge_index,span_lo,span_hi,edge_lo,edge_hi,error,cap))return false;
''')
    # ---- W unit harnesses --------------------------------------------------------------------
    ch = "tests/geo261_contacts_harness.c"
    t.sub(ch, HARNESS_SPAN_OLD_CONST, HARNESS_SPAN_NEW_CONST)
    text = t.get(ch)
    a = text.index("static int span(void)\n")
    b = text.index("static int kinds(void)\n")
    t.put(ch, text[:a] + HARNESS_SPAN_FN_NEW + "\n" + text[b:])
    t.sub(ch, "ok = wood_member_span_extension_check(&self,true,-1,100,0,100,err,cap);",
          "ok = wood_member_span_extension_check(&self,true,EDGE,-1,100,0,100,err,cap);")
    t.sub(ch, '''    CHECK("full-id-refusal", !wood_member_span_extension_check(&self,true,-1,100,0,100,err,sizeof err));
    CHECK("full-id-text", !strcmp(err,"V_EXTENSION：非 boundary 角材（4294967295）的 footprint 超出定位邊範圍"));
''', '''    CHECK("full-id-refusal", !wood_member_span_extension_check(&self,true,EDGE,-1,100,0,100,err,sizeof err));
    CHECK("full-id-text", !strcmp(err,"V_EXTENSION：非 boundary 角材（4294967295）的 footprint 超出定位邊範圍——定位邊 e5 [0,100] mm，低端超出 [-1,0] mm"));
''')
    t.sub(ch, HARNESS_EQ_OLD, HARNESS_EQ_NEW)

    cwh = "tests/geo261_contact_world_harness.c"
    t.sub(cwh, '''    CHECK("boundary-vertical-numeric-interval",wood_contact_boundary_interval(&b,true,0,100,40,50,&lo,&hi)&&lo==50&&hi==100);
''', '''    CHECK("boundary-vertical-numeric-interval",wood_contact_boundary_interval(&b,true,0,100,40,50,&lo,&hi)&&lo==50&&hi==100);
    {int edge=-7;
        CHECK("boundary-edge-index-horizontal",wood_contact_boundary_edge(&b,false,0,100,40,50,&lo,&hi,&edge)&&edge==2&&lo==50&&hi==100);
        edge=-7;CHECK("boundary-edge-index-vertical",wood_contact_boundary_edge(&b,true,0,100,40,50,&lo,&hi,&edge)&&edge==3&&lo==50&&hi==100);
        edge=-7;lo=-999;hi=-888;CHECK("boundary-edge-failure-leaves-outputs",!wood_contact_boundary_edge(&b,false,0,100,50,60,&lo,&hi,&edge)&&edge==-7&&lo==-999&&hi==-888);
        CHECK("boundary-edge-null-index-accepted",wood_contact_boundary_edge(&b,false,0,100,40,50,&lo,&hi,NULL)&&lo==50&&hi==100);}
''')
    t.sub(cwh, '&&strstr(error,"V_EXTENSION"));',
          '&&!strcmp(error,"V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e2 [50,100] mm，低端超出 [0,50] mm"));')
    t.sub("tests/geo261_host_facts_authority_harness.c",
          '!strcmp(error,"V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍")&&geo_eval_node_count',
          '!strcmp(error,"V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍——定位邊 e2 [50,100] mm，低端超出 [0,50] mm")&&geo_eval_node_count')

    # ---- python guards for W -----------------------------------------------------------------
    wc = "tests/test_geo261_wood_contacts.py"
    t.sub(wc, '''        expected = {
            "wood_member_span_extension_check": "{" + span + " return true; }",
            "wood_member_end_contact_check": "{" + contact.replace("continue;", "return true;") + " return true; }",
        }
''', '''        # I22 W (#299) deliberately extends the V_EXTENSION wording. The frozen decision (the guard) and the
        # frozen wording (as exact literal prefix pieces) must survive unchanged; the added fields are pinned
        # by the span/buffer/equivalence cases of geo261_contacts_harness.c and by the controls below.
        with self.subTest(function="wood_member_span_extension_check"):
            actual = definition(source, "wood_member_span_extension_check")
            body = tokens(actual[actual.index("{") :])
            guard = tokens(span[: span.index("{")])
            self.assertEqual(guard, body[1 : 1 + len(guard)])
            for literal in (item for item in tokens(span) if item.startswith('"')):
                self.assertIn(literal, body)
        expected = {
            "wood_member_end_contact_check": "{" + contact.replace("continue;", "return true;") + " return true; }",
        }
''')
    t.sub(wc, '''            ("span-error", "wood_member_span_extension_check", "err != NULL", "false", "span", "span-error-exact"),
''', '''            ("span-error", "wood_member_span_extension_check", "err != NULL", "false", "span", "span-error-exact"),
            ("span-edge-id", "wood_member_span_extension_check", "(unsigned)self->id, edge_index,", "(unsigned)self->id, 0,", "span", "span-error-exact"),
            ("span-edge-interval", "wood_member_span_extension_check", "(long long)edge_lo, (long long)edge_hi, low_note, high_note);", "(long long)span_lo, (long long)edge_hi, low_note, high_note);", "span", "span-error-exact"),
            ("span-low-clause", "wood_member_span_extension_check", "if (edge_lo > span_lo) {", "if (0) {", "span", "span-error-exact"),
            ("span-high-clause", "wood_member_span_extension_check", "if (edge_hi < span_hi) {", "if (0) {", "span", "span-high-error-exact"),
            ("span-low-always", "wood_member_span_extension_check", "if (edge_lo > span_lo) {", "if (1) {", "span", "span-high-error-exact"),
            ("span-high-always", "wood_member_span_extension_check", "if (edge_hi < span_hi) {", "if (1) {", "span", "span-error-exact"),
''')
    cwp = "tests/test_geo261_wood_contact_world.py"
    t.sub(cwp, "    def test_twenty_actual_guard_controls_fail_the_named_numeric_assertions(self):",
          "    def test_actual_guard_controls_fail_the_named_numeric_assertions(self):")
    t.sub(cwp, '''    ("extension-end", "||ext_end[end]", "", "ends", "self-boundary-extension-end-exempt"),
)''', '''    ("extension-end", "||ext_end[end]", "", "ends", "self-boundary-extension-end-exempt"),
    ("edge-index-output", "if(out_edge)*out_edge=edge;", "(void)edge;", "intervals", "boundary-edge-index-horizontal"),
)''')

    # ---- core oracle: run_tests.py ---------------------------------------------------------
    rt = "tests/run_tests.py"
    t.sub(rt, '''  error:   reject 時,本夾具的「路徑:[行號:]診斷」必須包含此子字串
''', '''  error:   reject 時,本夾具的「路徑:[行號:]診斷」必須包含此子字串;
           也可寫成清單——同一行診斷必須逐項全含(#299:逐欄位釘訊息)
  error_not: reject 時(選填),上述那一行診斷不得含清單中的任何子字串
''')
    t.sub(rt, '''    if spec["expect"] == "reject" and not spec.get("error"):
        return "INFRA rejection requires an explicit expected diagnostic"
''', '''    if spec["expect"] == "reject" and not spec.get("error"):
        return "INFRA rejection requires an explicit expected diagnostic"
    if spec.get("error_not") and spec["expect"] != "reject":
        return "INFRA error_not only applies to a rejection"
''')
    t.sub(rt, '''    if not any(spec["error"] in diagnostic for diagnostic in diagnostics):
        return f"FAIL 錯誤不符: 期望含「{spec['error']}」實得「{first}」"
    return "ok"
''', '''    needles = spec["error"] if isinstance(spec["error"], list) else [spec["error"]]
    forbidden = spec.get("error_not", [])
    if not any(all(n in diagnostic for n in needles) and not any(n in diagnostic for n in forbidden)
               for diagnostic in diagnostics):
        shown = "」且含「".join(needles)
        absent = ("且不含「" + "」「".join(forbidden) + "」") if forbidden else ""
        return f"FAIL 錯誤不符: 期望含「{shown}」{absent}實得「{first}」"
    return "ok"
''')
    t.sub(rt, ''' # 只釘前綴:I22 要求訊息另指名定位邊與超出區間,核心日後補上時不該誤紅。
 {'scene': '_s1_p8_l_room_primary_through_reflex_extension.scene', 'expect': 'reject',
  'error': 'V_EXTENSION：非 boundary 角材（3）'},
 # p8 的高端鏡像:M88 殺手(V_EXTENSION 只驗起點那一半)。
 {'scene': '_s1_p8b_l_room_primary_through_reflex_extension_hi.scene', 'expect': 'reject',
  'error': 'V_EXTENSION：非 boundary 角材（3）'},
''', ''' # I22 W(#299):訊息指名料件、定位邊與超出的區間。error 清單 = 同一行診斷必須逐項全含;error_not = 該行不得出現。
 # p8 = 低端:凹角在定位邊 e3(v 3000..4800)的起點,足跡 v∈[27,4773] → 低端超出 [27,3000],沒有高端超出。
 # M92 殺手 = p8(拿掉低端區間)、M95 殺手 = p8(error_not 擋住無條件多印的高端區間)。
 {'scene': '_s1_p8_l_room_primary_through_reflex_extension.scene', 'expect': 'reject',
  'error': ['V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍',
            '定位邊 e3 [3000,4800] mm',
            '低端超出 [27,3000] mm'],
  'error_not': ['高端超出']},
 # p8 的高端鏡像:定位邊 e1(v 0..1800),足跡同 → 高端超出 [1800,4773],沒有低端超出。
 # M88 殺手(V_EXTENSION 只驗起點那一半)、M93 殺手(拿掉高端區間)、M94 殺手(error_not 擋住無條件多印的低端區間)。
 # M89–M91、M96(料件、定位邊編號、定位邊區間、W 回報編號)由 p8 與 p8b 各自殺。
 {'scene': '_s1_p8b_l_room_primary_through_reflex_extension_hi.scene', 'expect': 'reject',
  'error': ['V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍',
            '定位邊 e1 [0,1800] mm',
            '高端超出 [1800,4773] mm'],
  'error_not': ['低端超出']},
''')

    # ---- mutation table ------------------------------------------------------------------------
    contacts_new = t.get(NATIVE + "contacts.c")
    items = mutants299(contacts_new)
    for mid, desc, file, old, new in items:
        text = t.get(file)
        assert text.count(old) == 1, (mid, old)
    t.sub("tests/mutate.py", '''         old="        (span_lo < edge_lo || span_hi > edge_hi)) {",
         new="        (span_lo < edge_lo)) {"),
]
''', '''         old="        (span_lo < edge_lo || span_hi > edge_hi)) {",
         new="        (span_lo < edge_lo)) {"),
''' + render_mutants(items) + "]\n")
    t.sub("tests/test_geo261_mutation_migration.py", '''        self.assertEqual(28, len(added))
''', '''        # #299 (I22 W V_EXTENSION names the edge and the interval): M89-M95 mutate contacts.c's message,
        # M96 mutates contact_world.c's edge report.
        added.update({mid: "geometry-templates/woodworking/native/contacts.c" for mid in ("M89", "M90", "M91", "M92", "M93", "M94", "M95")})
        added["M96"] = "geometry-templates/woodworking/native/contact_world.c"
        self.assertEqual(36, len(added))
''')
    # ---- architecture inventory --------------------------------------------------------------------
    t.sub("geometry-core/domain-decoupling/product-architecture.json",
          '      "wood_contact_boundary_interval",\n',
          '      "wood_contact_boundary_edge",\n      "wood_contact_boundary_interval",\n')
    return t
