#include "history.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct { unsigned char bytes[32]; } Snapshot;
typedef struct {
    AppHistory history;
    Snapshot undo[32], redo[32], evicted, group_base;
} Storage;
typedef struct { unsigned calls; bool preserve_position; } Restore;

#define CHECK(condition, name) do { if (!(condition)) { fprintf(stderr,"ASSERT:%s\n",name); return 1; } } while (0)

static Snapshot value(unsigned id)
{
    Snapshot out;
    for (unsigned i=0;i<sizeof out.bytes;++i) out.bytes[i]=(unsigned char)(id*7u+i*3u);
    return out;
}
static bool equal(const Snapshot *a,const Snapshot *b)
{return memcmp(a,b,sizeof *a)==0;}
static bool is_value(const Snapshot *actual,unsigned id)
{Snapshot expected=value(id);return equal(actual,&expected);}
static void restore(void *opaque_document,const void *opaque_snapshot,void *opaque)
{
    Snapshot *document=opaque_document;
    const Snapshot *snapshot=opaque_snapshot;
    Restore *state=opaque;
    unsigned char presentation[8];
    memcpy(presentation,document->bytes+24,sizeof presentation);
    *document=*snapshot;
    if(state->preserve_position)memcpy(document->bytes+24,presentation,sizeof presentation);
    ++state->calls;
}
static void init(Storage *storage,size_t capacity)
{
    memset(storage,0xa5,sizeof *storage);
    app_history_init(&storage->history,sizeof(Snapshot),capacity,
        storage->undo,storage->redo,&storage->evicted,&storage->group_base);
}

static int record_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0};
    CHECK(app_history_peek_undo(&s.history)==NULL,"empty-peek");
    CHECK(!app_history_undo(&s.history,&document,restore,&r)&&r.calls==0,"empty-undo");
    CHECK(!app_history_redo(&s.history,&document,restore,&r)&&r.calls==0,"empty-redo");
    app_history_record(&s.history,&document);document=value(1);
    CHECK(s.history.undo_count==1&&s.history.redo_count==0,"record-counts");
    CHECK(is_value(app_history_peek_undo(&s.history),0),"record-full-snapshot");
    CHECK(app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,0),"undo-direction");
    CHECK(s.history.undo_count==0&&s.history.redo_count==1&&r.calls==1,"undo-counts-callback");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,1),"redo-direction");
    CHECK(s.history.undo_count==1&&s.history.redo_count==0&&r.calls==2,"redo-counts-callback");
    return 0;
}

static int eviction_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0};
    for(unsigned i=1;i<=40;++i){app_history_record(&s.history,&document);document=value(i);}
    CHECK(s.history.undo_count==32,"capacity-thirty-two");
    for(unsigned i=40;i>8;--i){
        CHECK(app_history_undo(&s.history,&document,restore,&r),"eviction-undo-present");
        CHECK(is_value(&document,i-1),"eviction-keeps-latest-thirty-two");
    }
    CHECK(!app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,8),"eviction-discards-only-oldest");
    for(unsigned i=9;i<=40;++i){
        CHECK(app_history_redo(&s.history,&document,restore,&r),"eviction-redo-present");
        CHECK(is_value(&document,i),"eviction-redo-order");
    }
    CHECK(r.calls==64&&!app_history_redo(&s.history,&document,restore,&r),"eviction-callback-count");
    return 0;
}

static int unrecord_case(void)
{
    Storage s;init(&s,3);Snapshot document=value(0);Restore r={0};
    for(unsigned i=1;i<=3;++i){app_history_record(&s.history,&document);document=value(i);}
    app_history_record(&s.history,&document);document=value(99);
    document=*(const Snapshot*)app_history_peek_undo(&s.history);
    app_history_unrecord(&s.history);
    CHECK(is_value(&document,3)&&s.history.undo_count==3,"failed-write-restored");
    CHECK(!s.history.record_evicted,"unrecord-clears-eviction-marker");
    for(unsigned i=3;i>0;--i){
        CHECK(app_history_undo(&s.history,&document,restore,&r),"unrecord-full-stack-count");
        CHECK(is_value(&document,i-1),"unrecord-restores-evicted-oldest");
    }
    for(unsigned i=1;i<=3;++i)CHECK(app_history_redo(&s.history,&document,restore,&r),"unrecord-replay-present");
    CHECK(app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,2),"redo-preserve-setup");
    app_history_record(&s.history,&document);
    CHECK(s.history.redo_count==0,"successful-record-clears-redo");
    document=value(99);document=*(const Snapshot*)app_history_peek_undo(&s.history);
    app_history_unrecord(&s.history);
    CHECK(s.history.undo_count==2&&s.history.redo_count==1,"unrecord-restores-redo-count");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,3),"unrecord-preserves-redo-bytes");
    return 0;
}

static int group_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0};
    CHECK(!app_history_group_end(&s.history),"end-without-begin");
    app_history_record(&s.history,&document);document=value(1);
    CHECK(app_history_undo(&s.history,&document,restore,&r),"group-redo-setup");
    CHECK(app_history_group_begin(&s.history,&document),"group-begin");
    CHECK(app_history_group_end(&s.history),"clean-group-end");
    CHECK(s.history.undo_count==0&&s.history.redo_count==1,"clean-group-preserves-redo");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,1),"group-redo-available");
    CHECK(app_history_group_begin(&s.history,&document),"dirty-group-begin");
    document=value(2);app_history_group_mark_dirty(&s.history);
    CHECK(!app_history_group_begin(&s.history,&document),"nested-begin-rejected");
    document=value(3);app_history_group_mark_dirty(&s.history);
    CHECK(app_history_group_end(&s.history),"dirty-group-end");
    CHECK(!s.history.grouping&&!s.history.group_dirty&&s.history.undo_count==2,"dirty-group-single-step");
    CHECK(app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,1),"group-base-keeps-first-begin");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,3),"group-redo-final-state");
    return 0;
}

static int abort_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0};
    app_history_record(&s.history,&document);document=value(1);
    CHECK(app_history_undo(&s.history,&document,restore,&r),"abort-redo-setup");
    unsigned before=r.calls;
    CHECK(app_history_group_begin(&s.history,&document),"abort-begin");
    document=value(77);app_history_group_mark_dirty(&s.history);
    app_history_group_abort(&s.history,&document);
    CHECK(is_value(&document,0),"abort-full-snapshot");
    CHECK(!s.history.grouping&&!s.history.group_dirty,"abort-closes-group");
    CHECK(s.history.undo_count==0&&s.history.redo_count==1&&r.calls==before,"abort-no-history-or-restore-hook");
    document=value(88);app_history_group_abort(&s.history,&document);
    CHECK(is_value(&document,88),"abort-idempotent");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,1),"abort-preserves-redo");
    return 0;
}

static int callback_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0,true};
    app_history_record(&s.history,&document);document=value(1);
    memset(document.bytes+24,0xbb,8);
    CHECK(app_history_undo(&s.history,&document,restore,&r),"callback-undo-present");
    Snapshot expected=value(0);memset(expected.bytes+24,0xbb,8);
    CHECK(equal(&document,&expected)&&r.calls==1,"undo-delegates-presentation");
    CHECK(s.redo[0].bytes[0]==7&&s.redo[0].bytes[31]==0xbb,"undo-push-before-restore");
    memset(document.bytes+24,0xcc,8);
    CHECK(app_history_redo(&s.history,&document,restore,&r),"callback-redo-present");
    expected=value(1);memset(expected.bytes+24,0xcc,8);
    CHECK(equal(&document,&expected)&&r.calls==2,"redo-delegates-presentation");
    CHECK(app_history_group_begin(&s.history,&document),"callback-abort-begin");
    memset(document.bytes,0xdd,sizeof document.bytes);app_history_group_mark_dirty(&s.history);
    app_history_group_abort(&s.history,&document);
    CHECK(equal(&document,&expected)&&r.calls==2,"abort-bypasses-presentation-hook");
    return 0;
}

static int clear_case(void)
{
    Storage s;init(&s,32);Snapshot document=value(0);Restore r={0};
    app_history_record(&s.history,&document);document=value(1);
    app_history_record(&s.history,&document);document=value(2);
    CHECK(app_history_undo(&s.history,&document,restore,&r),"clear-redo-setup");
    CHECK(app_history_group_begin(&s.history,&document),"clear-group-setup");
    app_history_group_mark_dirty(&s.history);
    Snapshot old_undo[32],old_redo[32],old_evicted=s.evicted,old_group=s.group_base;
    memcpy(old_undo,s.undo,sizeof old_undo);memcpy(old_redo,s.redo,sizeof old_redo);
    app_history_clear(&s.history);
    CHECK(!s.history.undo_count&&!s.history.redo_count&&!s.history.grouping&&!s.history.group_dirty,"clear-counts-and-group");
    CHECK(!memcmp(old_undo,s.undo,sizeof old_undo)&&!memcmp(old_redo,s.redo,sizeof old_redo)
        &&equal(&old_evicted,&s.evicted)&&equal(&old_group,&s.group_base),"clear-leaves-storage-bytes");
    CHECK(!app_history_undo(&s.history,&document,restore,&r)&&!app_history_redo(&s.history,&document,restore,&r),"clear-no-old-history");
    return 0;
}

static int single_case(void)
{
    Storage s;init(&s,1);Snapshot document=value(0);Restore r={0};
    app_history_record(&s.history,&document);document=value(1);
    app_history_record(&s.history,&document);document=value(2);
    CHECK(app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,1),"one-slot-undo");
    CHECK(!app_history_undo(&s.history,&document,restore,&r),"one-slot-oldest-gone");
    CHECK(app_history_redo(&s.history,&document,restore,&r)&&is_value(&document,2),"one-slot-redo");
    app_history_record(&s.history,&document);app_history_unrecord(&s.history);
    CHECK(app_history_undo(&s.history,&document,restore,&r)&&is_value(&document,1),"one-slot-unrecord-restores-oldest");
    return 0;
}

int main(int argc,char **argv)
{
    if(argc!=2)return 2;
    if(!strcmp(argv[1],"record"))return record_case();
    if(!strcmp(argv[1],"eviction"))return eviction_case();
    if(!strcmp(argv[1],"unrecord"))return unrecord_case();
    if(!strcmp(argv[1],"group"))return group_case();
    if(!strcmp(argv[1],"abort"))return abort_case();
    if(!strcmp(argv[1],"callback"))return callback_case();
    if(!strcmp(argv[1],"clear"))return clear_case();
    if(!strcmp(argv[1],"single"))return single_case();
    return 2;
}
