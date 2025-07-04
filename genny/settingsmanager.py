import json
import logging
import os

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(script_dir, settings_file)
        self.settings = {
            "default_code": "",
            "default_template": "standard",
            "default_format": "markdown",
            "default_destination": "",
            "repo_path": ""
        }
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.settings_file, "r") as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            logging.warning(f"Settings file '{self.settings_file}' not found. Using default settings.")
            self.save_settings()
        except json.JSONDecodeError:
            logging.error(f"Error reading settings file '{self.settings_file}'. Using default settings.")

    def save_settings(self):
        try:
            with open(self.settings_file, "w") as file:
                json.dump(self.settings, file, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings to file '{self.settings_file}': {e}")

    def update_setting(self, key, value):
        if key in self.settings:
            self.settings[key] = value
            self.save_settings()
        else:
            logging.info(f"Invalid setting: {key}")

