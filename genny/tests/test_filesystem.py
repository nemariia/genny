import unittest
import os
import tempfile
from genny.filesystem import FileSystem

class TestFileSystem(unittest.TestCase):

    def setUp(self):
        self.file_system = FileSystem()
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_read_file(self):
        # Create a temporary file with content
        file_path = os.path.join(self.temp_dir.name, "test_read.txt")
        with open(file_path, 'w') as file:
            file.write("Sample content")
        
        # Read the file using FileSystem and verify content
        content = self.file_system.read_file(file_path)
        self.assertEqual(content, "Sample content")

    def test_write_file(self):
        # Create a temporary file path
        file_path = os.path.join(self.temp_dir.name, "test_write.txt")
        
        # Write content using FileSystem
        self.file_system.write_file(file_path, "Test data")
        
        # Verify that the content is correctly written
        with open(file_path, 'r') as file:
            content = file.read()
        self.assertEqual(content, "Test data")

    def test_read_nonexistent_file(self):
        # Attempt to read a file that does not exist
        file_path = os.path.join(self.temp_dir.name, "nonexistent.txt")
        with self.assertRaises(FileNotFoundError) as context:
            self.file_system.read_file(file_path)
        self.assertEqual(str(context.exception), f"The file '{file_path}' does not exist.")

    def test_write_and_read_back(self):
        # Write data to a file and read it back
        file_path = os.path.join(self.temp_dir.name, "test_round_trip.txt")
        data = "Round-trip test content"
        
        self.file_system.write_file(file_path, data)
        read_data = self.file_system.read_file(file_path)
        
        self.assertEqual(read_data, data)
