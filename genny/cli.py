import typer
import pyfiglet
from .docgen import Docgen
from .templater import Templater
from .versioncontrol import VersionControl
from .settingsmanager import SettingsManager
import json
import os

app = typer.Typer()
# TODO: add generation for all files in a folder
settings_manager = SettingsManager()


# Load settings from the settings.json file
def load_settings():
    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    try:
        with open(settings_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        typer.echo("Settings file not found. Using defaults.")
        return {}
    except json.JSONDecodeError:
        typer.echo("Error decoding the settings file. Using defaults.")
        return {}


settings = load_settings()


@app.command()
def gen(code_file: str = typer.Option(None, help="Path to the code file"),
        template: str = typer.Option(None, help="Template to use for documentation"),
        output_format: str = typer.Option(None, help="Output format (e.g., markdown, html, json, yaml)"),
        destination: str = typer.Option(None, help="Destination file path for the generated documentation")):
    """
    Generates documentation from the specified code file using the given template and output format.
    If a destination is specified, exports the documentation; otherwise, prints it to the console.
    """
    # Use settings.json defaults if parameters are not provided
    code_file = code_file or settings.get("default_code")
    template = template or settings.get("default_template", "current")
    output_format = output_format or settings.get("default_format", "markdown")
    destination = destination or settings.get("default_destination")

    if not code_file:
        typer.echo("Code file not provided and no default set in settings.json. Exiting.")
        return

    typer.echo(pyfiglet.figlet_format("generating docs...", font="banner"))
    dg = Docgen()
    try:
        dg.generate_docs(code_file, template)
        if destination:
            dg.export_docs(output_format, destination)
        else:
            typer.echo("No destination provided. The documentation will be printed here:")
            typer.echo(dg.generated_docs)
    except Exception as e:
        typer.echo(f"An error occurred: {str(e)}", err=True)

    print(f"Generated successfully at {destination}")
    repo = settings_manager.settings.get("repo_path")
    if repo:
        vc = VersionControl(repo)
        vc.commit_changes("committed via CLI")
        print(f"Changes committed to {repo}")


@app.command()
def list_templates():
    """
    Displays a list of available templates.
    """
    templates = Templater().list_templates()
    typer.echo(pyfiglet.figlet_format("available Templates:", font="banner"))
    for template in templates:
        typer.echo(template)


@app.command()
def delete_template(template: str):
    """
    Deletes a specified template.
    """
    typer.echo(f"Deleting template: {template}")
    
    # Delete the template using Templater
    try:
        templater = Templater()
        templater.delete_template(template_name=template)
        typer.echo(f"Template '{template}' deleted successfully.")
    except ValueError as e:
        typer.echo(f"Error: {e}")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")


@app.command()
def add_template(template_name: str):
    """
    Adds a new template to the available templates.

    Arguments:
        template_name: The name of the template to be added.
    """
    typer.echo(f"Adding template: {template_name}")

    # Prompt user for sections
    sections_input = typer.prompt(
        "Enter sections (comma-separated, e.g., classes,functions,imports)",
        default="classes,functions,imports"
    )
    sections = [section.strip() for section in sections_input.split(",")]

    # Prompt user for styles for each section
    styles = {}
    for section in sections:
        style = typer.prompt(
            f"Enter style for section '{section}' (e.g., detailed, summary)",
            default="detailed"
        )
        styles[section] = style

    try:
        # Create an instance of Templater
        templater = Templater()

        # Add the new template
        if templater.add_template(template_name=template_name, sections=sections, styling=styles):
            typer.echo(f"Template '{template_name}' added successfully!")
    except ValueError as e:
        typer.echo(f"Error: {e}")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")


@app.command()
def select_template():
    """
    Allows the user to select a template from the list of available templates.
    The selected template will be saved as the default template in settings.json.
    """
    try:
        # Create an instance of Templater
        templater = Templater()
        templates = templater.list_templates()

        if not templates:
            typer.echo("No templates available.")
            return

        typer.echo(pyfiglet.figlet_format("Available Templates:", font="banner"))
        for idx, template in enumerate(templates, start=1):
            typer.echo(f"{idx}. {template}")

        # Prompt the user to select a template by index
        choice = typer.prompt("Enter the number of the template you want to select")
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(templates):
                selected_template = templates[choice_idx]

                # Update the default template in settings
                settings_manager = SettingsManager()
                settings_manager.update_setting("default_template", selected_template)

                typer.echo(f"Template '{selected_template}' selected and saved as default.")
            else:
                typer.echo("Invalid choice. Please select a valid template number.")
        except ValueError:
            typer.echo("Invalid input. Please enter a number corresponding to a template.")

    except Exception as e:
        typer.echo(f"An error occurred: {str(e)}")


@app.command()
def add_repo(repo: str = typer.Option(None, help="Path to the repository")):
    """
    Adds or initializes a repository for version control.
    """
    repo_path = repo or settings_manager.settings.get("repo_path")
    if not repo_path:
        typer.echo("Repository path not provided and no default set in settings.json. Exiting.")
        return

    VersionControl(repo_path)
    settings_manager.update_setting("repo_path", repo_path)  # Save the repository path in settings
    typer.echo(f"Repository initialized at: {repo_path}")


@app.command()
def commit_history():
    """
    Displays the commit history of the current repository.
    """
    repo_path = settings_manager.settings.get("repo_path")
    if not repo_path:
        typer.echo("Repository path not set. Use the 'add_repo' command to set it.")
        return

    vc = VersionControl(repo_path)
    history = vc.get_commit_history()
    if history:
        typer.echo("Commit History:")
        typer.echo(history)
    else:
        typer.echo("No commits found or an error occurred.")


@app.command()
def checkout_branch(b: str = typer.Option(None, help="Branch name")):
    repo_path = settings_manager.settings.get("repo_path")
    if not repo_path:
        typer.echo("Repository path not set. Use the 'add_repo' command to set it.")
        return

    vc = VersionControl(repo_path)
    vc.checkout(b)


@app.command()
def edit_settings():
    """
    Edit settings interactively.
    """
    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    try:
        with open(settings_path, "r") as file:
            current_settings = json.load(file)

        typer.echo("Current Settings:")
        for key, value in current_settings.items():
            typer.echo(f"{key}: {value}")

        key = typer.prompt("Enter the setting key to update")
        if key not in current_settings:
            typer.echo(f"Error: '{key}' is not a valid setting key.")
            return

        value = typer.prompt(f"Enter the new value for '{key}'")
        current_settings[key] = value

        with open(settings_path, "w") as file:
            json.dump(current_settings, file, indent=4)

        typer.echo(f"Updated '{key}' to '{value}' in settings.json.")
    except Exception as e:
        typer.echo(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    app.command()(gen)
