/* D7/I18 declaration admission over the caller's same-candidate member store.
 * H retains tokenization, numeric decoding and transaction publication. */
#ifndef GEOMETRY_WOODWORKING_MEMBER_DECLARATION_H
#define GEOMETRY_WOODWORKING_MEMBER_DECLARATION_H
#include "members.h"
typedef struct {
    WoodMember *members;
    size_t *count,capacity;
    void *user;
    bool (*owned)(void *,uint32_t);
    bool (*replace)(void *,WoodMember *,const WoodMember *);
} WoodMemberDeclarationContext;
bool wood_member_declaration_capacity(const WoodMemberDeclarationContext *,bool,uint32_t,const char **);
bool wood_member_declaration_role(const char *,WoodMemberRole *,const char **);
bool wood_member_declaration_priority(WoodMemberRole,bool,bool,GeoCoord,const char **);
bool wood_member_declare(WoodMemberDeclarationContext *,uint32_t,GeoCoord,GeoCoord,WoodMemberRole,GeoCoord,const char **);
#endif
