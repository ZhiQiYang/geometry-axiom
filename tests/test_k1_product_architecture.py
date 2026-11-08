"""Main K1 increment, independently counted without changing the existing suite.

The original fixture functions are shared verbatim. This class inherits only
unittest.TestCase, so none of the original suite's tests are run a second time.
"""
import unittest
from tests import test_product_architecture as baseline


class K1ProductArchitecture(unittest.TestCase):
    setUpClass=classmethod(baseline.ProductArchitecture.setUpClass.__func__)
    setUp=baseline.ProductArchitecture.setUp
    change=baseline.ProductArchitecture.change
    focused=baseline.ProductArchitecture.focused
    rejects=baseline.ProductArchitecture.rejects

    def test_actual_interval_core_woodworking_policy_tokens_are_rejected(self):
        path = "geometry-core/interval-allocation.js"
        for token in (b"GeometryWoodworkingCutting", b"materialKey", b"stockIdentity", b"sectionKey",
                      b"kerf", b"minRemnant", b"allowance", b"TIMBER_ROLE_PRIMARY"):
            with self.subTest(token=token), self.change(path, lambda raw: raw + b"\nvoid " + token + b";\n"):
                self.rejects(self.focused(path), "FORBIDDEN_IDENTIFIER", path)


    def test_actual_interval_core_fixed_template_identity_is_rejected(self):
        path = "geometry-core/interval-allocation.js"
        with self.change(path, lambda raw: raw + b'\nvoid "woodworking/1";\n'):
            self.rejects(self.focused(path), "FORBIDDEN_STRING", path)


    def test_actual_interval_core_template_dependency_is_rejected(self):
        path = "geometry-core/interval-allocation.js"
        target = "geometry-templates/woodworking/cutting.js"
        with self.change(path, lambda raw: raw + b'\nrequire("../geometry-templates/woodworking/cutting.js");\n'):
            self.rejects(self.focused(path), "LAYER_DIRECTION", path, [path, target])


    def test_actual_woodworking_cutting_host_dependencies_are_rejected(self):
        path = "geometry-templates/woodworking/cutting.js"
        for target in ("geometry-web/cutting-settings.js", "geometry-web/timber-schedule.js",
                       "geometry-app/application.js"):
            with self.subTest(target=target), self.change(
                    path, lambda raw: raw + ('\nrequire("../../' + target + '");\n').encode("utf-8")):
                self.rejects(self.focused(path), "LAYER_DIRECTION", path, [path, target])


if __name__ == '__main__':
    unittest.main()
