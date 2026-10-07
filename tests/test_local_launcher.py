"""Local launcher rejects incomplete native setups before starting a service."""
from contextlib import nullcontext
import importlib.util
import io
import os
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_launcher", ROOT / "geometry-web/start_local.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="geometry-launcher-test-")
        self.temp = Path(self.directory.name)
        self.paths = {"core": str(self.temp / "core"), "bridge": str(self.temp / "bridge"),
                      "model-base": str(self.temp / "model-base")}

    def tearDown(self):
        self.directory.cleanup()

    def registry(self):
        return SimpleNamespace(OUT_DIR=None, LockBusy=type("LockBusy", (Exception,), {}),
            ProcessLock=Mock(side_effect=lambda name: nullcontext()),
            build=Mock(return_value={name: SimpleNamespace(ok=True, status="built", detail="") for name in launcher.NATIVE_NAMES}),
            BY_NAME={name: SimpleNamespace(path=Path(value)) for name,value in self.paths.items()},
            require_fresh=Mock(side_effect=lambda name,path: str(path)))

    def test_native_aliases_all_use_verified_absolute_paths(self):
        inherited={"GEOMETRY_BRIDGE":"old", "GEOMETRY_SCENARIO_BASE":"old", "GEOMETRY_BRIDGE_WSL":"1",
                   "GEOMETRY_MODEL_BASE_WSL_DISTRO":"OldDistro", "GEOMETRY_MANAGED_PREVIEW":"1", "OTHER":"keep"}
        env=launcher.runtime_environment(self.paths,environ=inherited)
        for name in ["GEOMETRY_BRIDGE","GEOMETRY_TEST_BRIDGE","GEOMETRY_MODEL_UPDATE_BRIDGE","GEOMETRY_SCENARIO_BRIDGE"]:
            self.assertEqual(env[name],self.paths["bridge"])
        for name in ["GEOMETRY_MODEL_BASE","GEOMETRY_SCENARIO_BASE"]:
            self.assertEqual(env[name],self.paths["model-base"])
        for name in ["GEOMETRY_BRIDGE_WSL","GEOMETRY_MODEL_BASE_WSL_DISTRO","GEOMETRY_MANAGED_PREVIEW"]:
            self.assertNotIn(name,env)
        self.assertEqual(env["OTHER"],"keep")
        self.assertEqual(inherited["GEOMETRY_BRIDGE"],"old")

    def test_managed_preview_requires_explicit_opt_in(self):
        self.assertEqual(launcher.runtime_environment(self.paths,managed=True,environ={})["GEOMETRY_MANAGED_PREVIEW"],"1")
        self.assertNotIn("GEOMETRY_MANAGED_PREVIEW",launcher.runtime_environment(self.paths,environ={"GEOMETRY_MANAGED_PREVIEW":"1"}))

    def test_private_output_is_stable_per_root_and_distinct_across_checkouts(self):
        a=launcher.binary_directory(root=self.temp/"a",temp=self.temp)
        self.assertEqual(a,launcher.binary_directory(root=self.temp/"a",temp=self.temp))
        self.assertNotEqual(a,launcher.binary_directory(root=self.temp/"b",temp=self.temp))

    def test_binary_directory_rejects_checkout_relative_and_temp_root(self):
        for value in ["relative", str(ROOT/".build"), str(self.temp), str(self.temp.parent/"outside")]:
            with self.subTest(value=value),self.assertRaises(ValueError):
                launcher.binary_directory(value,root=ROOT,temp=self.temp)

    def test_symlink_cannot_redirect_output_outside_temp(self):
        link=self.temp/"escape"
        original=Path.resolve
        # Exercise the resolved target without requiring Windows symlink privileges.
        def resolved(path,*args,**kwargs):
            return ROOT/"build" if path==link/"build" else original(path,*args,**kwargs)
        with patch.object(Path,"resolve",resolved),self.assertRaises(ValueError):
            launcher.binary_directory(link/"build",root=ROOT,temp=self.temp)

    def test_busy_port_is_rejected_without_stopping_its_owner(self):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1",0));listener.listen()
            port=listener.getsockname()[1]
            with self.assertRaises(RuntimeError):launcher.check_port(port)
            with socket.create_connection(("127.0.0.1",port),timeout=2):pass

    def test_insufficient_stack_hard_limit_refuses_start(self):
        limits=SimpleNamespace(RLIMIT_STACK=3,RLIM_INFINITY=-1,getrlimit=Mock(return_value=(1024,2048)),setrlimit=Mock())
        with self.assertRaises(RuntimeError):launcher.ensure_stack(limits)
        limits.setrlimit.assert_not_called()

    def test_stack_is_raised_and_unlimited_is_preserved(self):
        limits=SimpleNamespace(RLIMIT_STACK=3,RLIM_INFINITY=-1,
            getrlimit=Mock(side_effect=[(8192,-1),(launcher.MIN_STACK,-1)]),setrlimit=Mock())
        launcher.ensure_stack(limits)
        limits.setrlimit.assert_called_once_with(3,(launcher.MIN_STACK,-1))
        limits.getrlimit=Mock(return_value=(-1,-1));limits.setrlimit.reset_mock()
        launcher.ensure_stack(limits);limits.setrlimit.assert_not_called()

    def test_build_result_is_not_a_substitute_for_current_receipt(self):
        registry=self.registry();registry.require_fresh.side_effect=RuntimeError("missing or stale sidecar")
        with self.assertRaisesRegex(RuntimeError,"sidecar"),patch('sys.stdout',new_callable=io.StringIO):
            launcher.prepare_binaries(self.temp/"out",registry)
        registry.build.assert_called_once_with(launcher.NATIVE_NAMES)
        registry.require_fresh.assert_called_once()

    def test_failed_build_never_returns_launch_paths(self):
        registry=self.registry();registry.build.return_value["bridge"].ok=False
        registry.build.return_value["bridge"].status="compile-failed"
        with self.assertRaises(RuntimeError),patch('sys.stdout',new_callable=io.StringIO):
            launcher.prepare_binaries(self.temp/"out",registry)
        registry.require_fresh.assert_not_called()

    def test_build_lock_failure_does_not_build(self):
        registry=self.registry();registry.ProcessLock.side_effect=registry.LockBusy("already building")
        with self.assertRaisesRegex(RuntimeError,"already building"):
            launcher.prepare_binaries(self.temp/"out",registry)
        registry.build.assert_not_called()

    def test_successful_build_requires_all_three_fresh_receipts(self):
        registry=self.registry()
        with patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(launcher.prepare_binaries(self.temp/"out",registry),self.paths)
        self.assertEqual([call.args[0] for call in registry.require_fresh.call_args_list],list(launcher.NATIVE_NAMES))

    def test_build_only_does_not_probe_ports_or_start_service(self):
        with patch.object(launcher.sys,"platform","linux"),patch.object(launcher,"ensure_stack"), \
             patch.object(launcher,"prepare_binaries",return_value=self.paths),patch.object(launcher,"check_port") as port, \
             patch.object(launcher.os,"execve") as execute,patch('sys.stdout',new_callable=io.StringIO):
            self.assertEqual(launcher.main(["--build-only","--binary-dir",str(self.temp/"out")]),0)
        port.assert_not_called();execute.assert_not_called()

    def test_busy_port_prevents_build_and_exec(self):
        with patch.object(launcher.sys,"platform","linux"),patch.object(launcher,"ensure_stack"), \
             patch.object(launcher,"prepare_binaries") as build,patch.object(launcher,"check_port",side_effect=RuntimeError("busy")), \
             patch.object(launcher.os,"execve") as execute,patch('sys.stderr',new_callable=io.StringIO):
            self.assertEqual(launcher.main([]),2)
        build.assert_not_called();execute.assert_not_called()

    def test_managed_wrong_port_is_rejected_before_build(self):
        with patch.object(launcher,"prepare_binaries") as build,patch('sys.stderr',new_callable=io.StringIO),self.assertRaises(SystemExit) as error:
            launcher.main(["--managed-preview","--port","8982"])
        self.assertEqual(error.exception.code,2);build.assert_not_called()

    def test_real_start_execs_serve_with_same_verified_native_group(self):
        class Replaced(BaseException):pass
        with patch.object(launcher.sys,"platform","linux"),patch.object(launcher,"ensure_stack"), \
             patch.object(launcher,"prepare_binaries",return_value=self.paths),patch.object(launcher,"check_port") as port, \
             patch.object(launcher.os,"chdir") as cd,patch.object(launcher.os,"execve",side_effect=Replaced) as execute, \
             patch('sys.stdout',new_callable=io.StringIO),self.assertRaises(Replaced):
            launcher.main(["--port","8982"])
        self.assertEqual(port.call_count,2);cd.assert_called_once_with(ROOT)
        program,argv,env=execute.call_args.args
        self.assertEqual(argv,[program,"-u",str(ROOT/"geometry-web/serve.py"),"8982"])
        self.assertEqual(env["GEOMETRY_SCENARIO_BRIDGE"],env["GEOMETRY_BRIDGE"])
        self.assertEqual(env["GEOMETRY_SCENARIO_BASE"],env["GEOMETRY_MODEL_BASE"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
