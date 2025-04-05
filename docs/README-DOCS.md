# Documentation Overview

## About these Docs

This documentation is designed to help you understand, set up, and effectively use the AI Privacy Proxy. It provides comprehensive information on all aspects of the system, from quick start guides to advanced configuration options.

## Image Placeholders

Some image files in the `docs/images/` directory are currently placeholders. To complete the documentation, you should create or add the following images:

1. `architecture-overview.png`: High-level overview of the AI Privacy Proxy architecture
2. `system-architecture.png`: Technical diagram of the system components
3. `admin-dashboard.png`: Screenshot of the admin dashboard
4. `mappings-page.png`: Screenshot of the mappings management page
5. `patterns-page.png`: Screenshot of the pattern management page
6. `domains-page.png`: Screenshot of the domain configuration page
7. `logs-page.png`: Screenshot of the logs viewer
8. `setup-page.png`: Screenshot of the setup assistant
9. `security-check.png`: Screenshot of the security check page

## Building Documentation

If you want to build a static documentation site from these Markdown files, you can use a tool like [MkDocs](https://www.mkdocs.org/) or [Docusaurus](https://docusaurus.io/):

### MkDocs Example

1. Install MkDocs:
   ```bash
   pip install mkdocs
   ```

2. Create a configuration file (`mkdocs.yml`) in the project root:
   ```yaml
   site_name: AI Privacy Proxy
   nav:
     - Home: docs/README.md
     - Introduction: docs/introduction.md
     - Quick Start: docs/quickstart.md
     - Docker Setup: docs/docker-setup.md
     - Admin Interface: docs/admin-interface.md
     - Proxy Configuration: docs/proxy-configuration.md
     - Codename Generation: docs/codename-generation.md
     - PII Transformation: docs/pii-transformation.md
     - API Reference: docs/api-reference.md
     - Troubleshooting: docs/troubleshooting.md
   theme: readthedocs
   ```

3. Build the documentation:
   ```bash
   mkdocs build
   ```

4. The built documentation will be in the `site/` directory.

## Contributing to Docs

When contributing to this documentation:

1. Use clear, concise language
2. Include code examples where appropriate
3. Test commands and examples
4. Keep screenshots up to date
5. Maintain the existing structure
6. Update the table of contents when adding new sections