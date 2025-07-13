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

    def test_generate_docs_exception_handled(self):
        with patch("genny.cli.Docgen") as MockDocgen, \
         patch("genny.cli.settings", {
             "default_code": "main.py",
             "default_template": "standard",
             "default_format": "json",
             "default_destination": "docs.md"
         }), \
         patch("genny.cli.pyfiglet.figlet_format", return_value="FIGLET"), \
         patch("genny.cli.settings_manager.settings", {}):  # ensure no repo commits

            instance = MockDocgen.return_value
            instance.generate_docs.side_effect = RuntimeError("crash inside generate_docs")

            result = runner.invoke(app, ["gen"])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("An error occurred: crash inside generate_docs", result.stderr)

    def test_list_templates_success(self):
        with patch("genny.templater.Templater.list_templates", return_value=["template1", "template2"]):
            result = runner.invoke(app, ["list-templates"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("template1", result.stdout)
            self.assertIn("template2", result.stdout)

    def test_delete_template_success(self):
        with patch("genny.templater.Templater.delete_template", return_value=None):
            result = runner.invoke(app, ["delete-template", "template1"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("deleted successfully", result.stdout)

    def test_delete_template_not_found(self):
        with patch("genny.templater.Templater.delete_template", side_effect=ValueError("Template not found")):
            result = runner.invoke(app, ["delete-template", "missing_template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Error: Template not found", result.stdout)

    def test_delete_template_unexpected_error(self):
        with patch("genny.templater.Templater.delete_template", side_effect=RuntimeError("internal failure")):
            result = runner.invoke(app, ["delete-template", "template1"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("An unexpected error occurred: internal failure", result.stdout)

    def test_delete_template_missing_argument(self):
        result = runner.invoke(app, ["delete-template"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing argument 'TEMPLATE'", result.stderr)

    def test_add_template_success(self):
        with patch("genny.cli.typer.prompt", side_effect=[
            "classes,functions",  # sections input
            "detailed",           # style for 'classes'
            "summary"             # style for 'functions'
        ]), patch("genny.templater.Templater.add_template", return_value=True):
            result = runner.invoke(app, ["add-template", "new_template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Template 'new_template' added successfully!", result.stdout)

    def test_add_template_value_error(self):
        with patch("genny.cli.typer.prompt", side_effect=[
            "classes", "detailed"
        ]), patch("genny.templater.Templater.add_template", side_effect=ValueError("already exists")):
            result = runner.invoke(app, ["add-template", "existing_template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Error: already exists", result.stdout)

    def test_add_template_unexpected_error(self):
        with patch("genny.cli.typer.prompt", side_effect=[
            "functions", "summary"
        ]), patch("genny.templater.Templater.add_template", side_effect=RuntimeError("crash")):
            result = runner.invoke(app, ["add-template", "bad_template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("An unexpected error occurred: crash", result.stdout)

    def test_add_template_missing_argument(self):
        result = runner.invoke(app, ["add-template"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Usage", result.stderr)
        self.assertIn("Missing argument 'TEMPLATE_NAME'", result.stderr)

    def test_select_template_success(self):
        with patch("genny.templater.Templater.list_templates", return_value=["a", "b"]), \
             patch("genny.cli.typer.prompt", return_value="2"), \
             patch("genny.settingsmanager.SettingsManager.update_setting") as mock_update, \
             patch("genny.cli.pyfiglet.figlet_format", return_value="FIGLET"):
            result = runner.invoke(app, ["select-template"])
            self.assertEqual(result.exit_code, 0)
            mock_update.assert_called_once_with("default_template", "b")
            self.assertIn("Template 'b' selected and saved as default.", result.stdout)

    def test_select_template_invalid_index(self):
        with patch("genny.templater.Templater.list_templates", return_value=["a", "b"]), \
             patch("genny.cli.typer.prompt", return_value="5"), \
             patch("genny.cli.pyfiglet.figlet_format", return_value="FIGLET"):
            result = runner.invoke(app, ["select-template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Invalid choice", result.stdout)

    def test_select_template_non_numeric_input(self):
        with patch("genny.templater.Templater.list_templates", return_value=["a", "b"]), \
             patch("genny.cli.typer.prompt", return_value="abc"), \
             patch("genny.cli.pyfiglet.figlet_format", return_value="FIGLET"):
            result = runner.invoke(app, ["select-template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Invalid input. Please enter a number", result.stdout)

    def test_select_template_no_templates(self):
        with patch("genny.templater.Templater.list_templates", return_value=[]):
            result = runner.invoke(app, ["select-template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("No templates available.", result.stdout)

    def test_select_template_unexpected_exception(self):
        with patch("genny.templater.Templater.list_templates", side_effect=RuntimeError("failure")):
            result = runner.invoke(app, ["select-template"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("An error occurred: failure", result.stdout)

    def test_add_repo_with_argument(self):
        with patch("genny.cli.VersionControl") as mock_vc, \
             patch("genny.cli.settings_manager.update_setting") as mock_update:
            result = runner.invoke(app, ["add-repo", "--repo", "my/repo"])
            self.assertEqual(result.exit_code, 0)
            mock_vc.assert_called_once_with("my/repo")
            mock_update.assert_called_once_with("repo_path", "my/repo")
            self.assertIn("Repository initialized at: my/repo", result.stdout)

    def test_add_repo_from_settings(self):
        with patch("genny.cli.settings_manager.settings", {"repo_path": "from/settings"}), \
             patch("genny.cli.VersionControl") as mock_vc, \
             patch("genny.cli.settings_manager.update_setting") as mock_update:
            result = runner.invoke(app, ["add-repo"])
            self.assertEqual(result.exit_code, 0)
            mock_vc.assert_called_once_with("from/settings")
            mock_update.assert_called_once_with("repo_path", "from/settings")
            self.assertIn("Repository initialized at: from/settings", result.stdout)

    def test_add_repo_no_input_or_setting(self):
        with patch("genny.cli.settings_manager.settings", {}):
            result = runner.invoke(app, ["add-repo"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Repository path not provided and no default set", result.stdout)

    def test_commit_history_with_commits(self):
        with patch("genny.cli.settings_manager.settings", {"repo_path": "some/repo"}), \
             patch("genny.cli.VersionControl") as mock_vc:
            mock_vc.return_value.get_commit_history.return_value = "commit1\ncommit2"
            result = runner.invoke(app, ["commit-history"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Commit History:", result.stdout)
            self.assertIn("commit1", result.stdout)
            self.assertIn("commit2", result.stdout)

    def test_commit_history_no_commits(self):
        with patch("genny.cli.settings_manager.settings", {"repo_path": "some/repo"}), \
             patch("genny.cli.VersionControl") as mock_vc:
            mock_vc.return_value.get_commit_history.return_value = ""
            result = runner.invoke(app, ["commit-history"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("No commits found or an error occurred.", result.stdout)

    def test_commit_history_no_repo_path(self):
        with patch("genny.cli.settings_manager.settings", {}):
            result = runner.invoke(app, ["commit-history"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Repository path not set", result.stdout)

    def test_checkout_branch_success(self):
        with patch("genny.cli.settings_manager.settings", {"repo_path": "repo/"}), \
             patch("genny.cli.VersionControl") as mock_vc:
            result = runner.invoke(app, ["checkout-branch", "--b", "dev"])
            self.assertEqual(result.exit_code, 0)
            mock_vc.return_value.checkout.assert_called_once_with("dev")

    def test_checkout_branch_no_repo_path(self):
        with patch("genny.cli.settings_manager.settings", {}):
            result = runner.invoke(app, ["checkout-branch", "--b", "dev"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Repository path not set. Use the 'add_repo' command to set it.", result.stdout)
