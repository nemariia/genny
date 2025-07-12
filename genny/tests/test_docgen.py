import unittest
import os
import tempfile
from unittest.mock import patch
from genny.docgen import Docgen
from genny.filesystem import FileSystem


class TestDocgen(unittest.TestCase):

    def setUp(self):
        self.docgen = Docgen()
        self.file_system = FileSystem()
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
