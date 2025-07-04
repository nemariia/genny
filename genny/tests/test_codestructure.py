import unittest
import ast
from unittest.mock import MagicMock
from genny.codeparser import CodeParser, CodeStructure


class TestCodeStructure(unittest.TestCase):
    def setUp(self):
        self.structure = CodeStructure()

    def test_add_import(self):
        self.structure.add_import(("module", "alias"))
        self.assertEqual(self.structure.imports, [("module", "alias")])

    def test_add_class(self):
        class_info = {"name": "TestClass", "docstring": "Class docstring"}
        self.structure.add_class(class_info)
        self.assertEqual(self.structure.classes, [class_info])

    def test_add_function(self):
        function_info = {"name": "test_function", "parameters": ["arg1", "arg2"]}
        self.structure.add_function(function_info)
        self.assertEqual(self.structure.functions, [function_info])

    def test_add_variable(self):
        variable_info = {"name": "test_var", "value": 42}
        self.structure.add_variable(variable_info)
        self.assertEqual(self.structure.variables, [variable_info])

    def test_reset(self):
        self.structure.add_import(("module", "alias"))
        self.structure.add_class({"name": "TestClass"})
        self.structure.add_function({"name": "test_function"})
        self.structure.add_variable({"name": "test_var"})
        self.structure.reset()
        self.assertEqual(self.structure.imports, [])
        self.assertEqual(self.structure.classes, [])
        self.assertEqual(self.structure.functions, [])
        self.assertEqual(self.structure.variables, [])

    def test_to_dict(self):
        # Add imports in the correct format
        self.structure.add_import([("module", None)])  # Valid format

        # Add a class
        self.structure.add_class({
            "name": "TestClass",
            "docstring": None,
            "base_classes": [],
            "methods": [],
            "attributes": []
        })

        # Add a function
        self.structure.add_function({
            "name": "test_function",
            "parameters": [],
            "docstring": None
        })

        # Add a variable
        self.structure.add_variable({
            "name": "test_var",
            "value": 42
        })

        # Generate the result and expected output
        result = self.structure.to_dict()
        expected = {
            "imports": [["module"]],
            "classes": [{"name": "TestClass"}],
            "functions": [{"name": "test_function", "docstring": None, "parameters": []}],
            "variables": [{"name": "test_var", "value": 42}]
        }

        # Validate the output
        self.assertEqual(result, expected)

        
if __name__ == "__main__":
    unittest.main()