import subprocess


class VersionControl:
    def __init__(self, repo_path, log_callback=None):
        self.log_callback = log_callback
        self.repo_path = repo_path
        self.branch_name = 'main'

    def checkout(self, branch_name):
        """Checkout a specific branch."""
        try:
            # Check if the branch already exists
            result = subprocess.run(
                ['git', '-C', self.repo_path, 'branch', '--list', branch_name],
                check=True, text=True, capture_output=True
            )
            if branch_name in result.stdout:
                # Branch exists, just switch to it
                subprocess.run(['git', '-C', self.repo_path, 'checkout', branch_name], check=True)
                message = f"Switched to existing branch '{branch_name}'"
            else:
                # Branch does not exist, create and switch to it
                subprocess.run(['git', '-C', self.repo_path, 'checkout', '-b', branch_name], check=True)
                message = f"Created and switched to new branch '{branch_name}'"
    
            self.branch_name = branch_name
        except subprocess.CalledProcessError as e:
                message = f"Failed to checkout branch '{branch_name}': {e}"
        if self.log_callback:
            self.log_callback(message)


    def commit_changes(self, message="Quick commit"):
        """Commit all changes in the repo with a message."""
        try:
            # Check if there are changes to commit
            result = subprocess.run(
                ['git', '-C', self.repo_path, 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                # No changes to commit
                message = "No changes to commit."
                if self.log_callback:
                    self.log_callback(message)
                return

            # Add and commit changes
            subprocess.run(['git', '-C', self.repo_path, 'add', '.'], check=True)
            subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', message], check=True)

            # Log success message
            message = "Changes committed successfully."
        except subprocess.CalledProcessError as e:
            message = f"Failed to commit changes: {e.stderr or e}"
        except Exception as e:
            message = f"Unexpected error: {str(e)}"

        # Log the message
        if self.log_callback:
            self.log_callback(message)


    def get_commit_history(self):
        """Retrieve the commit history of the current branch."""
        try:
            completed_process = subprocess.run(
                ['git', '-C', self.repo_path, 'log', '--oneline'],
                check=True, text=True, capture_output=True)
            message = completed_process.stdout.strip()
            if self.log_callback:
                self.log_callback(message)
            return message
        except subprocess.CalledProcessError as e:
            message = f"Failed to retrieve commit history: {e}"
            if self.log_callback:
                self.log_callback(message)
            return message
