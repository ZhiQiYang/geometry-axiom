"""Public K document ownership witnesses and safe, exact negative controls.

Only the isolated kernel factory is used. The native absence witness inspects
actual compile/link arguments and copied include files, not a proposed command.
No failed build, process crash or arbitrary nonzero exit counts as detection.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.test_geo261_native_kernel import kernel_only_native

KERNEL=ROOT/"geometry-core/kernel"
STORES=(
    ("GeoParameterStore","parameters","parameters"),
    ("GeoNamedValues","named_values","named_values"),
    ("GeoDatumStore","datums","datum_planes"),
    ("GeoGuideStore","guides","guide_lines"),
    ("GeoRegionStore","regions","region_data"),
    ("GeoPlacementStore","placements","placement_data"),
    ("GeoGridStore","grids","grid_store"),
    ("GeoVersionStore","versions","version_store"),
    ("GeoEnclosureStore","enclosures","enclosures"),
)


def code(source):
    return re.sub(r"/\*.*?\*/|//[^\n]*","",source,flags=re.S)


def controls():
    result=[]
    for kind,name,field in STORES:
        target="named_values" if name!="named_values" else "parameters"
        before=f"GEO_DOCUMENT_STORE({kind},{name},{field})"
        # Wrong-field handles are compared as addresses before any store API
        # dereferences them. Casts make this a runtime oracle, not a type error.
        after=(f"{kind} *geo_document_{name}(GeoDocument *document)\n"
            f"{{return document?({kind}*)(void*)&document->{target}:NULL;}}\n"
            f"const {kind} *geo_document_{name}_view(const GeoDocument *document)\n"
            f"{{return document?(const {kind}*)(const void*)&document->{target}:NULL;}}")
        result.append(("accessor-"+name,before,after,"handles","handles-nine-distinct"))
    before="if(copy)memcpy(copy,source,sizeof *copy);"
    for _,name,field in STORES:
        after=f"if(copy){{memcpy(copy,source,sizeof *copy);memset(&copy->{field},0,sizeof copy->{field});}}"
        result.append(("clone-"+name,before,after,"clone","clone-"+name.replace("_","-")))
    result.extend([
        ("clone-empty",before,"if(copy)memset(copy,0,sizeof *copy);","clone","clone-parameters"),
        ("clone-alias","GeoDocument *copy=malloc(sizeof *copy);\n    if(copy)memcpy(copy,source,sizeof *copy);\n    return copy;",
            "return (GeoDocument*)source;","clone","clone-distinct-document"),
        ("clear-noop","{if(document)memset(document,0,sizeof *document);}","{(void)document;}","clear","clear-all-nine-stores"),
        ("null-clone","if(!source)return NULL;","if(!source)return geo_document_create();","null","null-clone"),
        ("null-mutable","type *geo_document_##name(GeoDocument *document) "+chr(92)+"\n    {return document?&document->field:NULL;}",
            "type *geo_document_##name(GeoDocument *document) "+chr(92)+"\n    {return document?&document->field:(type*)(uintptr_t)1;}","null","null-mutable-accessors"),
        ("null-const","const type *geo_document_##name##_view(const GeoDocument *document) "+chr(92)+"\n    {return document?&document->field:NULL;}",
            "const type *geo_document_##name##_view(const GeoDocument *document) "+chr(92)+"\n    {return document?&document->field:(const type*)(uintptr_t)1;}","null","null-const-accessors"),
    ])
    return result


class DocumentBoundary(unittest.TestCase):
    def test_public_document_is_opaque_and_private_storage_is_nine_inline_stores(self):
        public=code((KERNEL/"document.h").read_text(encoding="utf-8"))
        private=code((KERNEL/"internal/document.h").read_text(encoding="utf-8"))
        self.assertIn("typedef struct GeoDocument GeoDocument;",public)
        self.assertNotIn("struct GeoDocument {",public)
        body=re.search(r"struct GeoDocument\s*\{(.*?)\};",private,re.S).group(1)
        self.assertNotIn("*",body)
        self.assertCountEqual([(kind,field) for kind,_,field in STORES],re.findall(r"(\w+)\s+(\w+)\s*;",body))
        source=public+private+code((KERNEL/"document.c").read_text(encoding="utf-8"))
        self.assertNotRegex(source,r"\b(?:World|Space|Timber|Wood\w*|App\w*)\b")

    def test_client_uses_only_public_document_header_and_all_accessor_pairs(self):
        source=(ROOT/"tests/geo261_document_harness.c").read_text(encoding="utf-8")
        self.assertEqual(["document.h"],re.findall(r'^#include "([^"]+)"',source,re.M))
        self.assertNotRegex(code(source),r"\b(?:World|Space|Timber|Wood\w*|App\w*)\b|internal/")
        for _,name,_ in STORES:
            self.assertRegex(source,r"\bgeo_document_"+name+r"\(")
            self.assertRegex(source,r"\bgeo_document_"+name+r"_view\(")

    def test_controls_target_one_real_definition_and_one_named_oracle(self):
        source=(KERNEL/"document.c").read_text(encoding="utf-8")
        harness=(ROOT/"tests/geo261_document_harness.c").read_text(encoding="utf-8")
        names=[]
        for name,before,after,case,marker in controls():
            with self.subTest(control=name):
                self.assertEqual(1,source.count(before),name)
                self.assertNotEqual(before,after)
                self.assertEqual(1,harness.count('"'+marker+'"'))
                self.assertIn('"'+case+'"',harness)
            names.append(name)
        self.assertEqual(24,len(names));self.assertEqual(len(names),len(set(names)))


class NativeDocument(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=kernel_only_native();source=build.work/"document-client.c"
        shutil.copy2(ROOT/"tests/geo261_document_harness.c",source)
        cls.client=build.compile(source,"document-client")
        cls.objects=build.kernel_objects()
        if cls.objects.count(build.document_object)!=1:
            raise AssertionError("Expected one actual document K object")
        cls.exe=build.link("document-client",[cls.client,*cls.objects])

    def case(self,name,exe=None,marker=None):
        run=subprocess.run([str(exe or self.exe),name],capture_output=True,text=True,encoding="utf-8",timeout=15)
        self.assertEqual(1 if marker else 0,run.returncode,run.stderr)
        self.assertEqual("ASSERT:"+marker+"\n" if marker else "",run.stderr)
        self.assertEqual("",run.stdout)

    def test_nine_distinct_mutable_and_const_handles_per_document(self):self.case("handles")
    def test_nine_populated_stores_own_definitions_caches_keys_and_version_bytes(self):self.case("contents")
    def test_clone_preserves_every_store_and_mutations_and_lifetimes_are_independent(self):self.case("clone")
    def test_clear_empties_every_store_keeps_handles_and_allows_reuse(self):self.case("clear")
    def test_null_accessors_clone_clear_and_destroy(self):self.case("null")

    def test_actual_build_has_no_host_or_template_files_sources_includes_or_objects(self):
        build=kernel_only_native()
        self.assertTrue(build.kernel_only)
        self.assertFalse(hasattr(build,"host"));self.assertFalse(hasattr(build,"woodworking"))
        self.assertFalse((build.work/"isolated-host").exists())
        self.assertFalse((build.work/"isolated-woodworking").exists())
        forbidden=r"geometry-app|geometry-templates|current_geometry|web_bridge|isolated-host|isolated-woodworking"
        compiled={};linked=[]
        for entry in build.logs:
            args=entry["arguments"]
            self.assertEqual(0,entry["exit"])
            self.assertNotRegex(" ".join(args).lower(),forbidden)
            sources=[Path(arg).resolve() for arg in args if arg.lower().endswith(".c")]
            if sources:
                self.assertEqual(1,len(sources));source=sources[0]
                self.assertTrue(source.is_relative_to(build.work.resolve()))
                self.assertTrue(source.is_relative_to(build.kernel.resolve()) or
                    (source.parent==build.work.resolve() and source.name.endswith("-client.c")))
                if build.windows:
                    outputs=[Path(arg[4:]).resolve() for arg in args if arg.startswith("/Fo:")]
                else:outputs=[Path(args[args.index("-o")+1]).resolve()]
                self.assertEqual(1,len(outputs));compiled[outputs[0]]=source
            else:
                linked.extend(Path(arg).resolve() for arg in args if arg.lower().endswith((".o",".obj")))
        self.assertEqual(build.kernel.resolve()/"document.c",compiled[build.document_object.resolve()])
        self.assertTrue(linked)
        for obj in [*linked,*self.objects,self.client]:
            self.assertIn(obj.resolve(),compiled)
        for path in build.work.rglob("*"):
            if not path.is_file() or path.suffix not in (".c",".h"):continue
            self.assertNotRegex(str(path).lower(),forbidden)
            source=path.read_text(encoding="utf-8")
            for name in re.findall(r'^\s*#include\s+"([^"]+)"',source,re.M):
                target=(path.parent/name).resolve()
                if not target.is_file():target=(build.kernel/name).resolve()
                self.assertTrue(target.is_file(),str(path)+": "+name)
                self.assertTrue(target.is_relative_to(build.kernel.resolve()),str(target))

    def test_actual_document_controls_fail_only_their_named_oracles(self):
        build=kernel_only_native();original=(build.kernel/"document.c").read_text(encoding="utf-8")
        for name,before,after,case,marker in controls():
            with self.subTest(control=name):
                self.case(case)
                self.assertEqual(1,original.count(before))
                path=build.kernel/("document-control-"+name+".c")
                path.write_text(original.replace(before,after),encoding="utf-8")
                changed=build.compile(path,"document-control-"+name)
                objects=[changed if obj==build.document_object else obj for obj in self.objects]
                mutant=build.link("document-control-"+name,[self.client,*objects])
                self.case(case,mutant,marker)
                self.case(case)


if __name__=="__main__":unittest.main(verbosity=2)
