/* H selects the exact World snapshot; all version storage/admission is K and
 * schema interpretation/archive policy is W. The backing contains no pointers. */
static GeoVersionStore *app_eng_version_store(const World *world)
{return &((World *)world)->geo.version_store;}
