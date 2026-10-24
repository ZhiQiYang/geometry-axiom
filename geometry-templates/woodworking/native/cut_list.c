#include "cut_list.h"
#include <string.h>

bool wood_cut_list_collect(const WoodMember *members,size_t count,WoodCutList *out)
{
    if(!out||(!members&&count)||count>WOOD_CUT_LIST_MEMBER_CAPACITY)return false;
    memset(out,0,sizeof *out);
    for(size_t i=0;i<count;++i){const WoodMember *member=&members[i];
        if(!member->placed)continue;
        ++out->placed;out->total_length+=member->length;
        size_t g=0;
        for(;g<out->group_count;++g){const WoodCutGroup *group=&out->groups[g];
            if(group->length==member->length&&group->size_a==member->size_a&&
                group->size_b==member->size_b&&group->role==member->role)break;
        }
        if(g==out->group_count){WoodCutGroup *group=&out->groups[g];
            group->length=member->length;group->size_a=member->size_a;
            group->size_b=member->size_b;group->role=member->role;
            ++out->group_count;
        }
        ++out->groups[g].count;
    }
    for(size_t a=0;a+1<out->group_count;++a)for(size_t b=a+1;b<out->group_count;++b){
        const WoodCutGroup *left=&out->groups[a],*right=&out->groups[b];
        bool swap=right->length>left->length||
            (right->length==left->length&&(right->size_a<left->size_a||
                (right->size_a==left->size_a&&(right->size_b<left->size_b||
                    (right->size_b==left->size_b&&right->role<left->role)))));
        if(swap){WoodCutGroup temporary=out->groups[a];out->groups[a]=out->groups[b];out->groups[b]=temporary;}
    }
    /* The sorted groups own disjoint slices of one report-local ID pool.
     * Revisit declarations to fill every slice in the original ID order. */
    size_t first=0;
    for(size_t g=0;g<out->group_count;++g){WoodCutGroup *group=&out->groups[g];
        group->first=first;first+=group->count;group->count=0;
    }
    for(size_t i=0;i<count;++i){const WoodMember *member=&members[i];
        if(member->placed){
            for(size_t g=0;g<out->group_count;++g){WoodCutGroup *group=&out->groups[g];
                if(group->length!=member->length||group->size_a!=member->size_a||
                    group->size_b!=member->size_b||group->role!=member->role)continue;
                out->ids[group->first+group->count++]=member->id;break;
            }
        }
    }
    return true;
}
