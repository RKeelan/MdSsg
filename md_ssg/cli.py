import click
from jinja2 import Environment, FileSystemLoader
import markdown
from markdown.extensions import footnotes
import os
import re
import shutil
import sys
import toml


@click.command()
@click.version_option()
@click.argument('config_path', type=click.Path(exists=True))
@click.option('-v', '--verbose', is_flag=True, help="Print verbose output")
def cli(config_path, verbose):
    # Read the TOML configuration file
    with open(config_path, 'r') as f:
        config = toml.load(f)

    # Define mandatory fields
    mandatory_fields = ['content_dir', 'templates_dir', 'static_dir', 'css_files', 'site_dir']

    # Check if all mandatory fields are present
    missing_fields = [field for field in mandatory_fields if field not in config]
    if missing_fields:
        print(f"Error: The following mandatory fields are missing from the config file: {', '.join(missing_fields)}")
        sys.exit(1)

    # Get the directory of the config file
    config_dir = os.path.dirname(os.path.abspath(config_path))

    # Extract parameters from the configuration, make paths relative to the config file, and resolve them
    content_dir = os.path.abspath(os.path.join(config_dir, config['content_dir']))
    templates_dir = os.path.abspath(os.path.join(config_dir, config['templates_dir']))
    static_dir = os.path.abspath(os.path.join(config_dir, config['static_dir']))
    css_files = config['css_files']
    site_dir = os.path.abspath(os.path.join(config_dir, config['site_dir']))

    # Print the configuration parameters
    print("Configuration parameters:")
    print(f"Content Directory: {content_dir}")
    print(f"Templates Directory: {templates_dir}")
    print(f"Static Directory: {static_dir}")
    print(f"CSS Files: {css_files}")
    print(f"Site Directory: {site_dir}")

    # Ensure the output directory exists
    if not os.path.exists(site_dir):
        os.makedirs(site_dir)

    # Copy static files to the output directory
    static_output_dir = os.path.join(site_dir, 'static')
    if os.path.exists(static_output_dir):
        shutil.rmtree(static_output_dir)
    shutil.copytree(static_dir, static_output_dir)

    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader(templates_dir))

    # Load the page template
    page_template = env.get_template('page.html')

    # Process Markdown files recursively in the content directory
    process_directory(content_dir, site_dir, env, page_template, css_files, verbose)

def process_directory(content_dir, site_dir, env, page_template, css_files, verbose):
    for root, dirs, files in os.walk(content_dir):
        for filename in files:
            if filename.endswith('.md'):
                input_filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(input_filepath, content_dir)
                output_filepath = os.path.join(site_dir, os.path.splitext(relative_path)[0] + '.html')

                # Create the output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

                with open(input_filepath, 'r', encoding='utf-8') as f:
                    md_content = f.read()

                # Extract the page title and remove it from the content
                page_title, md_content = extract_title(md_content)

                if not page_title:
                    print(f"Error: No level 1 header found in {input_filepath}")
                    sys.exit(1)

                # Convert Markdown to HTML with footnotes support
                html_content = markdown.markdown(md_content, extensions=['footnotes'])

                # Render the page template with the necessary variables
                page_html = page_template.render(
                    site_title=page_title,
                    page_title=page_title,
                    content=html_content,
                    css_files=css_files,
                )

                # Write the rendered HTML to the output directory
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    f.write(page_html)
                
                if verbose:
                    print(f"Generated '{output_filepath}' from '{input_filepath}'")

def extract_title(md_content):
    # Regular expression to match the first level 1 header and following blank lines
    pattern = r'^#\s*(.+?)\s*\n\s*\n*'
    match = re.match(pattern, md_content, re.MULTILINE)
    
    if match:
        title = match.group(1)
        content = md_content[match.end():].lstrip()
        return title, content
    else:
        return None, md_content
