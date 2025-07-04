import unittest
import os
import json
import tempfile
from genny.settingsmanager import SettingsManager


class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()  # Close so SettingsManager can access it
        self.manager = SettingsManager(self.temp_file.name)

    def tearDown(self):
        # Remove the temporary file after tests
        os.remove(self.temp_file.name)

    def test_load_settings(self):
        # Write sample settings to the temporary file
        sample_settings = {
            "default_code": "code.py",
            "default_template": "custom",
            "default_format": "html",
            "default_destination": "output.html",
            "repo_path": "/path/to/repo"
        }
        with open(self.temp_file.name, "w") as file:
            json.dump(sample_settings, file)

        # Load settings and verify the content
        self.manager.load_settings()
        self.assertEqual(self.manager.settings, sample_settings)

    def test_load_settings_file_not_found(self):
        # Initialize with a non-existent file
        nonexistent_file = tempfile.NamedTemporaryFile(delete=True).name
        manager = SettingsManager(nonexistent_file)
        default_settings = {
            "default_code": "",
            "default_template": "standard",
            "default_format": "markdown",
            "default_destination": "",
            "repo_path": ""
        }

        # Verify settings are initialized to defaults
        self.assertEqual(manager.settings, default_settings)
        # Verify the file is created
        self.assertTrue(os.path.exists(nonexistent_file))
        os.remove(nonexistent_file)

    def test_load_settings_invalid_json(self):
        # Write invalid JSON to the temporary file
        with open(self.temp_file.name, "w") as file:
            file.write("{ invalid json }")

        # Load settings and verify defaults are used
        with self.assertLogs(level='ERROR'):
            self.manager.load_settings()
        default_settings = {
            "default_code": "",
            "default_template": "standard",
            "default_format": "markdown",
            "default_destination": "",
            "repo_path": ""
        }
        self.assertEqual(self.manager.settings, default_settings)

    def test_save_settings(self):
        # Update settings and save
        updated_settings = {
            "default_code": "main.py",
            "default_template": "simple",
            "default_format": "json",
            "default_destination": "output.json",
            "repo_path": "/repo"
        }
        self.manager.settings = updated_settings
        self.manager.save_settings()

        # Verify the file content
        with open(self.temp_file.name, "r") as file:
            saved_data = json.load(file)
        self.assertEqual(saved_data, updated_settings)
        
    def test_load_settings_invalid_json(self):
        # Write invalid JSON to the temporary file
        with open(self.temp_file.name, "w") as file:
            file.write("{ invalid json }")

        # Load settings and verify defaults are used
        with self.assertLogs(level='ERROR') as log:
            self.manager.load_settings()
        default_settings = {
            "default_code": "",
            "default_template": "standard",
            "default_format": "markdown",
            "default_destination": "",
            "repo_path": ""
        }
        self.assertEqual(self.manager.settings, default_settings)
        self.assertIn("Error reading settings file", log.output[0])

    def test_update_setting_invalid_key(self):
        # Attempt to update a non-existent key
        with self.assertLogs(level='INFO') as log:
            self.manager.update_setting("nonexistent_key", "value")
        self.assertIn("Invalid setting: nonexistent_key", log.output[0])



if __name__ == "__main__":
    unittest.main()
