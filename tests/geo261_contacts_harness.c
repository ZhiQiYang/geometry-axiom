#include "contacts.h"
#include <stdio.h>
#include <string.h>

#define CHECK(name, expression) do { if (!(expression)) { \
    fprintf(stderr, "ASSERT:%s\n", name); return 1; } } while (0)

bool frozen_span_extension_check(const WoodMember *, bool,
    GeoCoord, GeoCoord, GeoCoord, GeoCoord, char *, size_t);
bool frozen_end_contact_check(const WoodMember *, const WoodStopFace *,
    const WoodMember *, bool, char *, size_t);

static const char SPAN_ERROR[] =
    "V_EXTENSION：非 boundary 角材（17）的 footprint 超出定位邊範圍";
static const char OUTLINE_ERROR[] =
    "V_CUT_PRIORITY：角材 17 端面頂到外輪廓邊（RC）——那條邊還沒鋪邊界材；只有 boundary 可頂 RC";
static const char EQUAL_PRIORITY_ERROR[] =
    "V_CUT_PRIORITY：角材 17（優先級 2）端面頂到角材 23（優先級 2）側面——擋面擁有者優先級必須嚴格小於自己";

static WoodMember member(uint32_t id, WoodMemberRole role, GeoCoord priority)
{
    WoodMember value = {0};
    value.id = id;
    value.role = role;
    value.cut_priority = priority;
    value.placed = true;
    return value;
}

static int span(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    char err[512] = "unchanged";
    CHECK("span-no-edge", wood_member_span_extension_check(&self,false,-1,101,0,100,err,sizeof err));
    CHECK("span-accept-output-unchanged", !strcmp(err,"unchanged"));
    self.role = WOOD_MEMBER_ROLE_BOUNDARY;
    CHECK("span-boundary-extension", wood_member_span_extension_check(&self,true,-1,101,0,100,err,sizeof err));
    self.role = WOOD_MEMBER_ROLE_PRIMARY;
    CHECK("span-touch-equality", wood_member_span_extension_check(&self,true,0,100,0,100,err,sizeof err));
    CHECK("span-contained", wood_member_span_extension_check(&self,true,1,99,0,100,err,sizeof err));
    CHECK("span-low-refusal", !wood_member_span_extension_check(&self,true,-1,100,0,100,err,sizeof err));
    CHECK("span-error-exact", !strcmp(err,SPAN_ERROR));
    CHECK("span-high-refusal", !wood_member_span_extension_check(&self,true,0,101,0,100,NULL,0));
    self.role = (WoodMemberRole)-7;
    CHECK("span-unknown-role-not-boundary", !wood_member_span_extension_check(&self,true,0,101,0,100,NULL,0));
    return 0;
}

static int kinds(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodMember owner = member(23,WOOD_MEMBER_ROLE_PRIMARY,9);
    WoodStopFace face = {0};
    face.fixity = WOOD_STOP_FIXED;
    face.timber_id = owner.id;
    char err[512] = "unchanged";
    face.kind = WOOD_STOP_OUTLINE_EDGE;
    CHECK("outline-primary-refusal", !wood_member_end_contact_check(&self,&face,&owner,true,err,sizeof err));
    CHECK("outline-error-exact", !strcmp(err,OUTLINE_ERROR));
    self.role = WOOD_MEMBER_ROLE_BOUNDARY;
    strcpy(err,"unchanged");
    CHECK("outline-boundary-accepted", wood_member_end_contact_check(&self,&face,&owner,true,err,sizeof err));
    CHECK("outline-accept-output-unchanged", !strcmp(err,"unchanged"));
    self.role = WOOD_MEMBER_ROLE_PRIMARY;
    face.kind = WOOD_STOP_HOLE_EDGE;
    CHECK("hole-accepted", wood_member_end_contact_check(&self,&face,&owner,false,err,sizeof err));
    face.kind = 99;
    CHECK("unknown-positive-kind-accepted", wood_member_end_contact_check(&self,&face,&owner,false,err,sizeof err));
    face.kind = -1;
    CHECK("unknown-negative-kind-accepted", wood_member_end_contact_check(&self,&face,&owner,false,err,sizeof err));
    CHECK("other-kinds-output-unchanged", !strcmp(err,"unchanged"));
    return 0;
}

static int owners(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodMember owner = member(23,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodStopFace face = {0};
    face.fixity = WOOD_STOP_FIXED;
    face.kind = WOOD_STOP_MEMBER_SIDE;
    face.timber_id = self.id;
    char err[512] = "unchanged";
    CHECK("null-owner-exempt", wood_member_end_contact_check(&self,&face,NULL,true,err,sizeof err));
    CHECK("self-owner-exempt", wood_member_end_contact_check(&self,&face,&self,true,err,sizeof err));
    CHECK("owner-exemption-output-unchanged", !strcmp(err,"unchanged"));
    owner.id = self.id;
    CHECK("same-id-distinct-pointer-not-exempt", !wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    owner.id = 23;
    face.timber_id = owner.id;
    CHECK("equal-priority-refusal", !wood_member_end_contact_check(&self,&face,&owner,false,err,sizeof err));
    CHECK("priority-error-exact", !strcmp(err,EQUAL_PRIORITY_ERROR));
    self.role = owner.role = WOOD_MEMBER_ROLE_BOUNDARY;
    self.cut_priority = owner.cut_priority = 1;
    strcpy(err,"unchanged");
    CHECK("two-boundary-exempt", wood_member_end_contact_check(&self,&face,&owner,true,err,sizeof err));
    CHECK("boundary-exemption-output-unchanged", !strcmp(err,"unchanged"));
    owner.role = WOOD_MEMBER_ROLE_PRIMARY;
    owner.cut_priority = 2;
    CHECK("only-self-boundary-not-exempt", !wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    return 0;
}

static int priorities(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodMember owner = member(23,WOOD_MEMBER_ROLE_BOUNDARY,1);
    WoodStopFace face = {0};
    face.fixity = WOOD_STOP_FIXED;
    face.kind = WOOD_STOP_MEMBER_SIDE;
    face.timber_id = owner.id;
    char err[512] = "unchanged";
    CHECK("lower-priority-accepted", wood_member_end_contact_check(&self,&face,&owner,false,err,sizeof err));
    CHECK("lower-priority-output-unchanged", !strcmp(err,"unchanged"));
    CHECK("extension-priority-two", !wood_member_end_contact_check(&self,&face,&owner,true,err,sizeof err));
    CHECK("extension-error-effective-priority", !strcmp(err,EQUAL_PRIORITY_ERROR));
    self.role = WOOD_MEMBER_ROLE_CUSTOM;
    self.cut_priority = 3;
    strcpy(err,"unchanged");
    CHECK("custom-three-accepts-extension", wood_member_end_contact_check(&self,&face,&owner,true,err,sizeof err));
    CHECK("custom-accept-output-unchanged", !strcmp(err,"unchanged"));
    owner.role = WOOD_MEMBER_ROLE_PRIMARY;
    owner.cut_priority = 4;
    CHECK("higher-priority-refusal", !wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    owner.cut_priority = 3;
    CHECK("equal-custom-priority-refusal", !wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    self.cut_priority = -4;
    owner.cut_priority = -5;
    CHECK("signed-priority-no-new-admission", wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    self.cut_priority = INT64_C(1) << 40;
    owner.cut_priority = self.cut_priority - 1;
    CHECK("wide-priority-comparison", wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    owner.cut_priority = self.cut_priority;
    CHECK("wide-equal-priority-refusal", !wood_member_end_contact_check(&self,&face,&owner,false,NULL,0));
    return 0;
}

static int buffer(void)
{
    WoodMember self = member(17,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodMember owner = member(23,WOOD_MEMBER_ROLE_PRIMARY,2);
    WoodStopFace face = {0};
    face.fixity = WOOD_STOP_FIXED;
    face.timber_id = owner.id;
    const size_t capacities[] = {0,1,8,21,512};
    const char *expected[] = {SPAN_ERROR,OUTLINE_ERROR,EQUAL_PRIORITY_ERROR};
    for (int kind = 0; kind < 3; ++kind) {
        for (size_t c = 0; c < sizeof capacities / sizeof capacities[0]; ++c) {
            char err[512];
            memset(err,0x5a,sizeof err);
            size_t cap = capacities[c];
            bool ok;
            if (kind == 0) {
                ok = wood_member_span_extension_check(&self,true,-1,100,0,100,err,cap);
            } else {
                face.kind = kind == 1 ? WOOD_STOP_OUTLINE_EDGE : WOOD_STOP_MEMBER_SIDE;
                ok = wood_member_end_contact_check(&self,&face,&owner,false,err,cap);
            }
            CHECK("buffer-refusal", !ok);
            size_t written = 0;
            if (cap) {
                written = strlen(expected[kind]);
                if (written >= cap) written = cap - 1;
                CHECK("buffer-exact-prefix", !memcmp(err,expected[kind],written));
                CHECK("buffer-null-terminated", err[written] == '\0');
                ++written;
            }
            for (size_t i = written; i < sizeof err; ++i)
                CHECK("buffer-tail-untouched", (unsigned char)err[i] == 0x5a);
        }
    }
    self.id = UINT32_MAX;
    char err[512];
    CHECK("full-id-refusal", !wood_member_span_extension_check(&self,true,-1,100,0,100,err,sizeof err));
    CHECK("full-id-text", !strcmp(err,"V_EXTENSION：非 boundary 角材（4294967295）的 footprint 超出定位邊範圍"));
    return 0;
}

static uint32_t random_state = UINT32_C(261);
static uint32_t next_random(void)
{
    random_state = random_state * UINT32_C(1664525) + UINT32_C(1013904223);
    return random_state;
}

static int equivalence(void)
{
    const GeoCoord priorities[] = {-7,0,1,2,3,INT64_C(1)<<40};
    for (size_t trial = 0; trial < 3000; ++trial) {
        WoodMember self = member(next_random(),(WoodMemberRole)((int)(next_random()%7)-1),priorities[next_random()%6]);
        WoodMember owner = member(next_random(),(WoodMemberRole)((int)(next_random()%7)-1),priorities[next_random()%6]);
        WoodStopFace face = {0};
        face.fixity = WOOD_STOP_FIXED;
        face.kind = (int)(next_random()%6)-1;
        const WoodMember *resolved = trial%3 == 0 ? NULL : trial%3 == 1 ? &self : &owner;
        face.timber_id = resolved == NULL ? 0 : resolved->id;
        bool extension = (next_random()%2)!=0;
        char actual[512], expected[512];
        memset(actual,0x5a,sizeof actual); memset(expected,0x5a,sizeof expected);
        size_t cap = trial%5 == 0 ? 0 : trial%5 == 1 ? 1 : trial%5 == 2 ? 19 : sizeof actual;
        bool a = wood_member_end_contact_check(&self,&face,resolved,extension,actual,cap);
        bool e = frozen_end_contact_check(&self,&face,resolved,extension,expected,cap);
        CHECK("frozen-contact-verdict-and-bytes", a == e && !memcmp(actual,expected,sizeof actual));
        GeoCoord lo = (GeoCoord)(next_random()%20)-5, hi = lo+(GeoCoord)(next_random()%20);
        bool has_edge = (next_random()%2)!=0;
        memset(actual,0x5a,sizeof actual); memset(expected,0x5a,sizeof expected);
        a = wood_member_span_extension_check(&self,has_edge,lo,hi,0,20,actual,cap);
        e = frozen_span_extension_check(&self,has_edge,lo,hi,0,20,expected,cap);
        CHECK("frozen-span-verdict-and-bytes", a == e && !memcmp(actual,expected,sizeof actual));
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1],"span")) return span();
    if (!strcmp(argv[1],"kinds")) return kinds();
    if (!strcmp(argv[1],"owners")) return owners();
    if (!strcmp(argv[1],"priorities")) return priorities();
    if (!strcmp(argv[1],"buffer")) return buffer();
    if (!strcmp(argv[1],"equivalence")) return equivalence();
    return 2;
}
