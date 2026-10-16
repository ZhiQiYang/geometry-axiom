#include "grid.h"
#include <string.h>
#include <limits.h>

bool geo_i64_add(int64_t a,int64_t b,int64_t *out)
{
    if ((b>0 && a>INT64_MAX-b)||(b<0 && a<INT64_MIN-b)) return false;
    *out=a+b; return true;
}
int64_t geo_floor_div(int64_t a,int64_t b)
{ int64_t q=a/b,r=a%b; return q-(r<0); }
int64_t geo_ceil_div(int64_t a,int64_t b)
{ int64_t q=a/b,r=a%b; return q+(r>0); }
GeoCoord geo_period_pitch(GeoCoord body,GeoCoord gap) { return body+gap; }
GeoCoord geo_period_body(GeoCoord anchor,GeoCoord body,GeoCoord gap,int64_t k)
{ return anchor+k*geo_period_pitch(body,gap); }
GeoCoord geo_period_center(GeoCoord anchor,GeoCoord body,GeoCoord gap,int64_t k)
{ return geo_period_body(anchor,body,gap,k)+body+gap/2; }
GeoCoord geo_alternating_shift(bool set,GeoCoord delta,int64_t row)
{ return set&&(row&1)?delta:0; }

bool geo_lattice_coord(const GeoLattice *g,int64_t k,GeoCoord *out)
{
    if (!g || g->pitch<=0 || g->base < -3*GEO_COORD_LIMIT || g->base > 3*GEO_COORD_LIMIT) return false;
    int64_t base=g->base,origin=g->index,step=g->pitch,value;
    if (k>=origin) {
        uint64_t delta=(uint64_t)k-(uint64_t)origin;
        int64_t room=GEO_COORD_LIMIT-base;
        if (room<0 || delta>(uint64_t)(room/step)) return false;
        value=base+(int64_t)delta*step;
    } else {
        uint64_t delta=(uint64_t)origin-(uint64_t)k;
        int64_t room=base+GEO_COORD_LIMIT;
        if (room<0 || delta>(uint64_t)(room/step)) return false;
        value=base-(int64_t)delta*step;
    }
    if (!geo_coord_in_range(value)) return false;
    if(out) *out=value; return true;
}

GeoGridStatus geo_lattice_window(const GeoLattice *g,GeoCoord lo,GeoCoord hi,
    size_t limit,bool sample,GeoLatticeWindow *out)
{
    if(!out)return GEO_GRID_INVALID;
    out->defined=false;out->first=out->last=0;out->total=0;out->stride=1;out->count=0;
    if (!g || !limit || limit>out->capacity || !out->lines || lo>hi || g->base < -3*GEO_COORD_LIMIT || g->base > 3*GEO_COORD_LIMIT || g->pitch<0 ||
        !geo_coord_in_range(lo) || !geo_coord_in_range(hi)) goto invalid;
    if (!g->pitch) return GEO_GRID_OK;
    out->defined=true;
    int64_t step=g->pitch,base=g->base,origin=g->index;
    int64_t first_delta=geo_ceil_div(lo-base,step),last_delta=geo_floor_div(hi-base,step);
    if(first_delta>last_delta) return GEO_GRID_OK;
    if(!geo_i64_add(origin,first_delta,&out->first)||!geo_i64_add(origin,last_delta,&out->last)) {
        return GEO_GRID_INDEX_RANGE;
    }
    out->total=(uint64_t)(last_delta-first_delta)+1;
    if(out->total>limit && !sample) {
        return GEO_GRID_CAPACITY;
    }
    out->stride=sample?(out->total+limit-1)/limit:1;
    if(!out->stride) out->stride=1;
    int64_t stride=(int64_t)out->stride,k=out->first,r=k%stride;
    if(r<0)r+=stride;
    if(r && !geo_i64_add(k,stride-r,&k)) return GEO_GRID_OK;
    for(;k<=out->last;) {
        GeoLatticeLine *line=&out->lines[out->count]; line->index=k;
        if(!geo_lattice_coord(g,k,&line->coordinate)) goto invalid;
        if(++out->count>=limit || out->last-k<stride) break;
        k+=stride;
    }
    return GEO_GRID_OK;
invalid:
    out->count=0;return GEO_GRID_INVALID;
}

bool geo_coordinates_increasing(const GeoCoord coords[], size_t count)
{
    for (size_t i = 0; i < count; ++i) {
        if (i > 0 && coords[i] <= coords[i - 1]) {
            return false;   /* 必須嚴格遞增 */
        }
    }

    return true;
}

GeoGridStatus geo_finite_sequence(const GeoFiniteSequence *def,GeoCoord lo,GeoCoord hi,
    GeoCoord *out,size_t capacity,size_t *out_count)
{
    if(out_count)*out_count=0;
    if(!def||!out_count||(!out&&capacity)||lo>hi||!geo_coord_in_range(lo)||!geo_coord_in_range(hi))return GEO_GRID_INVALID;
    if(def->kind==GEO_SEQUENCE_NONE)return GEO_GRID_NO_SOURCE;
    if(def->kind==GEO_SEQUENCE_EXPLICIT&&def->count&&!def->coordinates)return GEO_GRID_INVALID;
    size_t n = 0;

    if (def->kind == GEO_SEQUENCE_EXPLICIT) {
        if (def->count > capacity) {
            return GEO_GRID_INVALID;
        }

        for (size_t k = 0; k < def->count; ++k) {
            out[n++] = def->coordinates[k];
        }
    } else if (def->kind == GEO_SEQUENCE_SERIES) {
        /* D10：第 k 條 = start + k·step；step > 0 本身就保證嚴格遞增。 */
        if (def->count == 0 ||
            def->count > capacity ||
            def->step <= 0) {
            return GEO_GRID_INVALID;
        }

        for (size_t k = 0; k < def->count; ++k) {
            out[n++] = def->start + (GeoCoord)k * def->step;
        }
    } else if (def->kind == GEO_SEQUENCE_BODY_GAP) {
        /*
         * D10a：週期 T = panel + gap，第 k 條縫中心線
         *   c_k = a + k·T + panel + gap/2，
         * 產生條件 a+(k+1)·T < hi——整條縫落在範圍內，且其後仍有非空的面材本體。
         * 不滿足就停：末端是裁切片，合法，不因「除不盡」而拒絕。
         */
        const GeoCoord T = geo_period_pitch(def->body,def->gap);

        if (def->body <= 0 || def->gap < 0 ||
            def->anchor < lo || def->anchor >= hi) {
            return GEO_GRID_BODY_GAP_INVALID;
        }

        for (size_t k = 0; ; ++k) {
            const GeoCoord gap_hi = def->anchor + (GeoCoord)(k + 1) * T;

            if (gap_hi >= hi) {
                break;
            }

            if (n == capacity) {
                return GEO_GRID_CAPACITY;
            }

            out[n++] = geo_period_center(def->anchor,def->body,def->gap,(int64_t)k);
        }
    } else {
        return GEO_GRID_SOURCE_UNSUPPORTED;
    }

    /* I10：嚴格遞增。 */
    if (!geo_coordinates_increasing(out, n)) {
        return GEO_GRID_ORDER;
    }

    /* I10：每條都落在該軸外接區間內——與 guide offset 同一條規則。 */
    for (size_t k = 0; k < n; ++k) {
        if (out[k] < lo || out[k] > hi) {
            return GEO_GRID_BOUNDS;
        }
    }

    *out_count=n;return GEO_GRID_OK;
}

GeoGridStatus geo_interval_subdivide(GeoCoord lo,GeoCoord hi,unsigned n,
    GeoCoord *out,size_t capacity,size_t *count)
{
    if(count)*count=0;
    if(!count||(!out&&capacity)||lo>=hi||!geo_coord_in_range(lo)||!geo_coord_in_range(hi)||n<1)return GEO_GRID_INVALID;
    if((size_t)n-1>capacity)return GEO_GRID_CAPACITY;
    if((hi-lo)%n)return GEO_GRID_NOT_DIVISIBLE;
    GeoCoord step=(hi-lo)/n;
    for(unsigned k=1;k<n;++k)out[(*count)++]=lo+k*step;
    return GEO_GRID_OK;
}
