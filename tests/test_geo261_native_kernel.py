"""N1a: standalone K codec/exact arithmetic and real bridge shared-code controls.

K builds copy ONLY public K headers/implementations to an isolated directory.
They have no repository include search path and cannot reach a template or host.
The product witness compiles the real web_bridge separately and links exactly
those K objects. Each negative control changes only one K object, then requires
both a K assertion and an actual bridge transaction assertion to fail.
Compile errors, process crashes and unavailable compilers never count as kills.
"""
from __future__ import annotations

import atexit
from fractions import Fraction
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tests import _bridge
from tests import test_engineering_json as existing_codec


class NativeBuild:
    def __init__(self, *, kernel_only=False):
        parent = Path(tempfile.gettempdir()) / "geometry-tests"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="geo261-n1a-", dir=parent)
        atexit.register(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.kernel_only = kernel_only
        self.kernel = self.work / "isolated-kernel"
        self.kernel.mkdir()
        for name in ("types.h", "exact.h", "exact.c", "codec.h", "codec.c", "geometry.h", "geometry.c", "clip.h", "clip.c", "grid.h", "grid.c", "parameters.h", "parameters.c", "parameter_sources.h", "parameter_sources.c", "linear.h", "linear.c", "named_values.h", "named_values.c", "datums.h", "datums.c", "source.h", "source.c", "regions.h", "regions.c", "region_key_sources.h", "region_key_sources.c", "guides.h", "guides.c", "grid_store.h", "grid_store.c", "candidate.h", "candidate.c", "placements.h", "placements.c", "placement_sources.h", "placement_sources.c", "versions.h", "versions.c", "enclosure.h", "enclosure.c", "enclosure_sources.h", "enclosure_sources.c", "document.h", "document.c"):
            shutil.copy2(ROOT / "geometry-core/kernel" / name, self.kernel / name)
        (self.kernel / "internal").mkdir()
        for name in ("linear_definition_sources.h", "linear_definition_sources.c", "version_sources.h", "version_sources.c"):
            shutil.copy2(ROOT / "geometry-core/kernel" / name, self.kernel / name)
        shutil.copy2(ROOT / "geometry-core/kernel/internal/parameter_store.h", self.kernel / "internal/parameter_store.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/named_values.h", self.kernel / "internal/named_values.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/datums.h", self.kernel / "internal/datums.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/regions.h", self.kernel / "internal/regions.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/grid_store.h", self.kernel / "internal/grid_store.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/guides.h", self.kernel / "internal/guides.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/placements.h", self.kernel / "internal/placements.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/versions.h", self.kernel / "internal/versions.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/enclosures.h", self.kernel / "internal/enclosures.h")
        shutil.copy2(ROOT / "geometry-core/kernel/internal/document.h", self.kernel / "internal/document.h")
        if not kernel_only:
            self.host = self.work / "isolated-host"
            self.host.mkdir()
            for name in ("history.h", "history.c", "app_candidate.h", "app_candidate.c"):
                shutil.copy2(ROOT / "geometry-app/native" / name, self.host / name)
            self.woodworking = self.work / "isolated-woodworking" / "native"
            self.woodworking.mkdir(parents=True)
            for name in ("members.h", "members.c", "supports.h", "supports.c", "contacts.h", "contacts.c", "contact_world.h", "contact_world.c", "contact_sources.h", "contact_sources.c", "cut_list.h", "cut_list.c", "member_declaration.h", "member_declaration.c", "definition_sources.h", "definition_sources.c", "world_validation.h", "world_validation.c", "engineering.h", "engineering.c", "engineering_sources.h", "engineering_sources.c", "engineering_operations.h", "engineering_operations.c", "panel_layout.h", "panel_layout.c", "panel_support.h", "panel_support.c", "boundary_policy.h", "boundary_policy.c", "domain_values.h", "section_profile.h", "section_profile.c", "section_profile_sources.h", "section_profile_sources.c", "assembly.h", "assembly.c", "assembly_sources.h", "assembly_sources.c", "finish.h", "finish.c", "derived_placement.h", "derived_placement.c", "finish_sources.h", "finish_sources.c", "grid_application.h", "grid_application.c", "grid_sources.h", "grid_sources.c", "grid_definition_codec.h", "grid_definition_codec.c", "grid_cells.c", "grid_rules.c", "member_reference.h", "member_reference.c", "document.h", "member_placement.h", "obstacles.h"):
                shutil.copy2(ROOT / "geometry-templates/woodworking/native" / name, self.woodworking / name)
        self.windows = os.name == "nt"
        self.suffix = ".exe" if self.windows else ""
        self.logs = []
        self.vcvars = None
        if self.windows:
            vswhere = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
            if not vswhere.exists():
                raise unittest.SkipTest("No MSVC discovery tool for K build")
            install = subprocess.check_output([str(vswhere), "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"], text=True).strip()
            self.vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
            if not self.vcvars.is_file():
                raise unittest.SkipTest("No MSVC compiler for K build")
        else:
            self.cc = shutil.which(os.environ.get("CC", "cc"))
            if not self.cc:
                raise unittest.SkipTest("No C compiler for K build")
        self.exact_object = self.compile(self.kernel / "exact.c", "exact")
        self.codec_object = self.compile(self.kernel / "codec.c", "codec")
        self.geometry_object = self.compile(self.kernel / "geometry.c", "geometry")
        self.clip_object = self.compile(self.kernel / "clip.c", "clip")
        self.grid_object = self.compile(self.kernel / "grid.c", "grid")
        self.parameters_object = self.compile(self.kernel / "parameters.c", "parameters")
        self.parameter_sources_object = self.compile(self.kernel / "parameter_sources.c", "parameter-sources")
        self.linear_object = self.compile(self.kernel / "linear.c", "linear")
        self.named_values_object = self.compile(self.kernel / "named_values.c", "named-values")
        self.datums_object = self.compile(self.kernel / "datums.c", "datums")
        self.source_object = self.compile(self.kernel / "source.c", "source")
        self.candidate_object = self.compile(self.kernel / "candidate.c", "candidate")
        self.placements_object = self.compile(self.kernel / "placements.c", "placements")
        self.placement_sources_object = self.compile(self.kernel / "placement_sources.c", "placement-sources")
        self.versions_object = self.compile(self.kernel / "versions.c", "versions")
        self.enclosure_object = self.compile(self.kernel / "enclosure.c", "enclosure")
        self.enclosure_sources_object = self.compile(self.kernel / "enclosure_sources.c", "enclosure-sources")
        self.kernel_region_key_sources_object = self.compile(self.kernel / "region_key_sources.c", "region-key-sources")
        self.document_object = self.compile(self.kernel / "document.c", "document")
        self.regions_object = self.compile(self.kernel / "regions.c", "regions")
        self.grid_store_object = self.compile(self.kernel / "grid_store.c", "grid-store")
        self.guides_object = self.compile(self.kernel / "guides.c", "guides")
        self.linear_definition_sources_object = self.compile(self.kernel / "linear_definition_sources.c", "linear-definition-sources")
        self.version_sources_object = self.compile(self.kernel / "version_sources.c", "version-sources")
        if not kernel_only:
            self.host_history_object = self.compile(self.host / "history.c", "host-history")
            self.host_candidate_object = self.compile(self.host / "app_candidate.c", "host-candidate")
            self.wood_members_object = self.compile(self.woodworking / "members.c", "wood-members")
            self.wood_supports_object = self.compile(self.woodworking / "supports.c", "wood-supports")
            self.wood_contacts_object = self.compile(self.woodworking / "contacts.c", "wood-contacts")
            self.wood_contact_world_object = self.compile(self.woodworking / "contact_world.c", "wood-contact-world")
            self.wood_contact_sources_object = self.compile(self.woodworking / "contact_sources.c", "wood-contact-sources")
            self.wood_cut_list_object = self.compile(self.woodworking / "cut_list.c", "wood-cut-list")
            self.wood_member_declaration_object = self.compile(self.woodworking / "member_declaration.c", "wood-member-declaration")
            self.wood_definition_sources_object = self.compile(self.woodworking / "definition_sources.c", "wood-definition-sources")
            self.wood_world_validation_object = self.compile(self.woodworking / "world_validation.c", "wood-world-validation")
            self.wood_boundary_policy_object = self.compile(self.woodworking / "boundary_policy.c", "wood-boundary-policy")
            self.wood_engineering_object = self.compile(self.woodworking / "engineering.c", "wood-engineering")
            self.wood_engineering_sources_object = self.compile(self.woodworking / "engineering_sources.c", "wood-engineering-sources")
            self.wood_engineering_operations_object = self.compile(self.woodworking / "engineering_operations.c", "wood-engineering-operations")
            self.wood_panel_layout_object = self.compile(self.woodworking / "panel_layout.c", "wood-panel-layout")
            self.wood_panel_support_object = self.compile(self.woodworking / "panel_support.c", "wood-panel-support")
            self.wood_section_profile_object = self.compile(self.woodworking / "section_profile.c", "wood-section-profile")
            self.wood_section_profile_sources_object = self.compile(self.woodworking / "section_profile_sources.c", "wood-section-profile-sources")
            self.wood_assembly_object = self.compile(self.woodworking / "assembly.c", "wood-assembly")
            self.wood_assembly_sources_object = self.compile(self.woodworking / "assembly_sources.c", "wood-assembly-sources")
            self.wood_finish_object = self.compile(self.woodworking / "finish.c", "wood-finish")
            self.wood_derived_placement_object = self.compile(self.woodworking / "derived_placement.c", "wood-derived-placement")
            self.wood_finish_sources_object = self.compile(self.woodworking / "finish_sources.c", "wood-finish-sources")
            self.wood_grid_application_object = self.compile(self.woodworking / "grid_application.c", "wood-grid-application")
            self.wood_grid_sources_object = self.compile(self.woodworking / "grid_sources.c", "wood-grid-sources")
            self.wood_grid_definition_codec_object = self.compile(self.woodworking / "grid_definition_codec.c", "wood-grid-definition-codec")
            self.wood_grid_cells_object = self.compile(self.woodworking / "grid_cells.c", "wood-grid-cells")
            self.wood_grid_rules_object = self.compile(self.woodworking / "grid_rules.c", "wood-grid-rules")
            self.wood_member_reference_object = self.compile(self.woodworking / "member_reference.c", "wood-member-reference")
        exact_source = self.work / "exact-client.c"
        shutil.copy2(ROOT / "tests/geo261_exact_harness.c", exact_source)
        self.exact_client = self.compile(exact_source, "exact-client")
        codec_source = self.work / "codec-client.c"
        source = existing_codec.HARNESS.replace('#include "engineering_json.inc"', '#include "codec.h"')
        source = source.replace("EngJson", "GeoJson")
        source = re.sub(r"\beng_(json_|sha256|base64_)", r"geo_\1", source)
        codec_source.write_text(source, encoding="utf-8")
        self.codec_client = self.compile(codec_source, "codec-client")
        self.exact = self.link("exact-client", [self.exact_client, self.exact_object])
        self.codec = self.link("codec-client", [self.codec_client, self.codec_object])
        self.bridge_object = None
        self.bridge_exe = None
        self.cli_exe = None
        self.model_base_exe = None
        self.model_base_object = None

    def run_build(self, args):
        if self.windows:
            script = self.work / ("build-%d.cmd" % len(self.logs))
            script.write_text('@echo off\ncall "' + str(self.vcvars) + '" >nul\n' + subprocess.list2cmdline(args) + '\n', encoding="utf-8")
            command = ["cmd", "/d", "/c", str(script)]
        else:
            command = args
        run = subprocess.run(command, cwd=self.work, capture_output=True, text=True, errors="replace", timeout=300)
        self.logs.append({"command": command, "arguments": list(args), "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
        (self.work / "build-log.json").write_text(json.dumps(self.logs, indent=2), encoding="utf-8")
        if run.returncode:
            raise AssertionError("Native compile/link failed (not a valid negative control):\n" + run.stdout + run.stderr)

    def compile(self, source, name, defines=()):
        out = self.work / (name + (".obj" if self.windows else ".o"))
        if self.windows:
            args = ["cl", "/nologo", "/utf-8", "/Od", "/W3", "/c", "/I" + str(self.kernel), "/Fo:" + str(out)]
            # Product CLI excludes GDI; codec clients must retain _WIN32 so
            # their stdout stays binary during base64 round-trip assertions.
            if source in (ROOT / "geometry-web/web_bridge.c", ROOT / "current_geometry.c", ROOT / "geometry-core/model_base.c"):
                args.append("/U_WIN32")
            args += ["/D" + d for d in defines] + [str(source)]
        else:
            args = [self.cc, "-std=c11", "-O0", "-Werror=implicit-function-declaration", "-I", str(self.kernel)]
            args += ["-D" + d for d in defines] + ["-c", str(source), "-o", str(out)]
        self.run_build(args)
        return out

    def link(self, name, objects):
        out = self.work / (name + self.suffix)
        if self.windows:
            args = ["cl", "/nologo", *map(str, objects), "/Fe:" + str(out), "/link", "/STACK:16777216"]
        else:
            args = [self.cc, *map(str, objects), "-lm", "-o", str(out)]
        self.run_build(args)
        return out

    def bridge(self):
        if self.kernel_only:
            raise AssertionError("K-only build has no host or woodworking product")
        if self.bridge_object is None:
            self.bridge_object = self.compile(ROOT / "geometry-web/web_bridge.c", "product-bridge", ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1", "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
            self.bridge_exe = self.link("product-bridge", [self.bridge_object, *self.product_objects()])
        return self.bridge_exe

    def product_objects(self):
        if self.kernel_only:
            raise AssertionError("K-only build has no host or woodworking product")
        return [*self.kernel_objects(), self.wood_members_object, self.wood_supports_object, self.wood_contacts_object, self.wood_contact_world_object, self.wood_contact_sources_object, self.wood_cut_list_object, self.wood_member_declaration_object, self.wood_definition_sources_object, self.wood_world_validation_object, self.wood_boundary_policy_object, self.wood_engineering_object, self.wood_engineering_sources_object, self.wood_engineering_operations_object, self.wood_panel_layout_object, self.wood_panel_support_object, self.wood_section_profile_object, self.wood_section_profile_sources_object, self.wood_assembly_object, self.wood_assembly_sources_object, self.wood_finish_object, self.wood_derived_placement_object, self.wood_finish_sources_object, self.wood_grid_application_object, self.wood_grid_sources_object, self.wood_grid_definition_codec_object, self.wood_grid_cells_object, self.wood_grid_rules_object, self.wood_member_reference_object, self.host_history_object, self.host_candidate_object]

    def cli(self):
        if self.kernel_only:
            raise AssertionError("K-only build has no host or woodworking product")
        if self.cli_exe is None:
            obj = self.compile(ROOT / "current_geometry.c", "product-cli", ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1", "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
            self.cli_exe = self.link("product-cli", [obj, *self.product_objects()])
        return self.cli_exe

    def model_base(self):
        if self.kernel_only:
            raise AssertionError("K-only build has no host or woodworking product")
        if self.model_base_exe is None:
            self.model_base_object = self.compile(ROOT / "geometry-core/model_base.c", "product-model-base", ["GEOMETRY_KERNEL_EXTERNAL=1", "GEOMETRY_WOODWORKING_EXTERNAL=1", "GEOMETRY_HOST_HISTORY_EXTERNAL=1", "GEOMETRY_HOST_CANDIDATE_EXTERNAL=1"])
            self.model_base_exe = self.link("product-model-base", [self.model_base_object, *self.product_objects()])
        return self.model_base_exe

    def kernel_objects(self):
        return [self.exact_object, self.codec_object, self.geometry_object, self.clip_object, self.grid_object,
                self.parameters_object, self.parameter_sources_object, self.linear_object, self.named_values_object, self.datums_object, self.source_object, self.candidate_object, self.placements_object, self.placement_sources_object, self.versions_object, self.enclosure_object, self.enclosure_sources_object, self.document_object, self.regions_object, self.kernel_region_key_sources_object, self.grid_store_object, self.guides_object, self.linear_definition_sources_object, self.version_sources_object]

    def mutant(self, module, before, after, client_object=None):
        text = (self.kernel / (module + ".c")).read_text(encoding="utf-8")
        if text.count(before) != 1:
            raise AssertionError("Negative control did not hit exactly once: " + module)
        source = self.work / (module + "-mutant.c")
        source.write_text(text.replace(before, after), encoding="utf-8")
        changed = self.compile(source, module + "-mutant")
        self.bridge()
        if client_object is None:
            client_object = self.exact_client if module == "exact" else self.codec_client
        dependencies = [self.geometry_object] if module == "grid" else []
        if module == "parameters":
            dependencies = [self.codec_object, self.exact_object, self.geometry_object]
        if module == "linear":
            dependencies = [self.exact_object, self.geometry_object, self.named_values_object]
        if module == "named_values":
            dependencies = [self.geometry_object, self.linear_object, self.exact_object]
        if module == "datums":
            dependencies = [self.geometry_object, self.linear_object, self.exact_object]
        if module == "guides":
            dependencies = [self.linear_object,self.exact_object,self.datums_object,self.geometry_object]
        if module in ("regions", "clip"):
            dependencies = [self.geometry_object]
        if module == "grid_store":
            dependencies = [self.grid_object, self.geometry_object, self.codec_object]
        client = self.link(module + "-mutant-client", [client_object, changed, *dependencies])
        original = getattr(self, module + "_object")
        objects = self.product_objects()
        if objects.count(original) != 1:
            raise AssertionError("Expected one production object for " + module)
        product = self.link(module + "-mutant-bridge", [self.bridge_object,
            *[changed if obj == original else obj for obj in objects]])
        return client, product


_BUILD = None
def native():
    global _BUILD
    if _BUILD is None:
        _BUILD = NativeBuild()
    return _BUILD


_KERNEL_ONLY_BUILD = None
def kernel_only_native():
    """Compile K with neither H nor W source directories in the build closure."""
    global _KERNEL_ONLY_BUILD
    if _KERNEL_ONLY_BUILD is None:
        _KERNEL_ONLY_BUILD = NativeBuild(kernel_only=True)
    return _KERNEL_ONLY_BUILD


class KernelCodec(existing_codec.EngineeringJson):
    """R381 extends the existing quote acceptance with actual K writer work.

    The scalar oracle is the exact string writer at 11eddfdb. All other bytes
    come from the current product; instrumentation adds only a call counter.
    No product counter, wall-time budget or source/decode cache is introduced.
    """
    @classmethod
    def setUpClass(cls):
        build = kernel_only_native()
        cls.work = build.work
        cls.exe = build.codec
        cls.compiler_output = "K-only independent compilation; isolated public source closure"

    BASE_STRING_WRITER = r'''static void geo_json_write_string(GeoJsonWriter *w,const char *s) {
    size_t p=0,n=strlen(s);
    static const char hex[]="0123456789abcdef";
    geo_json_write(w,"\"",1);
    while(p<n && w->ok) {
        unsigned char c=(unsigned char)s[p];
        const char *escape=NULL;
        if(c=='"')escape="\\\"";
        else if(c=='\\')escape="\\\\";
        else if(c=='\b')escape="\\b";
        else if(c=='\f')escape="\\f";
        else if(c=='\n')escape="\\n";
        else if(c=='\r')escape="\\r";
        else if(c=='\t')escape="\\t";
        if(escape){geo_json_write(w,escape,2);p++;}
        else if(c<0x20) {
            char buf[6]={'\\','u','0','0',hex[c>>4],hex[c&15]};geo_json_write(w,buf,6);p++;
        } else {
            size_t k=geo_utf8_scalar((const unsigned char*)s+p,n-p);
            if(!k){w->ok=0;break;}
            geo_json_write(w,s+p,k);p+=k;
        }
    }
    geo_json_write(w,"\"",1);
}
'''
    WRITE_ENTRY = "static void geo_json_write(GeoJsonWriter *w,const char *text,size_t n) {\n"
    COUNTED_ENTRY = "static size_t r381_json_write_calls;\n" + WRITE_ENTRY + "    ++r381_json_write_calls;\n"
    COUNTER_API = ("\nvoid r381_json_write_reset(void){r381_json_write_calls=0;}\n"
                   "size_t r381_json_write_count(void){return r381_json_write_calls;}\n")
    ASCII_GUARD_REVERTS = (
        ("R381_JSON_ASCII_ALIAS_GUARD_REVERT",
         "if(separate && n-p<w->capacity-w->used &&",
         "if(1 && n-p<w->capacity-w->used &&"),
        ("R381_JSON_ASCII_CAPACITY_GUARD_REVERT",
         "separate && n-p<w->capacity-w->used &&",
         "separate && 1 &&"),
        ("R381_JSON_ASCII_UTF8_GUARD_REVERT",
         "c>=0x20 && c<0x80 &&", "c>=0x20 && 1 &&"),
    )
    HARNESS = r'''
#include "codec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
void r381_json_write_reset(void);
size_t r381_json_write_count(void);
int main(int argc,char **argv) {
    if(argc!=5)return 70;
#ifdef _WIN32
    _setmode(_fileno(stdout),_O_BINARY);
#endif
    FILE *f=fopen(argv[2],"rb");if(!f)return 71;
    if(fseek(f,0,SEEK_END))return 72;
    long raw=ftell(f);if(raw<0)return 72;rewind(f);
    size_t n=(size_t)raw;char *data=malloc(n+1);if(!data)return 73;
    if(fread(data,1,n,f)!=n)return 74;fclose(f);data[n]=0;
    int canonical=!strcmp(argv[1],"canonical");
    if(!canonical&&strcmp(argv[1],"quote"))return 75;
    long alias=strtol(argv[4],NULL,10);if(alias < -1||alias>64||canonical&&alias>=0)return 76;
    GeoJson j;if(canonical&&!geo_json_parse_n(&j,data,n))return 77;
    const char *cursor=argv[3];
    while(*cursor){
        char *end;size_t capacity=(size_t)strtoul(cursor,&end,10);
        if(end==cursor||(*end&&*end!=',')||capacity>1048576)return 78;
        size_t span=capacity;
        if(alias>=0&&(size_t)alias+n+1>span)span=(size_t)alias+n+1;
        size_t size=span+32;unsigned char *buffer=malloc(size);if(!buffer)return 79;
        memset(buffer,0xa5,size);char *out=(char*)buffer+16;const char *input=data;
        if(alias>=0){memcpy(out+alias,data,n+1);input=out+alias;}
        r381_json_write_reset();
        int ok=canonical?geo_json_canonical(&j,0,out,capacity):geo_json_quote(input,out,capacity);
        printf("{\"ok\":%d,\"writes\":%zu,\"capacity\":%zu,\"buffer\":\"",ok,r381_json_write_count(),capacity);
        for(size_t i=0;i<size;++i)printf("%02x",(unsigned)buffer[i]);
        puts("\"}");free(buffer);cursor=*end?end+1:end;
    }
    if(canonical)geo_json_free(&j);free(data);return 0;
}
'''

    @classmethod
    def setup_ascii_work(cls):
        build = kernel_only_native()
        cls.work = build.work
        cls.source = (ROOT / "geometry-core/kernel/codec.c").read_text(encoding="utf-8")
        start = cls.source.index("static void geo_json_write_string(")
        end = cls.source.index("int geo_json_quote(", start)
        cls.scalar_source = cls.source[:start] + cls.BASE_STRING_WRITER + cls.source[end:]
        # With the run branch removed, the entire production file, not only its
        # successful outputs, must match the scalar reference transformation.
        cls.has_ascii_run = "/* R381_ASCII_RUN_BEGIN:" in cls.source
        if cls.has_ascii_run:
            begin = cls.source.index("/* R381_ASCII_RUN_BEGIN:")
            finish = cls.source.index("/* R381_ASCII_RUN_END */", begin)
            if cls.source.count("/* R381_ASCII_RUN_BEGIN:") != 1 or cls.source.count("/* R381_ASCII_RUN_END */") != 1:
                raise AssertionError("R381_JSON_ASCII_RUN_REVERT must have one exact product branch")
            begin = cls.source.rfind("\n", 0, begin) + 1
            finish = cls.source.index("\n", finish) + 1
            if cls.source[:begin] + cls.source[finish:] != cls.scalar_source:
                raise AssertionError("R381_JSON_ASCII_RUN_REVERT must preserve every other product byte")
        elif cls.source != cls.scalar_source:
            raise AssertionError("R381 scalar reference differs from the fixed base string writer")
        client_path = cls.work / "r381-json-ascii-client.c"
        client_path.write_text(cls.HARNESS, encoding="utf-8")
        client = build.compile(client_path, "r381-json-ascii-client")
        cls.executables = {}
        variants = [("actual", cls.source), ("R381_JSON_ASCII_RUN_REVERT", cls.scalar_source)]
        if cls.has_ascii_run:
            for label, before, after in cls.ASCII_GUARD_REVERTS:
                if cls.source.count(before) != 1:
                    raise AssertionError(label + " must change one actual product guard")
                changed = cls.source.replace(before, after)
                if changed.count(after) != 1 or changed.replace(after, before) != cls.source:
                    raise AssertionError(label + " must preserve every other product byte")
                variants.append((label, changed))
        for label, source in variants:
            if source.count(cls.WRITE_ENTRY) != 1:
                raise AssertionError("R381 counter must hit one real geo_json_write entry")
            counted = source.replace(cls.WRITE_ENTRY, cls.COUNTED_ENTRY) + cls.COUNTER_API
            if counted[:-len(cls.COUNTER_API)].replace(cls.COUNTED_ENTRY, cls.WRITE_ENTRY) != source:
                raise AssertionError("R381 counter must preserve every other product byte")
            path = cls.work / ("r381-json-" + label + ".c")
            path.write_text(counted, encoding="utf-8")
            obj = build.compile(path, "r381-json-" + label)
            cls.executables[label] = build.link("r381-json-" + label, [client, obj])

    def codec_rows(self, executable, mode, data, capacities, alias=-1):
        path = self.work / "r381-json-input.bin"
        path.write_bytes(data)
        result = subprocess.run([str(executable), mode, str(path), ",".join(map(str, capacities)), str(alias)],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, "R381 codec harness failed: " + result.stderr.decode(errors="replace"))
        self.assertEqual(b"", result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(list(capacities), [row["capacity"] for row in rows])
        return rows

    def check_quote_and_canonical_retain_every_buffer_byte(self):
        valid = ["", "plain ASCII", "\x7f" * 31,
                 "a" * 37 + "\n\"\\" + "b" * 19 + "é中😀" + "c" * 29,
                 "".join(chr(i) for i in range(1, 128)),
                 "left" + "\u0080\u07ff\u0800\ud7ff\ue000\uffff\U00010000\U0010ffff" + "right"]
        cases = []
        for value in valid:
            expected = json.dumps(value, ensure_ascii=False).encode("utf-8")
            cases.append(("quote", value.encode("utf-8"), expected))
            for escaped in (False, True):
                cases.append(("canonical", json.dumps(value, ensure_ascii=escaped).encode("utf-8"), expected))
        nested = {"plain-key": ["a" * 37, "é中😀", "\n\"\\"], "z": {"\x7f": -2**63}, "a": True}
        cases.append(("canonical", json.dumps(nested, ensure_ascii=False).encode("utf-8"),
                      json.dumps(nested, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")))
        invalid = [b"\x80", b"\xc0\xaf", b"\xe0\x80\xaf", b"\xed\xa0\x80", b"\xf0\x80\x80\xaf",
                   b"\xf4\x90\x80\x80", b"\xf5\x80\x80\x80", b"\xe2\x82", b"\xf0\x90\x80"]
        cases += [("quote", b"ASCII-prefix-" + bad + b"-tail", None) for bad in invalid]
        for mode, data, expected in cases:
            capacities = range((len(expected) if expected is not None else len(data) * 6) + 3)
            with self.subTest(mode=mode, data=data):
                actual = self.codec_rows(self.executables["actual"], mode, data, capacities)
                scalar = self.codec_rows(self.executables["R381_JSON_ASCII_RUN_REVERT"], mode, data, capacities)
                self.assertEqual([{k: v for k, v in row.items() if k != "writes"} for row in scalar],
                                 [{k: v for k, v in row.items() if k != "writes"} for row in actual],
                                 "R381_JSON_ASCII_FULL_BUFFER")
                for row in actual:
                    raw = bytes.fromhex(row["buffer"])
                    self.assertEqual(b"\xa5" * 16, raw[:16], "R381_JSON_ASCII_LEFT_CANARY")
                    self.assertEqual(b"\xa5" * 16, raw[-16:], "R381_JSON_ASCII_RIGHT_CANARY")
                    self.assertEqual(int(expected is not None and row["capacity"] > len(expected)), row["ok"])
                    if row["ok"]:
                        self.assertEqual(expected + b"\0", raw[16:16 + len(expected) + 1])
        # Public quote accepts pointer arguments without a non-alias contract.
        # Retain the scalar behavior even when expansion overwrites later input.
        for data in (b"A" * 37, b"left\n\"\\right-" + "é中😀".encode("utf-8"), b"prefix-\xe2\x82"):
            for alias in (0, 1, 2, 4, 16):
                capacities = range(len(data) * 2 + 10)
                with self.subTest(alias=alias, data=data):
                    actual = self.codec_rows(self.executables["actual"], "quote", data, capacities, alias)
                    scalar = self.codec_rows(self.executables["R381_JSON_ASCII_RUN_REVERT"], "quote", data, capacities, alias)
                    self.assertEqual([{k: v for k, v in row.items() if k != "writes"} for row in scalar],
                                     [{k: v for k, v in row.items() if k != "writes"} for row in actual],
                                     "R381_JSON_ASCII_ALIAS_FULL_BUFFER")
                    for before, after in zip(scalar, actual):
                        # Sharing an allocation does not imply overlapping byte
                        # ranges: input starts at out+alias, output ends at capacity.
                        if after["capacity"] > alias:
                            self.assertEqual(before, after, "R381_JSON_ASCII_ALIAS_SCALAR_WORK")

    def assert_ascii_alias_guard(self, executable, scalar_executable):
        # Overlapping memcpy can appear to work on a particular libc. Retaining
        # the exact scalar work proves the fast path did not attempt that copy.
        data = b"a" * 64
        actual = self.codec_rows(executable, "quote", data, [len(data) + 3], alias=4)
        scalar = self.codec_rows(scalar_executable, "quote", data, [len(data) + 3], alias=4)
        self.assertEqual(scalar, actual, "R381_JSON_ASCII_ALIAS_SCALAR_WORK")

    def assert_ascii_capacity_guard(self, executable, scalar_executable):
        data = b"a" * 64
        actual = self.codec_rows(executable, "quote", data, [4])
        scalar = self.codec_rows(scalar_executable, "quote", data, [4])
        self.assertEqual([{k: v for k, v in row.items() if k != "writes"} for row in scalar],
                         [{k: v for k, v in row.items() if k != "writes"} for row in actual],
                         "R381_JSON_ASCII_CAPACITY_FULL_BUFFER")

    def assert_ascii_utf8_guard(self, executable, scalar_executable):
        data = b"ASCII-prefix-\xc0\xaf-tail"
        actual = self.codec_rows(executable, "quote", data, [len(data) + 3])
        scalar = self.codec_rows(scalar_executable, "quote", data, [len(data) + 3])
        self.assertEqual([{k: v for k, v in row.items() if k != "writes"} for row in scalar],
                         [{k: v for k, v in row.items() if k != "writes"} for row in actual],
                         "R381_JSON_ASCII_UTF8_FULL_BUFFER")

    def assert_ascii_write_work(self, executable):
        for value, budget in (("a" * 64, 3), ("b" * 4096, 3), ("\x7f" * 64, 3),
                              ("a" * 64 + "\n" + "中" + "b" * 64, 6)):
            expected = json.dumps(value, ensure_ascii=False).encode("utf-8")
            for mode, data in (("quote", value.encode("utf-8")), ("canonical", expected)):
                row = self.codec_rows(executable, mode, data, [len(expected) + 1])[0]
                self.assertEqual(1, row["ok"])
                raw = bytes.fromhex(row["buffer"])
                self.assertEqual(expected + b"\0", raw[16:-16])
                self.assertLessEqual(row["writes"], budget,
                    "R381_JSON_ASCII_WRITE_WORK mode=%s input_bytes=%d writes=%d budget=%d" %
                    (mode, len(data), row["writes"], budget))

    def check_ascii_run_work_is_bounded_by_runs(self):
        self.assert_ascii_write_work(self.executables["actual"])

    def check_named_ascii_run_revert_is_normal_assertion_0_1_0(self):
        self.assertTrue(self.has_ascii_run, "R381_JSON_ASCII_RUN_REVERT requires the product run branch")
        code = ("from pathlib import Path; import sys; "
                "from tests.test_geo261_native_kernel import KernelCodec; "
                "case=KernelCodec(); case.work=Path(sys.argv[1]); "
                "case.assert_ascii_write_work(Path(sys.argv[2]))")
        for phase, label, expected in (("baseline", "actual", 0),
                                       ("R381_JSON_ASCII_RUN_REVERT", "R381_JSON_ASCII_RUN_REVERT", 1),
                                       ("restored", "actual", 0)):
            run = subprocess.run([sys.executable, "-c", code, str(self.work), str(self.executables[label])],
                                 cwd=ROOT, capture_output=True, timeout=20)
            self.assertEqual(expected, run.returncode, phase + ": " + run.stderr.decode(errors="replace"))
            if expected:
                self.assertIn(b"AssertionError:", run.stderr)
                self.assertIn(b"R381_JSON_ASCII_WRITE_WORK", run.stderr)
            else:
                self.assertEqual(b"", run.stderr)
            print("R381_JSON_ASCII_RUN_REVERT phase=%s exit=%d" % (phase, run.returncode))

    def check_named_ascii_guard_reverts_are_normal_assertion_0_1_0(self):
        self.assertTrue(self.has_ascii_run, "R381 ASCII guard reverts require the product run branch")
        code = ("from pathlib import Path; import sys; "
                "from tests.test_geo261_native_kernel import KernelCodec; "
                "case=KernelCodec(); case.work=Path(sys.argv[1]); "
                "getattr(case,sys.argv[2])(Path(sys.argv[3]),Path(sys.argv[4]))")
        controls = (
            ("R381_JSON_ASCII_ALIAS_GUARD_REVERT", "assert_ascii_alias_guard", "R381_JSON_ASCII_ALIAS_SCALAR_WORK"),
            ("R381_JSON_ASCII_CAPACITY_GUARD_REVERT", "assert_ascii_capacity_guard", "R381_JSON_ASCII_CAPACITY_FULL_BUFFER"),
            ("R381_JSON_ASCII_UTF8_GUARD_REVERT", "assert_ascii_utf8_guard", "R381_JSON_ASCII_UTF8_FULL_BUFFER"),
        )
        for name, method, marker in controls:
            for phase, label, expected in (("baseline", "actual", 0),
                                           (name, name, 1),
                                           ("restored", "actual", 0)):
                run = subprocess.run([sys.executable, "-c", code, str(self.work), method,
                                      str(self.executables[label]),
                                      str(self.executables["R381_JSON_ASCII_RUN_REVERT"])],
                                     cwd=ROOT, capture_output=True, timeout=20)
                self.assertEqual(expected, run.returncode, phase + ": " + run.stderr.decode(errors="replace"))
                if expected:
                    self.assertIn(b"AssertionError:", run.stderr)
                    self.assertIn(marker.encode("ascii"), run.stderr)
                else:
                    self.assertEqual(b"", run.stderr)
                print("%s phase=%s exit=%d" % (name, phase, run.returncode))

    def test_quote_matches_canonical_strings(self):
        # Retain the original independent Python/UTF-8 assertions and extend
        # this same quote acceptance; the discovered suite remains 13 tests.
        super().test_quote_matches_canonical_strings()
        self.setup_ascii_work()
        self.check_quote_and_canonical_retain_every_buffer_byte()
        self.check_ascii_run_work_is_bounded_by_runs()
        self.check_named_ascii_run_revert_is_normal_assertion_0_1_0()
        self.check_named_ascii_guard_reverts_are_normal_assertion_0_1_0()


def exact_call(exe, operation, a, b=None):
    args = [str(exe), str(operation), *map(str, a)]
    if b is not None:
        args += list(map(str, b))
    run = subprocess.run(args, capture_output=True, text=True, timeout=10)
    if run.returncode:
        raise AssertionError("K process failed, not a numerical rejection: " + run.stderr)
    return tuple(map(int, run.stdout.split()))


class KernelExact(unittest.TestCase):
    def test_fractional_arithmetic_matches_independent_fraction_oracle(self):
        rng = random.Random(261)
        for operation in range(4):
            for _ in range(40):
                a, b = Fraction(rng.randint(-10000, 10000), rng.randint(1, 100)), Fraction(rng.randint(1, 10000), rng.randint(1, 100))
                expected = (lambda: a+b, lambda: a-b, lambda: a*b, lambda: a/b)[operation]()
                result = exact_call(kernel_only_native().exact, operation, (a.numerator, a.denominator, 0), (b.numerator, b.denominator, 0))
                self.assertEqual((0, expected.numerator, expected.denominator, 0), result)

    def test_cross_cancellation_precedes_checked_multiplication(self):
        self.assertEqual((0, 1, 1, 1), exact_call(kernel_only_native().exact, 2, (2**63-1, 3, 1), (3, 2**63-1, 0)))
        self.assertEqual((0, 0, 1, 0), exact_call(kernel_only_native().exact, 1, (-17, 23, 0), (-17, 23, 0)))
        self.assertEqual((0, -2, 3, 0), exact_call(kernel_only_native().exact, 3, (2, 7, 1), (-3, 7, 1)))

    def test_overflow_unit_failures_preserve_output(self):
        cases = [(0, (2**63-1, 1, 0), (1, 1, 0), 3),
                 (1, (-(2**63-1), 1, 0), (1, 1, 0), 3),
                 (2, (2**63-1, 1, 0), (2, 1, 0), 2),
                 (0, (1, 1, 0), (1, 1, 1), 4),
                 (2, (1, 1, 1), (1, 1, 1), 5),
                 (3, (1, 1, 0), (0, 1, 0), 6),
                 (3, (1, 1, 0), (1, 1, 1), 7),
                 (9, (1, 1, 0), (1, 1, 0), 8)]
        for operation, a, b, error in cases:
            with self.subTest(operation=operation, a=a, b=b):
                self.assertEqual((error, 37, 41, 1), exact_call(kernel_only_native().exact, operation, a, b))

    def test_public_normalization_rejects_invalid_values(self):
        for value, expected in [((0, 19, 0), (0, 0, 1, 0)), ((-4, 6, 1), (0, -2, 3, 1)),
                                ((-2**63, 1, 0), (1, 37, 41, 1)), ((1, 0, 0), (9, 37, 41, 1)),
                                ((1, -1, 0), (9, 37, 41, 1)), ((1, 1, 4), (10, 37, 41, 1))]:
            with self.subTest(value=value):
                self.assertEqual(expected, exact_call(kernel_only_native().exact, "normalize", value))


def product_preview(exe, expression, *, duplicate=False):
    with _bridge.BridgeSession(exe) as session:
        if not session.command("reset")["ok"]:
            raise AssertionError("bridge reset failed")
        read = session.command("engineering-read")
        if not read["ok"]:
            raise AssertionError(read)
        card = {"op": "put-parameter", "value": {"id": 1, "name": "exact witness", "fields": [{"id": 1, "name": "length", "type": "dimension", "input": expression}]}}
        request = {"schema": "engineering-transaction/1", "expectedRevision": read["revision"], "operations": [card]}
        raw = json.dumps(request)
        if duplicate:
            raw = raw.replace('{"schema":', '{"schema":"engineering-transaction/1","schema":', 1)
        path = native().work / "production-witness.json"
        path.write_text(raw, encoding="utf-8")
        response = session.command("engineering-preview " + str(path))
        return response


class ProductSharedImplementation(unittest.TestCase):
    def assert_exact_witness(self, client, bridge):
        self.assertEqual((0, 2, 1, 1), exact_call(client, 2, (2**63-1, 3, 1), (6, 2**63-1, 0)))
        self.assert_product_exact(bridge)

    def assert_product_exact(self, bridge):
        response = product_preview(bridge, "=9223372036854775807 mm/3*(6/9223372036854775807)")
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["preview"]["valid"], response)
        value = response["preview"]["after"]["parameters"][0]["fields"][0]["value"]
        self.assertEqual({"num": "2", "den": "1", "unit": "mm"}, value)

    def assert_codec_witness(self, client):
        path = native().work / "duplicate.json"
        path.write_text('{"a":1,"\\u0061":2}', encoding="utf-8")
        run = subprocess.run([str(client), "canonical", str(path)], capture_output=True, text=True, timeout=10)
        self.assertIn(run.returncode, (0, 1), "crash is not a parser result")
        self.assertEqual(1, run.returncode)
        self.assertIn("Duplicate JSON object key", run.stderr)

    def assert_product_codec(self, bridge):
        response = product_preview(bridge, "1", duplicate=True)
        self.assertFalse(response["ok"], response)
        self.assertIn("Duplicate JSON object key", response["error"])

    def test_exact_negative_control_changes_both_kernel_and_product(self):
        build = native()
        self.assert_exact_witness(build.exact, build.bridge())
        client, bridge = build.mutant("exact", "g=geo_exact_gcd(a.num,b.den);a.num/=g;b.den/=g;", "g=1;a.num/=g;b.den/=g;")
        self.assertNotEqual(0, exact_call(client, 2, (2**63-1, 3, 1), (6, 2**63-1, 0))[0])
        response = product_preview(bridge, "=9223372036854775807 mm/3*(6/9223372036854775807)")
        self.assertTrue(response["ok"], response)
        self.assertFalse(response["preview"]["valid"], response)
        self.assertIn("PRECISION", json.dumps(response))
        self.assert_exact_witness(build.exact, build.bridge())

    def test_codec_negative_control_changes_both_kernel_and_product(self):
        build = native()
        self.assert_codec_witness(build.codec)
        self.assert_product_codec(build.bridge())
        client, bridge = build.mutant("codec", "if(strcmp(order[i-1].key,order[i].key)==0)", "if(0)")
        path = build.work / "duplicate.json"
        run = subprocess.run([str(client), "canonical", str(path)], capture_output=True, text=True, timeout=10)
        self.assertEqual(0, run.returncode, run.stderr)
        response = product_preview(bridge, "1", duplicate=True)
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["preview"]["valid"], response)
        self.assert_codec_witness(build.codec)
        self.assert_product_codec(build.bridge())


if __name__ == "__main__":
    unittest.main(verbosity=2)
