"""R43 geometry belongs to K and is actually shared by the W consumer.

Missing ownership is a named assertion before compilation. Semantic controls
must compile, then fail independent K/W assertions; setup failures are invalid.
All withdrawals use temporary source copies and print complete diffs/results.
"""
from __future__ import annotations

import difflib
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
KERNEL="geometry-core/kernel"
WOOD="geometry-templates/woodworking/native"
APIS=("geo_rect_section_union","geo_interval_edge_coverage")
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def without_comments(text):
    return re.sub(r"/\*.*?\*/|//[^\n]*","",text,flags=re.S)


def function_span(text,name):
    matches=list(re.finditer(r"^[\w *]+\b"+re.escape(name)+r"\s*\([^;{}]*\)\s*\{",text,re.M))
    assert len(matches)==1,"X3_R43_KERNEL_OWNERSHIP: expected one definition of "+name
    match=matches[0];depth=1;end=match.end()
    while depth and end<len(text):
        depth+=(text[end]=="{")-(text[end]=="}");end+=1
    assert depth==0,"X3_R43_KERNEL_OWNERSHIP: unterminated definition of "+name
    return match.start(),end


def owned(root):
    header=without_comments((root/KERNEL/"geometry.h").read_text(encoding="utf-8"))
    core=without_comments((root/KERNEL/"geometry.c").read_text(encoding="utf-8"))
    assert re.search(r"}\s*GeoAxisBox2\s*;",header),"X3_R43_KERNEL_OWNERSHIP: neutral box carrier missing"
    for name in APIS:
        assert len(re.findall(r"\b"+name+r"\s*\([^;{}]*\)\s*;",header))==1,"X3_R43_KERNEL_OWNERSHIP: public declaration missing: "+name
        function_span(core,name)
    source=without_comments((root/WOOD/"panel_support.c").read_text(encoding="utf-8"))
    assert not re.search(r"\bpf_support_(?:union|width)\s*\(",source),"X3_R43_TEMPLATE_OWNERSHIP: private geometry copy returned"
    start,end=function_span(source,"wood_panel_support_evaluate")
    evaluator=source[start:end]
    for name,count in zip(APIS,(1,2)):
        assert len(re.findall(r"\b"+name+r"\s*\(",evaluator))==count,"X3_R43_TEMPLATE_OWNERSHIP: evaluator must consume "+name


def raw_run(command,cwd,label,env=None):
    result=subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,text=True,timeout=120)
    print(json.dumps({"witness":label,"command":list(map(str,command)),"cwd":str(cwd),"exit":result.returncode}),flush=True)
    print("stdout:",flush=True);print(result.stdout,end="",flush=True)
    print("stderr:",flush=True);print(result.stderr,end="",flush=True)
    return result


def print_diff(label,before,after,path):
    print(json.dumps({"withdrawal":label,"path":path,
        "beforeSha256":hashlib.sha256(before.encode()).hexdigest(),
        "afterSha256":hashlib.sha256(after.encode()).hexdigest()}),flush=True)
    print("".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile="a/"+path,tofile="b/"+path)),end="",flush=True)


class KernelBuild:
    """Compile only copied geometry.c/.h/types.h plus the independent client."""
    def __init__(self,test):
        self.test=test;temporary=tempfile.TemporaryDirectory(prefix="x3-r43-k-only-")
        test.addCleanup(temporary.cleanup);self.work=Path(temporary.name)
        for name in ("geometry.c","geometry.h","types.h"):
            shutil.copyfile(ROOT/KERNEL/name,self.work/name)
        shutil.copyfile(ROOT/"tests/x3_r43_harness.c",self.work/"client.c")
        test.assertEqual({"geometry.c","geometry.h","types.h","client.c"},{p.name for p in self.work.iterdir()})
        self.env={k:v for k,v in os.environ.items() if k not in ("CPATH","C_INCLUDE_PATH","CPLUS_INCLUDE_PATH","LIBRARY_PATH")}
        self.windows=os.name=="nt"
        if self.windows:
            finder=Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)"))/"Microsoft Visual Studio/Installer/vswhere.exe"
            test.assertTrue(finder.is_file(),"X3 setup: MSVC finder unavailable; not a semantic kill")
            install=subprocess.check_output([str(finder),"-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],text=True).strip()
            self.vcvars=Path(install)/"VC/Auxiliary/Build/vcvars64.bat"
            test.assertTrue(self.vcvars.is_file(),"X3 setup: MSVC environment unavailable")
        else:
            self.cc=shutil.which(os.environ.get("CC","cc"))
            test.assertIsNotNone(self.cc,"X3 setup: C compiler unavailable; not a semantic kill")

    def build(self,source,label):
        path=self.work/(label+".c");path.write_text(source,encoding="utf-8",newline="\n")
        exe=self.work/(label+(".exe" if self.windows else ""))
        if self.windows:
            command=["cl","/nologo","/utf-8","/Od","/W3","/I"+str(self.work),str(path),str(self.work/"client.c"),"/Fe:"+str(exe)]
            script=self.work/(label+".cmd")
            script.write_text('@echo off\ncall "'+str(self.vcvars)+'" >nul\n'+subprocess.list2cmdline(command)+'\n',encoding="utf-8")
            command=["cmd","/d","/c",str(script)]
        else:
            command=[self.cc,"-std=c11","-O0","-Werror=implicit-function-declaration","-I",self.work,path,self.work/"client.c","-o",exe]
        result=raw_run(command,self.work,label+"/compile",self.env)
        self.test.assertEqual(0,result.returncode,"X3 setup: compile/link failure is not a semantic kill")
        return exe


@lru_cache(maxsize=1)
def product():
    from tests import test_geo261_panel_native as panel
    from tests.test_geo261_native_kernel import native
    panel.PanelNative.setUpClass()
    return panel,native()


def union_withdrawal(source):
    start,end=function_span(source,APIS[0]);body=source[start:end]
    pattern=r"out\[i\]\.start\s*<=\s*out\[used\s*-\s*1\]\.end"
    matches=list(re.finditer(pattern,body))
    assert len(matches)==1,"X3 mutation: touching-union guard must occur exactly once"
    match=matches[0];changed=body[:match.start()]+match.group().replace("<=","<")+body[match.end():]
    return source[:start]+changed+source[end:]


def width_withdrawal(source):
    start,end=function_span(source,APIS[1]);body=source[start:end]
    return source[:start]+body[:body.index("{")+1]+"\n    return 0;\n}"+source[end:]


class R43Kernel(unittest.TestCase):
    def test_kernel_owns_public_geometry_and_template_delegates(self):
        owned(ROOT)

    def test_independent_cell_oracle_without_any_template_source(self):
        owned(ROOT);build=KernelBuild(self)
        source=(ROOT/KERNEL/"geometry.c").read_text(encoding="utf-8")
        exe=build.build(source,"oracle")
        result=raw_run([exe],build.work,"neutral-oracle",build.env)
        self.assertEqual(0,result.returncode)
        self.assertEqual("X3_R43_ORACLE sections=15360 edge_queries=1382400 touching_cases=1\n",result.stdout)

    def shared_control(self,label,transform,k_marker):
        owned(ROOT);isolated=KernelBuild(self);panel,build=product()
        source=(ROOT/KERNEL/"geometry.c").read_text(encoding="utf-8");changed=transform(source)
        print_diff(label,source,changed,KERNEL+"/geometry.c")
        for phase,text,expected in (("baseline",source,0),("withdrawn",changed,1),("restored",source,0)):
            tag="x3-"+label+"-"+phase
            k_exe=isolated.build(text,tag)
            path=build.kernel/(tag+".c");path.write_text(text,encoding="utf-8",newline="\n")
            obj=build.compile(path,tag)
            w_exe=build.link(tag+"-w",panel.PanelNative.objects("geometry_object",obj))
            for consumer,command,cwd,marker in (("K",[k_exe],isolated.work,k_marker),
                    ("W",[w_exe,"support"],build.work,"ASSERT:support-touching-union\n")):
                result=raw_run(command,cwd,label+"/"+phase+"/"+consumer)
                self.assertIn(result.returncode,(0,1),"X3 crash/setup is not a semantic verdict")
                self.assertEqual(expected,result.returncode,"X3 shared K implementation must affect both consumers")
                if expected:self.assertEqual(marker,result.stderr)

    def test_union_withdrawal_hits_independent_kernel_and_real_template(self):
        self.shared_control("union",union_withdrawal,"ASSERT:X3_R43_UNION_TOUCHING\n")

    def test_width_withdrawal_hits_independent_kernel_and_real_template(self):
        self.shared_control("width",width_withdrawal,"ASSERT:X3_R43_EDGE_COVERAGE\n")

    def test_ownership_guard_rejects_behavior_preserving_private_copy(self):
        owned(ROOT);panel,build=product()
        original=(ROOT/WOOD/"panel_support.c").read_text(encoding="utf-8")
        # The archive-local old algorithm is copied only into a temporary W
        # mutant. It still computes the right answers, but violates ownership.
        definitions="\n".join(panel.definition(panel.fixture(),name) for name in
            ("pf_interval_compare","pf_support_union","pf_support_width"))
        renames={"Coord":"GeoCoord","PfFootprint":"WoodPanelFootprint","PfInterval":"X3PrivateInterval",
                 "coord_min":"support_min","coord_max":"support_max"}
        definitions=re.sub(r"\b[A-Za-z_]\w*\b",lambda m:renames.get(m.group(),m.group()),definitions)
        definitions="typedef struct {GeoCoord lo,hi;} X3PrivateInterval;\n"+definitions+"\n"
        start,_=function_span(original,"wood_panel_support_evaluate")
        changed=original[:start]+definitions+original[start:]
        self.assertEqual(1,len(re.findall(r"\bGeoInterval\s*\*\s*un\b",changed)),"X3 private-copy control must replace one workspace carrier")
        changed=re.sub(r"\bGeoInterval\s*\*\s*un\b","X3PrivateInterval *un",changed)
        for before,after in zip(APIS,("pf_support_union","pf_support_width")):
            changed=re.sub(r"\b"+before+r"\b",after,changed)
        print_diff("private-copy",original,changed,WOOD+"/panel_support.c")
        with tempfile.TemporaryDirectory(prefix="x3-r43-ownership-") as folder:
            root=Path(folder)
            for relative in (KERNEL+"/geometry.c",KERNEL+"/geometry.h",WOOD+"/panel_support.c"):
                target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,target)
            for phase,text,expected in (("baseline",original,0),("withdrawn",changed,1),("restored",original,0)):
                (root/WOOD/"panel_support.c").write_text(text,encoding="utf-8",newline="\n")
                tag="x3-private-"+phase;path=build.woodworking/(tag+".c")
                path.write_text(text,encoding="utf-8",newline="\n");obj=build.compile(path,tag)
                exe=build.link(tag,panel.PanelNative.objects("wood_panel_support_object",obj))
                runtime=raw_run([exe,"support"],build.work,"private-copy/"+phase+"/product")
                self.assertEqual(0,runtime.returncode,"X3 private-copy withdrawal must retain product behavior")
                guard=raw_run([sys.executable,"-B",Path(__file__).resolve(),"--ownership-root",root],root,"private-copy/"+phase+"/guard")
                self.assertEqual(expected,guard.returncode)
                if expected:self.assertEqual("ASSERT:X3_R43_TEMPLATE_OWNERSHIP: private geometry copy returned\n",guard.stderr)


if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--ownership-root":
        try:owned(Path(sys.argv[2]))
        except AssertionError as error:
            print("ASSERT:"+str(error),file=sys.stderr);raise SystemExit(1)
        print("X3_R43_OWNERSHIP_OK");raise SystemExit(0)
    unittest.main()
