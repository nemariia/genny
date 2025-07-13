import unittest
import ast
from unittest.mock import MagicMock
from genny.codeparser import CodeParser, CodeStructure


class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.mock_file_system = MagicMock()
        self.parser = CodeParser(self.mock_file_system)
        self.cs = CodeStructure()

    def test_parse_code(self):
        sample_code = """
import os

class TestClass:
    def method(self):
        pass

def function():
    pass
"""
        self.mock_file_system.read_file.return_value = sample_code
        structure = self.parser.parse_code("test_file.py")
        self.assertEqual(len(structure.imports), 1)
        self.assertEqual(len(structure.classes), 1)
        self.assertEqual(len(structure.functions), 1)

    def test_get_class_details(self):
        class_code = """
class TestClass(BaseClass):
    \"\"\"Class docstring.\"\"\"
    def method(self):
        \"\"\"Method docstring.\"\"\"
        pass
"""
        tree = ast.parse(class_code)  # Ensure correct indentation in the string
        class_node = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        details = self.parser.get_class_details(class_node)
        expected = {
            "name": "TestClass",
            "docstring": "Class docstring.",
            "base_classes": ["BaseClass"],
            "methods": [{"name": "method", "docstring": "Method docstring.", "parameters": ["self"], "return_type": "Returns None"}],
            "attributes": []
        }
        self.assertEqual(details, expected)

    def test_get_function_details(self):
        function_code = """
def test_function(arg1, arg2):
    \"\"\"Function docstring.\"\"\"
    return arg1 + arg2
"""
        tree = ast.parse(function_code)
        function_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        details = self.parser.get_function_details(function_node)
        expected = {
            "name": "test_function",
            "docstring": "Function docstring.",
            "parameters": ["arg1", "arg2"],
            "return_type": "Returns a value of type: BinOp"
        }
        self.assertEqual(details, expected)

    def test_get_import_details(self):
        import_code = """
import os
from sys import path as sys_path
"""
        tree = ast.parse(import_code)
        import_nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        details = [self.parser.get_import_details(node) for node in import_nodes]
        expected = [
            [("os", None)],
            [("sys.path", "sys_path")]
        ]
        self.assertEqual(details, expected)

    def test_get_docstrings(self):
        sample_code = """
\"\"\"Module docstring.\"\"\"

def function():
    \"\"\"Function docstring.\"\"\"
    pass

class TestClass:
    \"\"\"Class docstring.\"\"\"
    def method(self):
        \"\"\"Method docstring.\"\"\"
        pass
"""
        self.mock_file_system.read_file.return_value = sample_code
        docstrings = self.parser.get_docstrings("test_file.py")
        expected = [
            "Module docstring.",
            "Function docstring.",
            "Class docstring.",
            "Method docstring."
        ]
        self.assertEqual(docstrings, expected)

    def test_tuple_with_alias(self):
        imports = [("os", "oslib"), ("sys", "")]
        expected = ["os as oslib", "sys"]
        result = self.cs.format_imports(imports)
        self.assertEqual(result, expected)

    def test_strings_only(self):
        imports = ["math", "random"]
        expected = ["math", "random"]
        result = self.cs.format_imports(imports)
        self.assertEqual(result, expected)

    def test_malformed_items(self):
        imports = [{"key": "value"}, 123, None]
        expected = ["Invalid import format", "Invalid import format", "Invalid import format"]
        result = self.cs.format_imports(imports)
        self.assertEqual(result, expected)

    def test_mixed_inputs(self):
        imports = [("json", "js"), "datetime", 42, ("os", "")]
        expected = ["json as js", "datetime", "Invalid import format", "os"]
        result = self.cs.format_imports(imports)
        self.assertEqual(result, expected)

    def parse_class(self, class_src):
        tree = ast.parse(class_src)
        class_node = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        return self.parser.get_class_details(class_node)

    def test_simple_assign(self):
        result = self.parse_class("class A:\n    x = 123")
        self.assertIn({'name': 'x', 'value': '123'}, result['attributes'])

    def test_annassign_with_value(self):
        result = self.parse_class("class A:\n    x: int = 123")
        self.assertIn({'name': 'x', 'value': '123'}, result['attributes'])

    def test_annassign_without_value(self):
        result = self.parse_class("class A:\n    x: int")
        self.assertIn({'name': 'x', 'value': 'None'}, result['attributes'])

    def test_multiple_targets(self):
        result = self.parse_class("class A:\n    x, y = 1, 2")
        self.assertEqual(result['attributes'], [])  # Should skip tuple unpacking

    def test_non_name_target(self):
        result = self.parse_class("class A:\n    [x] = [1]")
        self.assertEqual(result['attributes'], [])  # [x] is a List node, not Name
