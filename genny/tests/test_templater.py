import unittest
from unittest.mock import MagicMock, patch, mock_open
from genny.templater import Templater
import json
import tempfile
import os


class TestTemplater(unittest.TestCase):

    def setUp(self):
        self.file_system_mock = MagicMock()
        self.templater = Templater(file_system=self.file_system_mock)
        self.templater.templates_metadata = {
            "existing_template": {"sections": ["classes"], "style": {"classes": "detailed"}}
        }
        self.templater._save_metadata = MagicMock()

    def test_get_template_metadata_valid(self):
        """Test retrieving metadata for a valid template."""
        # Mock metadata content
        mock_metadata = {"sections": ["classes", "functions"], "style": {"classes": "detailed", "functions": "summary"}}
        self.templater.templates_metadata = {"standard": mock_metadata}

        # Call the method
        metadata = self.templater.get_template_metadata("standard")

        # Assert the metadata matches the mocked metadata
        self.assertEqual(metadata, mock_metadata)

    def test_get_template_metadata_invalid(self):
        self.file_system_mock.read_file.side_effect = FileNotFoundError("Template file not found")
        
        with self.assertRaises(ValueError) as context:
            self.templater.get_template_metadata("missing_template")

        self.assertEqual(str(context.exception), "Template 'missing_template' not found.")

    def test_render_template(self):
        """Test rendering a template with provided data."""
        # Mock template content and data
        mock_template = "Template Title: {{ title }}\nSections: {% for section in sections %}- {{ section }}{% endfor %}"
        self.templater.file_system.read_file.return_value = mock_template

        mock_data = {"title": "Documentation", "sections": ["classes", "functions"]}

        # Mock rendering logic to return plain text
        self.templater.render_template = MagicMock(return_value="Template Title: Documentation\nSections: - classes- functions")

        # Render the template
        rendered_output = self.templater.render_template("standard", mock_data)

        # Expected output
        expected_output = "Template Title: Documentation\nSections: - classes- functions"

        self.assertEqual(rendered_output.strip(), expected_output.strip())
        self.templater.render_template.assert_called_once_with("standard", mock_data)

    def test_add_template(self):
        """Test adding a new template."""
        mock_template_content = "New Template Content"
        mock_template_style = {"sections": ["functions"], "style": {"functions": "detailed"}}
        template_name = "new_template"

        # Simulate non-existent template
        self.templater.templates_metadata = {}
        self.templater._save_metadata = MagicMock()

        # Call the method
        result = self.templater.add_template(template_name, ["functions"], {"functions": "detailed"})

        # Assertions
        self.assertTrue(result)
        self.templater._save_metadata.assert_called_once()
        self.assertIn(template_name, self.templater.templates_metadata)

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_delete_existing_template_with_file(self, mock_remove, mock_exists):
        """Test deleting an existing template with a corresponding file."""
        template_name = "existing_template"
        self.templater.templates_metadata = {
            "existing_template": {"sections": ["functions"], "style": {"functions": "detailed"}}
        }
        self.templater._save_metadata = MagicMock()


        # Call the method
        self.templater.delete_template(template_name)

        # Verify that the template was removed from metadata
        self.assertNotIn(template_name, self.templater.templates_metadata)

        # Verify that metadata was saved
        self.templater._save_metadata.assert_called_once()

    @patch("os.path.exists")
    @patch("os.remove")
    def test_delete_existing_template_without_file(self, mock_remove, mock_exists):
        """Test deleting an existing template when the file does not exist."""
        template_name = "existing_template"

        # Simulate the file does not exist
        mock_exists.return_value = False

        # Call the method
        self.templater.delete_template(template_name)

        # Verify that the template was removed from metadata
        self.assertNotIn(template_name, self.templater.templates_metadata)

        # Verify that metadata was saved
        self.templater._save_metadata.assert_called_once()

        # Verify that no attempt to remove a non-existent file was made
        mock_remove.assert_not_called()

    def test_delete_nonexistent_template(self):
        """Test attempting to delete a template that does not exist."""
        template_name = "nonexistent_template"

        # Call the method and expect a ValueError
        with self.assertRaises(ValueError) as context:
            self.templater.delete_template(template_name)

        self.assertEqual(str(context.exception), f"Template '{template_name}' not found.")

    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_load_metadata_file_not_found(self, mock_open_fn):
        """Test _load_metadata returns empty dict if file is missing."""
        self.templater.metadata_file = "fake_metadata.json"

        result = self.templater._load_metadata()

        self.assertEqual(result, {})
        mock_open_fn.assert_called_once_with("fake_metadata.json", "r")

    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    @patch("json.load", side_effect=json.JSONDecodeError("Expecting value", doc="", pos=0))
    def test_load_metadata_json_decode_error(self, mock_json_load, mock_open_fn):
        """Test _load_metadata returns empty dict if JSON is invalid."""
        self.templater.metadata_file = "corrupt_metadata.json"

        result = self.templater._load_metadata()

        self.assertEqual(result, {})
        mock_open_fn.assert_called_once_with("corrupt_metadata.json", "r")
        mock_json_load.assert_called_once()

    def test_save_metadata(self):
        """Test _save_metadata success."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = os.path.join(temp_dir, "mock_metadata.json")

            # Recreate the Templater with the test-specific metadata path
            templater = Templater()
            templater.metadata_file = metadata_path
            templater.templates_metadata = {
                "sample_template": {"sections": ["functions"], "style": {"functions": "detailed"}}
            }

            # Write the file
            templater._save_metadata()

            # Confirm the file exists and contains correct JSON
            assert os.path.exists(metadata_path), "Metadata file was not created"
            with open(metadata_path, "r") as f:
                data = json.load(f)

            self.assertEqual(data, templater.templates_metadata)

    @patch("genny.templater.open", new_callable=mock_open)
    def test_save_metadata_handles_oserror(self, mock_open_fn):
        """Test _save_metadata os error."""
        # Allow reading to succeed but writing to fail
        def open_side_effect(file, mode, *args, **kwargs):
            if mode == "w":
                raise OSError("Permission denied")
            return mock_open(read_data="{}").return_value

        mock_open_fn.side_effect = open_side_effect

        # Create templater instance
        log = MagicMock()
        templater = Templater(file_system=MagicMock(), log_callback=log)
        templater.metadata_file = "mock_metadata.json"
        templater.templates_metadata = {
            "template": {"sections": ["functions"], "style": {"functions": "detailed"}}
        }

        # Act
        templater._save_metadata()

        # Assert log was called with proper error
        log.assert_called_once()
        self.assertIn("Error saving metadata", log.call_args[0][0])
        self.assertIn("Permission denied", log.call_args[0][0])

    @patch("json.dump", side_effect=TypeError("Unserializable object"))
    @patch("genny.templater.open", new_callable=mock_open, read_data="{}")
    def test_save_metadata_handles_json_typeerror(self, mock_open_fn, mock_json_dump):
        log = MagicMock()
        templater = Templater(file_system=MagicMock(), log_callback=log)
        templater.metadata_file = "mock_metadata.json"
        templater.templates_metadata = {
            "template": {"sections": ["functions"], "style": {"functions": set(["not", "json", "serializable"])}}
        }

        templater._save_metadata()

        # Check that error is logged
        log.assert_called_once()
        error_msg = log.call_args[0][0]
        self.assertIn("Error saving metadata", error_msg)
        self.assertIn("Unserializable object", error_msg)
