import json
import os
from datetime import datetime

def load_ai_servers():
    """Load AI server configurations from JSON file"""
    servers_file = os.path.join('data', 'ai_servers.json')
    
    if not os.path.exists(servers_file):
        # Create default configurations
        default_servers = [
            {
                'name': 'OpenAI',
                'provider': 'openai',
                'base_url': 'https://api.openai.com',
                'auth_type': 'bearer',
                'auth_key': 'Authorization',
                'auth_value': '',
                'custom_headers': '',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            },
            {
                'name': 'Anthropic',
                'provider': 'anthropic',
                'base_url': 'https://api.anthropic.com',
                'auth_type': 'api_key',
                'auth_key': 'x-api-key',
                'auth_value': '',
                'custom_headers': '',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
        ]
        save_ai_servers(default_servers)
        return default_servers
    
    try:
        with open(servers_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading AI servers: {str(e)}")
        return []

def save_ai_servers(servers):
    """Save AI server configurations to JSON file"""
    servers_file = os.path.join('data', 'ai_servers.json')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(servers_file), exist_ok=True)
    
    try:
        with open(servers_file, 'w') as f:
            json.dump(servers, f, indent=2)
        print(f"Saved {len(servers)} AI server configurations")
        return True
    except Exception as e:
        print(f"Error saving AI servers: {str(e)}")
        return False

def add_ai_server(name, provider, base_url, auth_type, auth_key, auth_value, custom_headers="", is_active=True):
    """Add a new AI server configuration"""
    server = {
        'name': name,
        'provider': provider,
        'base_url': base_url,
        'auth_type': auth_type,
        'auth_key': auth_key,
        'auth_value': auth_value,
        'custom_headers': custom_headers,
        'is_active': is_active,
        'created_at': datetime.now().isoformat()
    }
    
    servers = load_ai_servers()
    
    # Check if server with same name already exists
    if any(s['name'] == name for s in servers):
        print(f"Server with name '{name}' already exists")
        return False
    
    servers.append(server)
    save_ai_servers(servers)
    print(f"Added server: {name}")
    return True

def edit_ai_server(server_name, **kwargs):
    """Edit an existing AI server configuration"""
    servers = load_ai_servers()
    server = next((s for s in servers if s['name'] == server_name), None)
    
    if not server:
        print(f"Server '{server_name}' not found")
        return False
    
    # Update server properties
    for key, value in kwargs.items():
        if key in server:
            server[key] = value
    
    server['updated_at'] = datetime.now().isoformat()
    save_ai_servers(servers)
    print(f"Updated server: {server_name}")
    return True

def delete_ai_server(server_name):
    """Delete an AI server configuration"""
    servers = load_ai_servers()
    initial_count = len(servers)
    servers = [s for s in servers if s['name'] != server_name]
    
    if len(servers) == initial_count:
        print(f"Server '{server_name}' not found")
        return False
    
    save_ai_servers(servers)
    print(f"Deleted server: {server_name}")
    return True

def list_ai_servers():
    """List all AI server configurations"""
    servers = load_ai_servers()
    print(f"Found {len(servers)} AI server configurations:")
    
    for i, server in enumerate(servers, 1):
        status = "Active" if server.get('is_active', True) else "Inactive"
        print(f"{i}. {server['name']} ({server['provider']}) - {server['base_url']} - {status}")
    
    return servers

def test_ai_server_management():
    """Test AI server management functionality"""
    print("=== Testing AI Server Management ===")
    
    # List existing servers
    print("\nListing existing servers:")
    list_ai_servers()
    
    # Add a new server
    print("\nAdding a new server:")
    add_ai_server(
        name="Test Server",
        provider="custom",
        base_url="https://api.example.com",
        auth_type="api_key",
        auth_key="X-API-Key",
        auth_value="test-api-key-123",
        custom_headers='{"X-Custom-Header": "test-value"}',
        is_active=True
    )
    
    # List servers after adding
    print("\nListing servers after adding:")
    list_ai_servers()
    
    # Edit the server
    print("\nEditing the server:")
    edit_ai_server(
        "Test Server",
        base_url="https://api.updated-example.com",
        auth_value="updated-api-key-456",
        is_active=False
    )
    
    # List servers after editing
    print("\nListing servers after editing:")
    list_ai_servers()
    
    # Delete the server
    print("\nDeleting the server:")
    delete_ai_server("Test Server")
    
    # List servers after deleting
    print("\nListing servers after deleting:")
    list_ai_servers()

if __name__ == "__main__":
    test_ai_server_management()