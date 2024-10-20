# md-ssg

[![PyPI](https://img.shields.io/pypi/v/md-ssg.svg)](https://pypi.org/project/md-ssg/)
[![Changelog](https://img.shields.io/github/v/release/RKeelan/md-ssg?include_prereleases&label=changelog)](https://github.com/RKeelan/md-ssg/releases)
[![Tests](https://github.com/RKeelan/md-ssg/actions/workflows/test.yml/badge.svg)](https://github.com/RKeelan/md-ssg/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/RKeelan/md-ssg/blob/master/LICENSE)

Create a static website from markdown files

## Installation

Install this tool using `pip`:
```bash
pip install md-ssg
```
## Usage

For help, run:
```bash
md-ssg --help
```
You can also use:
```bash
python -m md_ssg --help
```
## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd md-ssg
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
