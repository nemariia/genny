import unittest
import os
import tempfile
from unittest.mock import patch, Mock, MagicMock
from genny.docgen import Docgen
from genny.codeparser import CodeParser
from genny.filesystem import FileSystem
import yaml


class TestDocgen(unittest.TestCase):

    def setUp(self):
        self.docgen = Docgen()
        self.file_system = FileSystem()
        self.parser = CodeParser(self.file_system)
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_file_path = os.path.join(self.temp_dir.name, "sample_code.py")

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_generate_docs_with_valid_file(self):
        # Write sample Python code to a temporary file
        sample_code = """
import os

class TestClass:
    \"\"\"A test class.\"\"\"
    def method(self):
        \"\"\"A test method.\"\"\"
        pass

def test_function():
    \"\"\"A test function.\"\"\"
    pass
"""
        self.file_system.write_file(self.sample_file_path, sample_code)

        # Generate documentation
        self.docgen.generate_docs(self.sample_file_path)

        # Assertions
        generated_docs = self.docgen.generated_docs
        self.assertIn("title", generated_docs)
        self.assertEqual(generated_docs["title"], "sample_code.py")
        self.assertIn("classes", generated_docs)
        self.assertIn("functions", generated_docs)
        self.assertEqual(len(generated_docs["classes"]), 1)
        self.assertEqual(len(generated_docs["functions"]), 1)

    def test_generate_docs_with_missing_file(self):
        # Call generate_docs with a non-existent file
        missing_file_path = os.path.join(self.temp_dir.name, "missing_file.py")
        with self.assertLogs(level="ERROR") as log:
            self.docgen.generate_docs(missing_file_path)

        # Check logs
        self.assertIn(f"Error: The file '{missing_file_path}' does not exist.", log.output[0])

    def test_export_docs_json(self):
        # Write sample Python code to generate docs
        sample_code = """
def test_function():
    \"\"\"A test function.\"\"\"
    pass
"""
        self.file_system.write_file(self.sample_file_path, sample_code)

        # Generate documentation
        self.docgen.generate_docs(self.sample_file_path)

        # Export to JSON
        output_file = os.path.join(self.temp_dir.name, "output.json")
        self.docgen.export_docs("json", output_file)

        # Read the exported file and verify content
        exported_content = self.file_system.read_file(output_file)
        self.assertIn("test_function", exported_content)
    
    def test_export_docs_markdown(self):
        self.docgen.generated_docs = {"title": "test.py"}
        self.docgen.file_system.write_file = MagicMock()
        self.docgen.log_callback = MagicMock()

        result = self.docgen.export_docs("markdown", "output.md")

        self.assertTrue(result)
        self.docgen.file_system.write_file.assert_called_once()
        args = self.docgen.file_system.write_file.call_args[0]
        self.assertEqual(args[0], "output.md")
        self.assertIn("# Documentation", args[1])
    
    def test_export_docs_html_success(self):
        self.docgen.generated_docs = {"title": "test.py"}
        self.docgen.file_system.write_file = MagicMock()
        self.docgen.log_callback = MagicMock()
        self.docgen.format_html = MagicMock(return_value="<html>ok</html>")

        result = self.docgen.export_docs("html", "output.html")

        self.assertTrue(result)
        self.assertEqual(self.docgen.format_html.call_count, 2)
        self.docgen.format_html.assert_called_with({'title': 'test.py'})
        self.docgen.file_system.write_file.assert_called_once()

    def test_export_docs_html_returns_false_on_none(self):
        self.docgen.generated_docs = {"title": "test.py"}
        self.docgen.log_callback = MagicMock()
        self.docgen.format_html = MagicMock(return_value="")  # Simulate failure
        self.docgen.file_system.write_file = MagicMock()

        result = self.docgen.export_docs("html", "output.html")

        self.assertFalse(result)
        self.docgen.file_system.write_file.assert_not_called()

    def test_export_docs_yaml(self):
        self.docgen.generated_docs = {"title": "test.py"}
        self.docgen.file_system.write_file = MagicMock()
        self.docgen.log_callback = MagicMock()

        result = self.docgen.export_docs("yaml", "output.yaml")

        self.assertTrue(result)
        args = self.docgen.file_system.write_file.call_args[0]
        self.assertEqual(args[0], "output.yaml")
        self.assertIn("title: test.py", args[1])

    def test_export_docs_with_unsupported_format(self):
        # Write sample Python code to generate docs
        sample_code = """
def test_function():
    \"\"\"A test function.\"\"\"
    pass
"""
        self.file_system.write_file(self.sample_file_path, sample_code)
        self.docgen.log_callback = MagicMock()

        # Generate documentation
        self.docgen.generate_docs(self.sample_file_path)

        self.docgen.export_docs("unsupported", "output.txt")

        self.docgen.log_callback.assert_called_with("Unsupported format: unsupported")
    
    def test_export_docs_no_generated_docs_returns_false(self):
        self.docgen.generated_docs = {}
        self.docgen.log_callback = MagicMock()

        result = self.docgen.export_docs("markdown", "output.md")

        self.assertFalse(result)
        self.docgen.log_callback.assert_called_once_with("No documentation generated to export.")

    @patch("genny.docgen.FileSystem.read_file", return_value="def foo(): pass")
    @patch("genny.docgen.Templater.get_template_metadata", return_value={"sections": [], "style": {}})
    @patch("genny.docgen.CodeParser.parse_code")
    def test_sets_current_template_when_not_current(self, mock_parse, mock_get_template_metadata, mock_read_file):
        mock_parse.return_value.to_dict.return_value = {}

        self.docgen.generate_docs("dummy_file.py", template="custom-template")

        self.assertEqual(self.docgen.current_template, "custom-template")

    @patch("genny.docgen.FileSystem.read_file", side_effect=FileNotFoundError("dummy_file.py not found"))
    def test_logs_error_callback_on_file_not_found(self, mock_read_file):
        mock_callback = Mock()
        docgen = Docgen(log_callback=mock_callback)

        docgen.generate_docs("dummy_file.py")

        expected_message = "Error: dummy_file.py not found"
        mock_callback.assert_called_once_with(expected_message)

    @patch("genny.docgen.Templater.get_template_metadata", side_effect=KeyError)
    @patch("genny.docgen.FileSystem.read_file", return_value="def foo(): pass")
    def test_logs_error_callback_when_template_not_found(self, mock_read_file, mock_get_metadata):
        mock_callback = Mock()
        docgen = Docgen(log_callback=mock_callback)
        docgen.current_template = "nonexistent_template"

        docgen.generate_docs("some_file.py")

        expected_message = "Error: Template 'nonexistent_template' not found."
        mock_callback.assert_called_once_with(expected_message)

    def test_summary_style_uses_unnamed_when_missing_name(self):
        # Sample code with functions (parser will be mocked, so content doesn't matter)
        sample_code = """
def foo():
    pass

def bar():
    pass
"""

        # Write sample code to file
        self.file_system.write_file(self.sample_file_path, sample_code)

        # Patch the parser to return a structure with one item missing 'name'
        self.docgen.parser.parse_code = lambda _: type("MockParsed", (), {
            "to_dict": lambda self: {
                "functions": [
                    {"name": "foo"},
                    {"id": "not_a_name"}  # no 'name' key
                ]
            }
        })()

        # Patch template to specify summary style
        self.docgen.templater.get_template_metadata = lambda _: {
            "sections": ["functions"],
            "style": {"functions": "summary"}
        }

        # Act
        self.docgen.generate_docs(self.sample_file_path)

        generated_docs = self.docgen.generated_docs
        self.assertIn("functions", generated_docs)
        self.assertEqual(generated_docs["functions"], ["foo", "Unnamed"])
        self.assertEqual(generated_docs["title"], "sample_code.py")

    # Markdown tests
    def test_format_imports(self):
        docs = {
            "imports": [[
                "os",
                "sys as system"
            ]]
        }
        md = self.docgen.format_markdown(docs)
        self.assertIn("# Documentation", md)
        self.assertIn("## Imports", md)
        self.assertIn("- os", md)
        self.assertIn("- sys as system", md)

    def test_format_functions(self):
        docs = {
            "functions": [
                {
                    "name": "my_func",
                    "docstring": "Does something.",
                    "parameters": ["x", "y"],
                    "return_type": "Returns a number"
                }
            ]
        }
        md = self.docgen.format_markdown(docs)
        self.assertIn("## Functions", md)
        self.assertIn("### my_func", md)
        self.assertIn("**Docstring:**\n> Does something.", md)
        self.assertIn("**Parameters:**", md)
        self.assertIn("x, y", md)
        self.assertIn("**Returns:**\nReturns a number", md)

    def test_format_classes_with_details(self):
        docs = {
            "classes": [
                {
                    "name": "MyClass",
                    "docstring": "A sample class.",
                    "base_classes": ["Base"],
                    "attributes": [
                        {"name": "x", "value": "123"},
                        {"name": "y"}
                    ],
                    "methods": [
                        {
                            "name": "foo",
                            "parameters": ["self"],
                            "docstring": "Does foo.",
                            "return_type": "Returns None"
                        }
                    ]
                }
            ]
        }
        md = self.docgen.format_markdown(docs)
        self.assertIn("## Classes", md)
        self.assertIn("### MyClass", md)
        self.assertIn("**Docstring:**\n> A sample class.", md)
        self.assertIn("**Base Classes:**", md)
        self.assertIn("Base", md)
        self.assertIn("**Attributes:**", md)
        self.assertIn("- `x`: 123", md)
        self.assertIn("- `y`: No description", md)
        self.assertIn("**Methods:**", md)
        self.assertIn("- `foo` (self)", md)
        self.assertIn("  - **Docstring:** Does foo.", md)
        self.assertIn("  - **Returns:** Returns None", md)

    def test_fallback_section(self):
        docs = {
            "misc": ["Item1", "Item2"]
        }
        md = self.docgen.format_markdown(docs)
        self.assertIn("## Misc", md)
        self.assertIn("- Item1", md)
        self.assertIn("- Item2", md)

    def test_format_html_returns_rendered_output(self):
        mock_templater = MagicMock()
        docs = {"title": "test.py", "functions": [{"name": "foo", "docstring": "test"}]}
        expected_html = "<html><body>Test</body></html>"

        # Mock the render_template method
        mock_templater.render_template.return_value = expected_html
        self.docgen.templater = mock_templater
        self.docgen.current_template = "test_template"

        # Run format_html
        result = self.docgen.format_html(docs)

        mock_templater.render_template.assert_called_once_with("test_template", docs)
        self.assertEqual(result, expected_html)
    
    def test_format_yaml_output(self):
        docs = {
            "title": "test.py",
            "functions": [
                {"name": "foo", "docstring": "Does something"}
            ],
            "imports": [["os", "sys"]]
        }

        yaml_output = self.docgen.format_yaml(docs)

        # Re-parse the YAML and compare to the original dict
        parsed = yaml.safe_load(yaml_output)
        self.assertEqual(parsed, docs)

        # Check formatting characteristics
        self.assertIn("title:", yaml_output)
        self.assertIn("functions:", yaml_output)
        self.assertNotIn("{", yaml_output)  # ensure block style
        self.assertNotIn("}", yaml_output)

    def test_export_docs_raises_exception_logs_it(self):
        self.docgen.generated_docs = {"title": "test.py"}
        self.docgen.log_callback = MagicMock()
        self.docgen.file_system.write_file = MagicMock(side_effect=Exception("Simulated write error"))

        result = self.docgen.export_docs("markdown", "output.md")

        self.assertFalse(result)
        self.docgen.log_callback.assert_called_once()
        self.assertIn("Error exporting documents: Simulated write error", self.docgen.log_callback.call_args[0][0])
