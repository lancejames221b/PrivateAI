# AI Server and Domain Management

Private AI 🕵️ supports configuration of multiple AI servers and domains through the admin interface. This allows the detective to seamlessly work with various AI providers while maintaining privacy protection.

## Managing AI Servers

The AI Server Management interface allows you to:

1. **Add new AI API configurations** - Connect to any AI service provider
2. **Edit existing configurations** - Update connection details as needed
3. **Toggle active status** - Enable or disable specific providers
4. **Configure authentication** - Securely store authentication details

## Server Configuration Fields

Each AI server configuration includes:

| Field | Description |
|-------|-------------|
| Server Name | A unique name to identify this configuration |
| Provider Type | The AI provider format (OpenAI, Anthropic, etc.) |
| API Base URL | The root URL for the AI API |
| Authentication Type | How to authenticate (API Key, Bearer Token, etc.) |
| Auth Key/Header | The header name or username |
| Auth Value | The API key, token, or password value |
| Custom Headers | Optional additional headers in JSON format |
| Active Status | Whether this configuration is currently in use |

## Managing AI Domains

The AI Domain Management interface allows you to:

1. **View domains by category** - Browse domains organized by provider type
2. **Add new domains** - Register new AI service domains for interception
3. **Delete existing domains** - Remove domains that are no longer needed
4. **Manage domain categories** - Organize domains into logical groups

All domains are stored in a JSON configuration file that is automatically loaded by the proxy at startup.

## Domain Categories

Domains are organized into the following categories:

- **OpenAI** - Domains for OpenAI API and Azure OpenAI services
- **Anthropic** - Domains for Claude and other Anthropic services
- **Google AI** - Domains for Google's AI services including Gemini
- **IDE Integration** - Domains for code editor AI assistants (GitHub Copilot, Cursor, etc.)
- **OpenRouter** - Domains for the OpenRouter API gateway
- **Open Source Models** - Domains for open source model providers like Hugging Face
- **Emerging Providers** - Domains for newer AI companies (Mistral, Together, etc.)
- **Testing Services** - Domains used for testing purposes
- **Other Services** - Miscellaneous AI service domains

## Supported Provider Types

Private AI 🕵️ automatically adapts requests and responses to work with different AI formats:

- **OpenAI API** - Standard OpenAI API format
- **Anthropic/Claude** - Claude API format
- **Google AI/Gemini** - Google's Gemini and PaLM models
- **Mistral AI** - Mistral's API format
- **GitHub Copilot** - GitHub Copilot's JSONRPC protocol
- **Cursor AI** - Cursor's specialized format
- **VS Code/Copilot** - VS Code extension format
- **JetBrains AI** - JetBrains IDE integration
- **Custom Provider** - Any other provider with OpenAI-compatible API

## Authentication Types

Multiple authentication methods are supported:

- **API Key in Header** - Standard API key authentication
- **Bearer Token** - OAuth and similar token-based auth
- **Basic Authentication** - Username/password basic auth
- **No Authentication** - For services that don't require auth

## JSON Configuration

Both server configurations and domain lists are stored in JSON files:

- **AI Servers**: `data/ai_servers.json`
- **AI Domains**: `data/ai_domains.json`

These files are automatically created with default values if they don't exist.

## Usage in the Proxy

When the proxy intercepts a request:

1. It checks if the domain matches a domain in the domain list
2. If matched, it looks for a corresponding server configuration
3. If a server configuration is found, it applies the configured authentication
4. It adapts the request format based on the provider type
5. After privacy processing, it adapts the response to match the original format

## Security Considerations

- API keys and authentication tokens are stored in local JSON files
- For production use, consider securing these files with appropriate permissions
- Authentication values are only used to communicate with the configured AI services
- No authentication details are logged or sent to any other services

## Adding a New AI Provider

To add support for a new AI provider:

1. Add the provider's domains to the domain list
2. Add the new provider to the `Provider Type` dropdown in the admin interface
3. Create a server configuration for the provider
4. Update the `detect_and_adapt_ai_format` function in `utils.py` if needed
5. Update the `adapt_ai_response` function if needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Domain not intercepted | Add the domain to the domain list |
| Authentication failing | Verify API key/token is correct and active |
| Format detection not working | Check the request headers and structure |
| Domain not recognized | Make sure the URL matches the configured base URL |
| Custom headers not applied | Verify JSON format in the custom headers field 