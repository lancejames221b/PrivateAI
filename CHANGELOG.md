# Changelog

All notable changes to the Private AI project will be documented in this file.

## [1.0.0] - 2025-04-04

### Added
- Initial release of Private AI - AI Tools Privacy Plugin
- Plugin architecture for intercepting and transforming sensitive information in AI tool traffic
- Support for multiple AI services including GitHub Copilot, OpenAI, Anthropic, Amazon CodeWhisperer, Tabnine, Sourcegraph, Codeium, Cursor, Replit, Kite, and JetBrains
- PII detection using transformer models and pattern matching
- Privacy transformation that replaces sensitive information with innocuous placeholders
- Traffic analysis with detailed metrics on what was protected
- VS Code integration with certificate management and proxy configuration
- Command-line interface with launch, analyze, and test commands
- Comprehensive documentation and examples
- Test suite with sample PII data for verification

### Changed
- Expanded scope from GitHub Copilot-only to all AI-powered development tools
- Improved certificate management for better security
- Enhanced error handling and logging
- Streamlined plugin configuration

### Fixed
- Certificate installation issues on different operating systems
- Proxy connection handling for better reliability
- PII detection accuracy with improved transformer models
- Response format adaptation for various AI services

## Author
Lance James, Unit 221B