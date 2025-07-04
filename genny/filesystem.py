import os

class FileSystem:
    def read_file(self, file_path):
        """
        Reads the content of a file.

        Parameters:
            file_path (str): The path to the file.

        Returns:
            str: Content of the file if it exists.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")
        with open(file_path, 'r') as file:
            return file.read()

    def write_file(self, file_path, data):
        """
        Writes data to a file.

        Parameters:
            file_path (str): The path to the file.
            data (str): The content to write to the file.
        """
        with open(file_path, 'w') as file:
            file.write(data)
