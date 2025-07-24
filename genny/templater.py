from jinja2 import Environment, FileSystemLoader
from genny.filesystem import FileSystem
import os
import json


class Templater:
    def __init__(self, template_dir="templates", file_system=None, log_callback=None):
        """
        Initialize the Templater class.
        """
        self.file_system = file_system or FileSystem()  # Default to a FileSystem instance if not provided
        self.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_dir)
        self.metadata_file = os.path.join(self.base_dir, "templates_metadata.json")
        self.env = Environment(loader=FileSystemLoader(self.base_dir))
        self.templates_metadata = self._load_metadata()
        self.log_callback = log_callback


    def _load_metadata(self):
        """
        Load metadata from the metadata file.
        If the file doesn't exist, return an empty dictionary.
        """
        try:
            with open(self.metadata_file, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Metadata file {self.metadata_file} not found. Using an empty dictionary.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.metadata_file}. Using an empty dictionary.")
            return {}

    def _save_metadata(self):
        """Save the current metadata to the metadata file."""
        try:
            with open(self.metadata_file, "w") as file:
                json.dump(self.templates_metadata, file, indent=4)
        except (OSError, TypeError) as e:
            error_message = f"Error saving metadata to {self.metadata_file}: {e}"
            print(error_message)
            if self.log_callback:
                self.log_callback(error_message)

    def add_template(self, template_name, sections, styling):
        """
        Add a new template to the metadata.

        Parameters:
            - template_name: The name of the template.
            - sections: Sections defined for the template.
            - styling: Styling rules for the template.
        """
        if template_name in self.templates_metadata:
            print(f"Template '{template_name}' already exists.")
            return False
        
        self.templates_metadata[template_name] = {"sections": sections, "style": styling}
        self._save_metadata()
        return True

    def get_template_metadata(self, template_name):
        """
        Retrieve metadata for a specific template.

        Parameters:
            - template_name: The name of the template.

        Returns:
            - Metadata for the template (sections and style).
        """
        if template_name not in self.templates_metadata:
            raise ValueError(f"Template '{template_name}' not found.")
        return self.templates_metadata[template_name]

    def _template_exists(self, template_file):

        try:
            self.env.loader.get_source(self.env, template_file)
            return True
        except Exception:
            return False


    def render_template(self, template_name, context):
        """
        Render a Jinja template with the provided context.

        Parameters:
            - template_name: The name of the Jinja template file.
            - context: A dictionary of variables to pass to the template.

        Returns:
            - Rendered template as a string.
        """
        
        try:
            # Ensure template_name only includes the base file name, not a path
            template_file = f"{template_name}.jinja"

            # Check if the template exists
            if self._template_exists(template_file):
                template = self.env.get_template(template_file)
            else:
                self.log_callback(f"Template '{template_file}' not found. Using fallback template.")
                template = self.env.get_template("fallback.jinja")

        # Render the template
            return template.render(context)
        except Exception as e:
            self.log_callback(f"Error rendering template '{template_name}': {e}")
            raise ValueError(f"Error rendering template '{template_name}': {e}")
            return False

    def delete_template(self, template_name):
        if template_name in self.templates_metadata:
            del self.templates_metadata[template_name]
            self._save_metadata()
        else:
            raise ValueError(f"Template '{template_name}' not found.")

        template_file_path = os.path.join(self.base_dir, f"{template_name}.jinja")
        
        if os.path.exists(template_file_path):
            os.remove(template_file_path)


    def list_templates(self):
        """
        List all available templates from metadata.

        Returns:
            - List of template names.
        """
        return list(self.templates_metadata.keys())
