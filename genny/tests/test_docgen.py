import unittest
import os
import tempfile
from unittest.mock import patch, Mock
from genny.docgen import Docgen
from genny.codeparser import CodeParser
from genny.filesystem import FileSystem


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

    def test_export_docs_with_unsupported_format(self):
        # Write sample Python code to generate docs
        sample_code = """
def test_function():
    \"\"\"A test function.\"\"\"
    pass
"""
        self.file_system.write_file(self.sample_file_path, sample_code)

        # Generate documentation
        self.docgen.generate_docs(self.sample_file_path)

        # Attempt to export in an unsupported format
        with self.assertRaises(ValueError) as context:
            self.docgen.export_docs("unsupported", "output.txt")

        self.assertEqual(str(context.exception), "Unsupported format: unsupported")

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

        # Assert
        generated_docs = self.docgen.generated_docs
        print(generated_docs)
        self.assertIn("functions", generated_docs)
        self.assertEqual(generated_docs["functions"], ["foo", "Unnamed"])
        self.assertEqual(generated_docs["title"], "sample_code.py")
