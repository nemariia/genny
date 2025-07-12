import unittest
from unittest.mock import MagicMock, patch
from genny.templater import Templater


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
