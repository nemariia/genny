import unittest
import ast
from unittest.mock import MagicMock
from genny.codeparser import CodeParser, CodeStructure


class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.mock_file_system = MagicMock()
        self.parser = CodeParser(self.mock_file_system)

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


if __name__ == "__main__":
    unittest.main()
