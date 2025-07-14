from genny.codeparser import CodeParser
from genny.filesystem import FileSystem
from genny.templater import Templater
import os

import json
import yaml
import logging

# Set up the logging configuration
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Docgen():

    def __init__(self, log_callback=None):
        self.current_template = 'standard'
        self.generated_docs = {}
        self.file_system = FileSystem()
        self.parser = CodeParser(self.file_system)
        self.log_callback = log_callback
        self.templater = Templater(log_callback=self.log_callback)

    def generate_docs(self, code_file, template='current'):
        if template != 'current':
            self.current_template = template
        try:
            source_code = self.file_system.read_file(code_file)
        except FileNotFoundError as e:
            error_message = f"Error: {e}"
            logger.error(error_message)  # Log the error
            if self.log_callback:
                self.log_callback(error_message)
            return

        try:
            template_structure = self.templater.get_template_metadata(self.current_template)
        except KeyError:
            if self.log_callback:
                self.log_callback(f"Error: Template '{self.current_template}' not found.")
            return

        code_structure = self.parser.parse_code(code_file).to_dict()
        sections = template_structure.get('sections', [])
        style = template_structure.get('style', {})

        doc_data = {}
        doc_data['title'] = os.path.basename(code_file)
        for section in sections:
            if section in code_structure:
                if style.get(section) == "detailed":
                    doc_data[section] = code_structure[section]
                elif style.get(section) == "summary":
                    doc_data[section] = [item.get('name', 'Unnamed') for item in code_structure[section]]
                else:
                    doc_data[section] = code_structure[section]

        self.generated_docs = doc_data

    def format_markdown(self, docs):
        """Generate a Markdown representation of the documentation."""
        lines = ["# Documentation\n"]
        for section, items in docs.items():
            lines.append(f"## {section.capitalize()}\n")
            if section == "imports":
                for imp in items:
                    for import_item in imp:
                        lines.append(f"- {import_item}\n")
            elif section in ["classes", "functions"]:
                for item in items:
                    lines.append(f"### {item['name']}\n")
                    if item.get('docstring'):
                        lines.append(f"**Docstring:**\n> {item['docstring']}\n")
                    if section == "classes":
                        if item.get('base_classes'):
                            lines.append("**Base Classes:**\n")
                            lines.append(', '.join(item['base_classes']) + '\n')
                        if item.get('attributes'):
                            lines.append("**Attributes:**\n")
                            for attr in item['attributes']:
                                lines.append(f"- `{attr['name']}`: {attr.get('value', 'No description')}\n")
                        if item.get('methods'):
                            lines.append("**Methods:**\n")
                            for method in item['methods']:
                                lines.append(f"- `{method['name']}` ({', '.join(method.get('parameters', []))})\n")
                                if method.get('docstring'):
                                    lines.append(f"  - **Docstring:** {method['docstring']}\n")
                                if method.get('return_type'):
                                    lines.append(f"  - **Returns:** {method['return_type']}\n")
                    else:
                        lines.append("**Parameters:**\n")
                        lines.append(', '.join(item.get('parameters', [])) + '\n')  # Default empty list for parameters
                        if item.get('return_type'):
                            lines.append(f"**Returns:**\n{item['return_type']}\n")
                        lines.append("\n")

            else:
                for item in items:
                    lines.append(f"- {item}\n")
        return '\n'.join(lines)

    def format_html(self, docs):
        """Generate an HTML representation of the documentation."""
        return self.templater.render_template(self.current_template, docs)

    def format_yaml(self, docs):
        """Generate a YAML representation of the documentation."""
        return yaml.dump(docs, default_flow_style=False, sort_keys=False)

    def export_docs(self, f, destination):
        if f not in ['json', 'markdown', 'html', 'yaml']:
            raise ValueError(f"Unsupported format: {f}")

        if not self.generated_docs:
            if self.log_callback:
                self.log_callback("No documentation generated to export.")
            return False

        try:
            formatted_output = ''
            if f == 'json':
                formatted_output = json.dumps(self.generated_docs, indent=4)
            elif f == 'markdown':
                formatted_output = self.format_markdown(self.generated_docs)
            elif f == 'html':
                if self.format_html(self.generated_docs):
                    formatted_output = self.format_html(self.generated_docs)
                else:
                    return False
            elif f == 'yaml':
                formatted_output = self.format_yaml(self.generated_docs)
            else:
                raise ValueError(f"Unsupported format: {f}")
                return False

            self.file_system.write_file(destination, formatted_output)
            if self.log_callback:
                self.log_callback(f"Export successful! File saved to: {destination}")
            return True
        except Exception as e:
            error_message = f"Error exporting documents: {e}"
            print(error_message)
            if self.log_callback:
                self.log_callback(error_message)
