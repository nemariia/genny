import os
import tempfile
import unittest
import subprocess
from genny.versioncontrol import VersionControl
from unittest.mock import patch, MagicMock


class TestVersionControl(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for a mock Git repo
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.repo_dir.name
        subprocess.run(['git', 'init', self.repo_path], check=True)
        self.vc = VersionControl(self.repo_path)

        # Create a file to commit
        file_path = os.path.join(self.repo_path, 'test.txt')
        with open(file_path, 'w') as f:
            f.write("Test content")
        subprocess.run(['git', '-C', self.repo_path, 'add', file_path], check=True)
        subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', 'Initial commit'], check=True)

    def tearDown(self):
        # Clean up the temporary directory
        self.repo_dir.cleanup()

    def test_checkout(self):
        # Create and switch to a new branch
        subprocess.run(['git', '-C', self.repo_path, 'checkout', '-b', 'test-branch'], check=True)
        self.vc.checkout('test-branch')
        branches = subprocess.run(
            ['git', '-C', self.repo_path, 'branch'], text=True, capture_output=True
        ).stdout
        self.assertIn('test-branch', branches)

    @patch("subprocess.run")
    def test_checkout_creates_and_switches_to_new_branch(self, mock_run):
        # Simulate `git branch --list` returns nothing (branch does not exist)
        mock_run.side_effect = [
            MagicMock(stdout=""),  # No such branch
            MagicMock()  # Simulate success of `git checkout -b branch`
        ]

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        vc.checkout("feature-xyz")

        self.assertEqual(vc.branch_name, "feature-xyz")
        log.assert_called_once_with("Created and switched to new branch 'feature-xyz'")
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(['git', '-C', "fake/repo", 'checkout', '-b', 'feature-xyz'], check=True)

    @patch("subprocess.run")
    def test_checkout_handles_subprocess_error(self, mock_run):
        # Simulate subprocess error (e.g. invalid branch name)
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        vc.checkout("invalid/branch")

        log.assert_called_once()
        self.assertIn("Failed to checkout branch 'invalid/branch'", log.call_args[0][0])

    def test_commit_changes(self):
        # Test committing changes
        new_file = os.path.join(self.repo_path, 'new_test.txt')
        with open(new_file, 'w') as f:
            f.write("Another test content")
        self.vc.commit_changes("Added new test file")
        log = self.vc.get_commit_history()
        self.assertIn("Added new test file", log)

    def test_commit_no_changes(self):
        # Test committing when there are no changes
        log = MagicMock()
        vc = VersionControl(self.repo_path, log_callback=log)
        vc.commit_changes("No changes")
        log.assert_called_once()
        self.assertIn("No changes to commit.", log.call_args[0][0])

    @patch("subprocess.run")
    def test_commit_changes_handles_called_process_error(self, mock_run):
        # Simulate subprocess failure during `git status`
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd='git',
            stderr='Some git error'
        )

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        vc.commit_changes("test message")

        log.assert_called_once()
        self.assertIn("Failed to commit changes: Some git error", log.call_args[0][0])

    @patch("subprocess.run")
    def test_commit_changes_handles_generic_exception(self, mock_run):
        # Simulate a generic error
        mock_run.side_effect = Exception("something broke")

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        vc.commit_changes("test message")

        log.assert_called_once()
        self.assertIn("Unexpected error: something broke", log.call_args[0][0])

    @patch("subprocess.run")
    def test_get_commit_history_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=['git'], returncode=0, stdout="abc123 Initial commit\nbcd234 Added feature"
        )

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        result = vc.get_commit_history()

        self.assertEqual(result, "abc123 Initial commit\nbcd234 Added feature")
        log.assert_called_once_with("abc123 Initial commit\nbcd234 Added feature")

    @patch("subprocess.run")
    def test_get_commit_history_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd='git log',
            stderr='fatal: not a git repository'
        )

        log = MagicMock()
        vc = VersionControl("fake/repo", log_callback=log)
        result = vc.get_commit_history()

        self.assertIn("Failed to retrieve commit history", result)
        log.assert_called_once()
        self.assertIn("Failed to retrieve commit history", log.call_args[0][0])
