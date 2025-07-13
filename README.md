# Genny – Code Documentation Generator

[![codecov](https://codecov.io/github/nemariia/genny/graph/badge.svg?token=UZTPFNJLGW)](https://codecov.io/github/nemariia/genny)

**Genny** is a Python-based tool that automatically generates documentation from your source code using customizable templates. It supports multiple output formats such as Markdown, HTML, YAML, and JSON.

## ✨ Features

- Parses Python code to extract classes, functions, imports, and more
- Customizable templates for flexible documentation styles
- Export to Markdown, HTML, JSON, or YAML
- Integration with git to generate version-specific documentation

## 📦 Installation

Clone the repository:

```
git clone https://github.com/nemariia/genny.git
cd genny
```

Install it as a local package:

```
pip install build
python -m build
pip install .
```

## 📑 Usage

Run this to see the available commands:

```
genny --help
```