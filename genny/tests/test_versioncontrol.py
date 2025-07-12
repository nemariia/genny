import os
import tempfile
import unittest
import subprocess
from genny.versioncontrol import VersionControl


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

    def test_commit_changes(self):
        # Test committing changes
        new_file = os.path.join(self.repo_path, 'new_test.txt')
        with open(new_file, 'w') as f:
            f.write("Another test content")
        self.vc.commit_changes("Added new test file")
        log = self.vc.get_commit_history()
        self.assertIn("Added new test file", log)

    def test_get_commit_history(self):
        # Test retrieving commit history
        history = self.vc.get_commit_history()
        self.assertTrue(len(history) > 0)
