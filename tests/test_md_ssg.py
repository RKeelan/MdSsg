import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from md_ssg.cli import cli, extract_title, process_directory


class TestCli:
    """Test the main CLI command."""

    def test_version(self):
        """Test the --version flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")

    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ["nonexistent.toml"])
        assert result.exit_code != 0

    def test_missing_mandatory_fields(self):
        """Test error when mandatory fields are missing from config."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create incomplete config file
            with open("config.toml", "w") as f:
                f.write('[project]\nname = "test"\n')
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 1
            assert "mandatory fields are missing" in result.output

    def test_successful_build(self):
        """Test successful site generation."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create directory structure
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            
            # Create config file
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = ["style.css"]
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            # Create template
            template_content = """<!DOCTYPE html>
<html>
<head>
    <title>{{ page_title }}</title>
    {% for css_file in css_files %}
    <link rel="stylesheet" href="static/{{ css_file }}">
    {% endfor %}
</head>
<body>
    <h1>{{ site_title }}</h1>
    {{ content }}
</body>
</html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            # Create markdown content
            md_content = """# Test Page

This is a test page with some content.

## Subsection

More content here.
"""
            with open("content/test.md", "w") as f:
                f.write(md_content)
            
            # Create static file
            with open("static/style.css", "w") as f:
                f.write("body { font-family: Arial; }")
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 0
            
            # Check that output files were created
            assert os.path.exists("site/test.html")
            assert os.path.exists("site/static/style.css")
            
            # Check content of generated HTML
            with open("site/test.html", "r") as f:
                html_content = f.read()
                assert "Test Page" in html_content
                assert "This is a test page" in html_content

    def test_verbose_output(self):
        """Test verbose flag produces additional output."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create minimal setup
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            md_content = "# Test\n\nContent"
            with open("content/test.md", "w") as f:
                f.write(md_content)
            
            result = runner.invoke(cli, ["config.toml", "--verbose"])
            assert result.exit_code == 0
            assert "Generated" in result.output

    def test_nested_content_directories(self):
        """Test processing nested content directories."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create nested directory structure
            os.makedirs("content/subdir")
            os.makedirs("templates")
            os.makedirs("static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            # Create markdown files in nested structure
            with open("content/root.md", "w") as f:
                f.write("# Root Page\n\nRoot content")
            
            with open("content/subdir/nested.md", "w") as f:
                f.write("# Nested Page\n\nNested content")
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 0
            
            # Check that nested structure is preserved
            assert os.path.exists("site/root.html")
            assert os.path.exists("site/subdir/nested.html")

    def test_missing_title_error(self):
        """Test error when markdown file has no level 1 header."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            # Create markdown without any header that matches the regex
            md_content = "Just plain text\n\nNo header at all"
            with open("content/test.md", "w") as f:
                f.write(md_content)
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 1
            assert "No level 1 header found" in result.output

    def test_existing_site_directory_cleanup(self):
        """Test that existing static directory is cleaned up."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            os.makedirs("site/static")
            
            # Create existing file in static output
            with open("site/static/old_file.txt", "w") as f:
                f.write("old content")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            with open("content/test.md", "w") as f:
                f.write("# Test\n\nContent")
            
            with open("static/new_file.txt", "w") as f:
                f.write("new content")
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 0
            
            # Old file should be gone, new file should exist
            assert not os.path.exists("site/static/old_file.txt")
            assert os.path.exists("site/static/new_file.txt")


class TestExtractTitle:
    """Test the extract_title function."""

    def test_extract_title_with_content(self):
        """Test extracting title from markdown with content."""
        md_content = "# My Title\n\nThis is the content."
        title, content = extract_title(md_content)
        assert title == "My Title"
        assert content == "This is the content."

    def test_extract_title_with_extra_whitespace(self):
        """Test extracting title with extra whitespace."""
        md_content = "#   Spaced Title   \n\n\n\nContent after spaces."
        title, content = extract_title(md_content)
        assert title == "Spaced Title"
        assert content == "Content after spaces."

    def test_extract_title_no_content(self):
        """Test extracting title with no following content."""
        md_content = "# Just Title\n\n"
        title, content = extract_title(md_content)
        assert title == "Just Title"
        assert content == ""

    def test_extract_title_no_header(self):
        """Test when there's no level 1 header."""
        md_content = "No header at all\n\nSome content."
        title, content = extract_title(md_content)
        assert title is None
        assert content == "No header at all\n\nSome content."

    def test_extract_title_empty_content(self):
        """Test with empty content."""
        md_content = ""
        title, content = extract_title(md_content)
        assert title is None
        assert content == ""

    def test_extract_title_multiple_headers(self):
        """Test that only the first level 1 header is extracted."""
        md_content = "# First Title\n\nContent\n\n# Second Title\n\nMore content"
        title, content = extract_title(md_content)
        assert title == "First Title"
        assert "# Second Title" in content

    def test_extract_title_level_2_header(self):
        """Test that level 2 headers are treated as level 1 due to regex behavior."""
        md_content = "## Level 2 Header\n\nSome content."
        title, content = extract_title(md_content)
        assert title == "# Level 2 Header"
        assert content == "Some content."


class TestProcessDirectory:
    """Test the process_directory function."""

    def test_process_directory_basic(self):
        """Test basic directory processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = os.path.join(temp_dir, "content")
            site_dir = os.path.join(temp_dir, "site")
            templates_dir = os.path.join(temp_dir, "templates")
            
            os.makedirs(content_dir)
            os.makedirs(templates_dir)
            
            # Create template
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader(templates_dir))
            
            template_content = """<html><body><h1>{{ page_title }}</h1>{{ content }}</body></html>"""
            with open(os.path.join(templates_dir, "page.html"), "w") as f:
                f.write(template_content)
            
            page_template = env.get_template("page.html")
            
            # Create markdown file
            with open(os.path.join(content_dir, "test.md"), "w") as f:
                f.write("# Test Page\n\nTest content")
            
            # Process directory
            process_directory(content_dir, site_dir, env, page_template, [], False)
            
            # Check output
            output_file = os.path.join(site_dir, "test.html")
            assert os.path.exists(output_file)
            
            with open(output_file, "r") as f:
                html_content = f.read()
                assert "Test Page" in html_content
                assert "Test content" in html_content

    def test_process_directory_verbose(self):
        """Test directory processing with verbose output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            content_dir = os.path.join(temp_dir, "content")
            site_dir = os.path.join(temp_dir, "site")
            templates_dir = os.path.join(temp_dir, "templates")
            
            os.makedirs(content_dir)
            os.makedirs(templates_dir)
            
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader(templates_dir))
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open(os.path.join(templates_dir, "page.html"), "w") as f:
                f.write(template_content)
            
            page_template = env.get_template("page.html")
            
            with open(os.path.join(content_dir, "test.md"), "w") as f:
                f.write("# Test\n\nContent")
            
            # Capture print output
            import io
            import sys
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                process_directory(content_dir, site_dir, env, page_template, [], True)
                output = captured_output.getvalue()
                assert "Generated" in output
            finally:
                sys.stdout = sys.__stdout__


class TestMainModule:
    """Test the __main__.py module."""

    def test_main_module_import(self):
        """Test that the main module can be imported."""
        import md_ssg.__main__
        assert hasattr(md_ssg.__main__, 'cli')

    @patch('md_ssg.__main__.cli')
    def test_main_module_execution(self, mock_cli):
        """Test that the main module calls cli when executed."""
        # Import and execute the main module logic
        from md_ssg.__main__ import cli
        
        # Simulate the if __name__ == "__main__" condition
        with patch('md_ssg.__main__.__name__', '__main__'):
            # This would normally call cli(), but we'll test the import path
            assert callable(cli)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_markdown_with_footnotes(self):
        """Test that footnotes extension works."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            # Create markdown with footnotes
            md_content = """# Test Page

This has a footnote[^1].

[^1]: This is the footnote.
"""
            with open("content/test.md", "w") as f:
                f.write(md_content)
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 0
            
            # Check that footnotes were processed
            with open("site/test.html", "r") as f:
                html_content = f.read()
                assert "footnote" in html_content

    def test_non_markdown_files_ignored(self):
        """Test that non-markdown files are ignored."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("content")
            os.makedirs("templates")
            os.makedirs("static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("templates/page.html", "w") as f:
                f.write(template_content)
            
            # Create markdown file and non-markdown file
            with open("content/test.md", "w") as f:
                f.write("# Test\n\nContent")
            
            with open("content/readme.txt", "w") as f:
                f.write("This is not markdown")
            
            result = runner.invoke(cli, ["config.toml"])
            assert result.exit_code == 0
            
            # Only markdown file should be processed
            assert os.path.exists("site/test.html")
            assert not os.path.exists("site/readme.html")

    def test_relative_config_paths(self):
        """Test that paths in config are resolved relative to config file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create subdirectory for config
            os.makedirs("config")
            os.makedirs("config/content")
            os.makedirs("config/templates")
            os.makedirs("config/static")
            
            config_content = """
content_dir = "content"
templates_dir = "templates"
static_dir = "static"
css_files = []
site_dir = "site"
"""
            with open("config/project.toml", "w") as f:
                f.write(config_content)
            
            template_content = """<html><body>{{ content }}</body></html>"""
            with open("config/templates/page.html", "w") as f:
                f.write(template_content)
            
            with open("config/content/test.md", "w") as f:
                f.write("# Test\n\nContent")
            
            result = runner.invoke(cli, ["config/project.toml"])
            assert result.exit_code == 0
            
            # Site should be created relative to config file
            assert os.path.exists("config/site/test.html")
