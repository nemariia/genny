import unittest
from typer.testing import CliRunner
from genny.cli import app
from unittest.mock import patch, mock_open, MagicMock
import json

runner = CliRunner()

class TestCLIUseCases(unittest.TestCase):

    def test_settings_loads_successfully(self):
        valid_settings = json.dumps({
            "default_code": "main.py",
            "default_template": "standard",
            "default_format": "markdown",
            "default_destination": "docs.md"
        })

        with patch("builtins.open", mock_open(read_data=valid_settings)):
            with patch("os.path.exists", return_value=True):
                # Reload cli module after patching
                import sys
                if "genny.cli" in sys.modules:
                    del sys.modules["genny.cli"]
                import genny.cli as cli
                self.assertIn("default_code", cli.settings)

    def test_settings_file_missing(self):
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with patch("genny.cli.typer.echo") as mock_echo:
                from importlib import reload
                from genny import cli
                reload(cli)
                mock_echo.assert_any_call("Settings file not found. Using defaults.")

    def test_settings_file_corrupted(self):
        with patch("builtins.open", mock_open(read_data="{ invalid json")):
            with patch("genny.cli.typer.echo") as mock_echo:
                from importlib import reload
                from genny import cli
                reload(cli)
                mock_echo.assert_any_call("Error decoding the settings file. Using defaults.")

    def test_generate_with_all_cli_args(self):
        with patch("genny.cli.Docgen") as MockDocgen:
            instance = MockDocgen.return_value
            instance.generate_docs.return_value = None
            instance.export_docs.return_value = True
            result = runner.invoke(app, [
                "gen",
                "--code-file", "main.py",
                "--template", "standard",
                "--output-format", "markdown",
                "--destination", "docs.md"
            ])
            self.assertEqual(result.exit_code, 0)
            instance.generate_docs.assert_called_once_with("main.py", "standard")
            instance.export_docs.assert_called_once_with("markdown", "docs.md")

    def test_generate_missing_code_file_and_no_default(self):
        with patch("genny.cli.settings", {}):
            result = runner.invoke(app, ["gen"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Code file not provided and no default set", result.stdout)

    def test_generate_no_destination_prints_docs(self):
        mock_docs = {"title": "test.py", "functions": ["foo"]}
        settings_patch = {
            "default_code": "main.py",
            "default_template": "standard",
            "default_format": "json"
            # Note: no default_destination
        }
        with patch("genny.cli.settings", settings_patch), \
             patch("genny.cli.Docgen") as MockDocgen, \
             patch("genny.cli.pyfiglet.figlet_format", return_value="FIGLET"):
            instance = MockDocgen.return_value
            instance.generate_docs.return_value = None
            instance.generated_docs = mock_docs
            result = runner.invoke(app, ["gen"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("The documentation will be printed here", result.stdout)
            self.assertIn("test.py", result.stdout)

    def test_list_templates_success(self):
        with patch("genny.templater.Templater.list_templates", return_value=["template1", "template2"]):
            result = runner.invoke(app, ["list-templates"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("template1", result.stdout)
            self.assertIn("template2", result.stdout)
