/* Independent K client: compile and link only kernel/exact.c. */
#include "exact.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

int main(int argc,char **argv)
{
    GeoQuantity a,b,out={37,41,GEO_UNIT_LENGTH};
    GeoExactStatus status;
    if(argc==5&&!strcmp(argv[1],"normalize")){
        a=(GeoQuantity){strtoll(argv[2],NULL,10),strtoll(argv[3],NULL,10),(GeoQuantityUnit)atoi(argv[4])};
        status=geo_quantity_normalize(a,&out);
    }else if(argc==8){
        a=(GeoQuantity){strtoll(argv[2],NULL,10),strtoll(argv[3],NULL,10),(GeoQuantityUnit)atoi(argv[4])};
        b=(GeoQuantity){strtoll(argv[5],NULL,10),strtoll(argv[6],NULL,10),(GeoQuantityUnit)atoi(argv[7])};
        status=geo_quantity_binary((GeoExactOperation)atoi(argv[1]),a,b,&out);
    }else return 70;
    printf("%d %" PRId64 " %" PRId64 " %d\n",(int)status,out.num,out.den,(int)out.unit);
    return 0;
}
