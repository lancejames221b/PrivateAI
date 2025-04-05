import os
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
import traceback
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_basicauth import BasicAuth
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, URL, Optional
from dotenv import load_dotenv
import socket
import time
import platform
import re

# Import production enhancements if available
try:
    from flask_talisman import Talisman
    from flask_compress import Compress
    from flask_caching import Cache
    from prometheus_flask_exporter import PrometheusMetrics
    PRODUCTION_ENHANCEMENTS_AVAILABLE = True
except ImportError:
    PRODUCTION_ENHANCEMENTS_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("admin_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai-security-proxy-admin")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
csrf = CSRFProtect(app)

# Apply production enhancements if available and in production mode
if PRODUCTION_ENHANCEMENTS_AVAILABLE and os.environ.get('FLASK_ENV') == 'production':
    # Enable security headers
    talisman = Talisman(
        app,
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
            'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
            'img-src': ["'self'", "data:"],
            'font-src': ["'self'", "cdn.jsdelivr.net"]
        },
        force_https=False  # Set to True in actual production
    )
    
    # Enable compression
    compress = Compress(app)
    
    # Enable caching
    cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})
    
    # Enable metrics
    metrics = PrometheusMetrics(app)
    
    logger.info("Production enhancements enabled")
else:
    logger.info("Running without production enhancements")

# Configure Basic Authentication
basic_auth_enabled = os.environ.get('BASIC_AUTH_ENABLED', 'true').lower() == 'true'
if basic_auth_enabled:
    app.config['BASIC_AUTH_USERNAME'] = os.environ.get('BASIC_AUTH_USERNAME', 'admin')
    app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('BASIC_AUTH_PASSWORD', 'change_this_password')
    app.config['BASIC_AUTH_FORCE'] = True
    basic_auth = BasicAuth(app)
    logger.info("Basic authentication is enabled")
else:
    logger.warning("Basic authentication is disabled. This is not recommended for production use.")

# Database connection with error handling
def get_db_connection():
    try:
        conn = sqlite3.connect('data/mapping_store.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

# Form for adding custom patterns
class PatternForm(FlaskForm):
    name = StringField('Pattern Name', validators=[DataRequired()])
    entity_type = SelectField('Entity Type', choices=[
        ('GENERIC', 'Generic Pattern'),
        ('DOMAIN', 'Domain Names'),
        ('API_KEY', 'API Keys'),
        ('EMAIL', 'Email Addresses'),
        ('IP_ADDRESS', 'IP Addresses'),
        ('CREDIT_CARD', 'Credit Card Numbers'),
        ('PII', 'Personal Identifiable Information'),
        ('CODE', 'Code Snippets'),
        ('CREDENTIAL', 'Credentials'),
        ('SECURITYDATA', 'Security Data'),
        ('INTERNAL_PROJECT_NAME', 'Internal Project Names'),
        ('SERVER_PATH', 'Server Paths'),
        ('INTERNAL_IP_RANGE', 'Internal IP Ranges'),
        ('DB_CONNECTION_STRING', 'Database Connection Strings'),
        ('CLOUD_RESOURCE', 'Cloud Resources'),
        ('ENV_VARIABLE', 'Environment Variables'),
        ('CUSTOM', 'Custom Entity')
    ])
    pattern = TextAreaField('Regex Pattern', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_active = BooleanField('Active', default=True)
    priority = SelectField('Priority', choices=[
        ('1', 'High - Apply first'),
        ('2', 'Medium - Normal processing'),
        ('3', 'Low - Apply last')
    ], default='2')
    submit = SubmitField('Save Pattern')

# Add a new form class for AI server configuration 
class AIServerForm(FlaskForm):
    name = StringField('Server Name', validators=[DataRequired()])
    provider = SelectField('Provider Type', choices=[
        ('openai', 'OpenAI API'), 
        ('anthropic', 'Anthropic/Claude'), 
        ('google', 'Google AI/Gemini'),
        ('mistral', 'Mistral AI'),
        ('github', 'GitHub Copilot'),
        ('cursor', 'Cursor AI'),
        ('vscode', 'VS Code/Copilot'),
        ('jetbrains', 'JetBrains AI'),
        ('custom', 'Custom Provider')
    ])
    base_url = StringField('API Base URL', validators=[URL(), DataRequired()])
    auth_type = SelectField('Authentication Type', choices=[
        ('api_key', 'API Key in Header'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Authentication'),
        ('none', 'No Authentication')
    ])
    auth_key = StringField('Auth Key/Username', validators=[Optional()])
    auth_value = StringField('Auth Value/Password', validators=[Optional()])
    custom_headers = TextAreaField('Custom Headers (JSON)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Server')

# Add after the AIServerForm class
class AIDomainForm(FlaskForm):
    domain = StringField('Domain', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic/Claude'),
        ('google', 'Google AI'),
        ('ide', 'IDE Integration'),
        ('openrouter', 'OpenRouter'),
        ('open', 'Open Source Models'),
        ('emerging', 'Emerging Providers'),
        ('testing', 'Testing Services'),
        ('other', 'Other Services')
    ])
    description = StringField('Description', validators=[Optional()])
    submit = SubmitField('Add Domain')

# Error handling decorator
def handle_errors(route_function):
    def wrapper(*args, **kwargs):
        try:
            return route_function(*args, **kwargs)
        except sqlite3.Error as e:
            logger.error(f"Database error in {route_function.__name__}: {str(e)}")
            flash(f"Database error: {str(e)}", 'error')
            return redirect(url_for('index'))
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error in {route_function.__name__}: {str(e)}")
            flash(f"Error executing command: {str(e)}", 'error')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Unexpected error in {route_function.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return redirect(url_for('index'))
    wrapper.__name__ = route_function.__name__
    return wrapper

# Routes
@app.route('/')
@handle_errors
def index():
    # Always redirect to one-page interface
    return redirect(url_for('one_page'))

@app.route('/start_proxy', methods=['POST'])
@handle_errors
def start_proxy():
    try:
        # Check if proxy is already running
        if is_proxy_running():
            flash('Proxy is already running', 'info')
            return redirect(url_for('index'))
            
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(current_dir, 'proxy_start.log')
        
        # Run in background with full path and redirect output
        proxy_script = os.path.join(current_dir, 'run_proxy.sh')
        
        if os.path.exists(proxy_script):
            # Make sure the script is executable
            os.chmod(proxy_script, 0o755)
            
            # Run the script with output redirection
            with open(log_path, 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', proxy_script],
                    stdout=log_file,
                    stderr=log_file,
                    cwd=current_dir
                )
                logger.info(f"Started proxy with PID: {process.pid}")
        else:
            # Fallback to direct Python execution
            logger.warning(f"Could not find run_proxy.sh at {proxy_script}, running ai_proxy.py directly")
            with open(log_path, 'w') as log_file:
                subprocess.Popen(
                    ['python3', 'ai_proxy.py'],
                    stdout=log_file,
                    stderr=log_file,
                    cwd=current_dir
                )
                             
        # Wait a moment and verify it's running
        time.sleep(2)  
        if is_proxy_running():
            flash('Proxy server started successfully', 'success')
            logger.info("Proxy server started and responding")
        else:
            flash('Proxy process started but not responding. Check proxy_start.log for details.', 'warning')
            logger.warning("Proxy process started but not responding")
    except Exception as e:
        logger.error(f"Error starting proxy: {str(e)}")
        flash(f'Error starting proxy: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/stop_proxy', methods=['POST'])
@handle_errors
def stop_proxy():
    try:
        # Check if proxy is already stopped
        if not is_proxy_running():
            flash('Proxy is already stopped', 'info')
            return redirect(url_for('index'))
            
        # Kill any existing proxy processes
        try:
            # Find and kill all instances
            subprocess.run(['pkill', '-f', 'mitmdump'], check=False)
            subprocess.run(['pkill', '-f', 'mitmproxy'], check=False)
            subprocess.run(['pkill', '-f', 'ai_proxy.py'], check=False)
            
            # For macOS, try force-killing any stuck processes
            if platform.system() == "Darwin":  # macOS
                subprocess.run(['killall', '-9', 'mitmdump'], check=False)
                subprocess.run(['killall', '-9', 'python3'], check=False)
        except Exception as kill_error:
            logger.error(f"Error while killing processes: {str(kill_error)}")
        
        # Wait and verify it's stopped
        time.sleep(1)
        if not is_proxy_running():
            flash('Proxy server stopped successfully', 'success')
            logger.info("Proxy server stopped")
        else:
            # Try one more aggressive attempt to kill
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run("ps aux | grep -E 'mitm|ai_proxy' | grep -v grep | awk '{print $2}' | xargs kill -9", shell=True, check=False)
                else:
                    subprocess.run("ps aux | grep -E 'mitm|ai_proxy' | grep -v grep | awk '{print $2}' | xargs kill -9", shell=True, check=False)
                time.sleep(1)
                
                if not is_proxy_running():
                    flash('Proxy server stopped successfully (with force)', 'success')
                    logger.info("Proxy server stopped with force kill")
                else:
                    flash('Failed to stop proxy server. Please stop it manually.', 'error')
                    logger.error("Failed to stop proxy server after multiple attempts")
            except Exception as e:
                logger.error(f"Error during force kill: {str(e)}")
                flash('Failed to stop proxy server. Please stop it manually.', 'error')
    except Exception as e:
        logger.error(f"Error stopping proxy: {str(e)}")
        flash(f'Error stopping proxy: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_mapping/<original>')
@handle_errors
def delete_mapping(original):
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM mappings WHERE original = ?', (original,))
        conn.commit()
        conn.close()
        flash('Mapping deleted successfully', 'success')
        logger.info(f"Mapping deleted: {original}")
    except Exception as e:
        logger.error(f"Error deleting mapping: {str(e)}")
        flash(f'Error deleting mapping: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_pattern', methods=['POST'])
@handle_errors
def add_pattern():
    form = PatternForm()
    
    if form.validate_on_submit():
        try:
            pattern_data = {
                "name": form.name.data,
                "entity_type": form.entity_type.data,
                "pattern": form.pattern.data,
                "description": form.description.data,
                "is_active": form.is_active.data,
                "priority": form.priority.data,
                "created_at": datetime.now().isoformat()
            }
            
            patterns = get_custom_patterns()
            patterns[form.name.data] = pattern_data
            save_custom_patterns(patterns)
            
            flash('Pattern added successfully', 'success')
            logger.info(f"Pattern added: {form.name.data}")
        except Exception as e:
            logger.error(f"Error adding pattern: {str(e)}")
            flash(f'Error adding pattern: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_pattern/<name>')
@handle_errors
def delete_pattern(name):
    try:
        patterns = get_custom_patterns()
        if name in patterns:
            del patterns[name]
            save_custom_patterns(patterns)
            flash('Pattern deleted successfully', 'success')
            logger.info(f"Pattern deleted: {name}")
    except Exception as e:
        logger.error(f"Error deleting pattern: {str(e)}")
        flash(f'Error deleting pattern: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/toggle_pattern/<name>')
@handle_errors
def toggle_pattern(name):
    try:
        patterns = get_custom_patterns()
        if name in patterns:
            patterns[name]['is_active'] = not patterns[name]['is_active']
            save_custom_patterns(patterns)
            status = 'activated' if patterns[name]['is_active'] else 'deactivated'
            flash(f'Pattern {status} successfully', 'success')
            logger.info(f"Pattern {status}: {name}")
    except Exception as e:
        logger.error(f"Error toggling pattern: {str(e)}")
        flash(f'Error toggling pattern: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_domain', methods=['POST'])
@handle_errors
def add_domain():
    # Handle domain blocklist updates
    domain = request.form.get('domain', '').strip()
    
    # Load domain blocklist
    blocklist = []
    try:
        if os.path.exists('data/domain_blocklist.txt'):
            with open('data/domain_blocklist.txt', 'r') as f:
                blocklist = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error loading domain blocklist: {str(e)}")
        flash(f'Error loading domain blocklist: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    if domain and domain not in blocklist:
        blocklist.append(domain)
        save_domain_blocklist(blocklist)
        flash(f'Domain {domain} added to blocklist', 'success')
        logger.info(f"Domain added to blocklist: {domain}")
    
    return redirect(url_for('index'))

@app.route('/remove_domain/<domain>')
@handle_errors
def remove_domain(domain):
    # Load domain blocklist
    blocklist = []
    try:
        if os.path.exists('data/domain_blocklist.txt'):
            with open('data/domain_blocklist.txt', 'r') as f:
                blocklist = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error loading domain blocklist: {str(e)}")
        flash(f'Error loading domain blocklist: {str(e)}', 'error')
        return redirect(url_for('index'))
    
    if domain in blocklist:
        blocklist.remove(domain)
        save_domain_blocklist(blocklist)
        flash(f'Domain {domain} removed from blocklist', 'success')
        logger.info(f"Domain removed from blocklist: {domain}")
    
    return redirect(url_for('index'))

@app.route('/toggle_block_all_domains', methods=['POST'])
@handle_errors
def toggle_block_all_domains():
    current_setting = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'
    new_value = not current_setting
    update_env_setting('BLOCK_ALL_DOMAINS', str(new_value).lower())
    flash(f'Block all domains setting updated to: {new_value}', 'success')
    logger.info(f"Block all domains setting updated to: {new_value}")
    return redirect(url_for('index'))

@app.route('/install_cert')
@handle_errors
def install_cert():
    try:
        # Run certificate installation script
        result = subprocess.run(['./setup_certificates.sh'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True,
                             shell=True)
        
        if result.returncode == 0:
            flash('Certificates installed successfully', 'success')
            logger.info("Certificates installed successfully")
        else:
            error_msg = f'Error installing certificates: {result.stderr}'
            flash(error_msg, 'error')
            logger.error(error_msg)
    except Exception as e:
        error_msg = f'Error running certificate installation: {str(e)}'
        flash(error_msg, 'error')
        logger.error(error_msg)
    
    return redirect(url_for('index'))

# API routes
@app.route('/api/stats')
@handle_errors
def api_stats():
    conn = get_db_connection()
    
    # Total mappings
    cursor = conn.execute('SELECT COUNT(*) FROM mappings')
    total_mappings = cursor.fetchone()[0]
    
    # Entity types count
    cursor = conn.execute('SELECT entity_type, COUNT(*) as count FROM mappings GROUP BY entity_type')
    entity_types = {row['entity_type']: row['count'] for row in cursor.fetchall()}
    
    # Get AI Inference stats
    cursor = conn.execute("""
        SELECT COUNT(*) FROM mappings 
        WHERE entity_type IN (
            'INTERNAL_PROJECT_NAME', 'SERVER_PATH', 'INTERNAL_IP_RANGE', 
            'DB_CONNECTION_STRING', 'CLOUD_RESOURCE', 'ENV_VARIABLE'
        )
    """)
    inference_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_mappings': total_mappings,
        'entity_types': entity_types,
        'inference_count': inference_count,
        'proxy_running': is_proxy_running()
    })

# Utility functions
def is_proxy_running():
    """Enhanced check if the proxy is running"""
    try:
        # First check for specific proxy-related processes
        try:
            result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
            output = result.stdout
            
            process_patterns = [
                'mitmdump', 
                'mitmproxy.tools.main', 
                'ai_proxy.py',
                'python.*ai_proxy'
            ]
            
            process_running = False
            for pattern in process_patterns:
                if re.search(pattern, output):
                    process_running = True
                    logger.debug(f"Found running process matching pattern: {pattern}")
                    break
                    
            if not process_running:
                logger.debug("No proxy processes found running")
                return False
            
            # Then check if standard proxy ports are listening
            proxy_ports = [8080, 8000]  # Standard proxy ports to check
            
            # Add configured port from environment if available
            if 'PROXY_PORT' in os.environ:
                try:
                    env_port = int(os.environ.get('PROXY_PORT'))
                    if env_port not in proxy_ports:
                        proxy_ports.append(env_port)
                except (ValueError, TypeError):
                    pass
            
            # Check each potential port
            for port in proxy_ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(0.5)
                        result = s.connect_ex(('localhost', port))
                        if result == 0:  # Port is open
                            logger.debug(f"Proxy port {port} is open and accepting connections")
                            return True
                except Exception as port_error:
                    logger.debug(f"Error checking port {port}: {str(port_error)}")
            
            logger.debug("Proxy processes running but no ports responding")
            return False  # No ports responding
            
        except subprocess.SubprocessError as e:
            logger.error(f"Error checking processes: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in is_proxy_running: {str(e)}")
        return False

def get_custom_patterns():
    try:
        if os.path.exists('data/custom_patterns.json'):
            with open('data/custom_patterns.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading custom patterns: {str(e)}")
    
    return {}

def save_custom_patterns(patterns):
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/custom_patterns.json', 'w') as f:
            json.dump(patterns, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving custom patterns: {str(e)}")
        raise

def save_domain_blocklist(domains):
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/domain_blocklist.txt', 'w') as f:
            for domain in domains:
                f.write(f"{domain}\n")
    except Exception as e:
        logger.error(f"Error saving domain blocklist: {str(e)}")
        raise

def update_env_setting(key, value):
    """Update a setting in the .env file"""
    try:
        # Load current .env
        env_path = '.env'
        env_dict = {}
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        k, v = line.strip().split('=', 1)
                        env_dict[k] = v
        
        # Update setting
        env_dict[key] = value
        
        # Write back
        with open(env_path, 'w') as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")
        
        # Update environment
        os.environ[key] = value
    except Exception as e:
        logger.error(f"Error updating environment setting {key}: {str(e)}")
        raise

# One-page interface route
@app.route('/one-page')
@handle_errors
def one_page():
    """Render the simplified one-page interface that combines all functionality."""
    try:
        # Get proxy status
        proxy_running = is_proxy_running()
        
        # Initialize stats with defaults in case DB operations fail
        total_mappings = 0
        entity_types = []
        patterns = {}
        
        try:
            # Get basic stats with optimized queries
            conn = get_db_connection()
            
            # Use a single query to get all stats
            cursor = conn.execute('''
                SELECT
                    (SELECT COUNT(*) FROM mappings) as total_mappings
            ''')
            result = cursor.fetchone()
            total_mappings = result[0] if result else 0
            
            # Entity types count - limit to top 10 for performance
            cursor = conn.execute('''
                SELECT entity_type, COUNT(*) as count
                FROM mappings
                GROUP BY entity_type
                ORDER BY count DESC
                LIMIT 10
            ''')
            entity_types = cursor.fetchall()
            
            # Get custom patterns
            patterns = get_custom_patterns()
            
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database error in one_page route: {str(e)}")
            flash(f"Database error: {str(e)}", 'error')
        
        # Load AI server configurations
        ai_servers = load_ai_servers()
        
        # Add cache control headers for production
        response = make_response(render_template('one_page.html',
                              proxy_running=proxy_running,
                              total_mappings=total_mappings,
                              entity_types=entity_types,
                              patterns=patterns,
                              ai_servers=ai_servers))
        
        # Set cache control headers if in production
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Cache-Control'] = 'public, max-age=60'
        
        return response
    except Exception as e:
        logger.error(f"Unexpected error in one_page route: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('one_page.html',
                              proxy_running=False,
                              total_mappings=0,
                              entity_types=[],
                              patterns={},
                              ai_servers=[],
                              error=str(e))

# API endpoint for processing text in the one-page interface
@app.route('/api/process-text', methods=['POST'])
@handle_errors
def process_text():
    """Process text through the privacy filters and return the result."""
    try:
        # Validate input
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        text = request.json.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Get active patterns
        patterns = get_custom_patterns()
        active_patterns = {k: v for k, v in patterns.items() if v.get('is_active', True)}
        
        # This is a simplified version - in production, this would call the actual privacy filtering logic
        processed_text = text
        
        # Apply patterns in order of priority
        for pattern_name, pattern_data in sorted(active_patterns.items(),
                                               key=lambda x: int(x[1].get('priority', 2))):
            try:
                pattern_regex = pattern_data.get('pattern', '')
                if pattern_regex:
                    replacement = f"[{pattern_data.get('entity_type', 'ENTITY')}]"
                    processed_text = re.sub(pattern_regex, replacement, processed_text)
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern_name}")
                continue
        
        # Apply default patterns
        processed_text = re.sub(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_ADDRESS]', processed_text)
        processed_text = re.sub(r'sk_test_[a-zA-Z0-9]+', '[API_KEY]', processed_text)
        processed_text = re.sub(r'Acme Corp', '[ORGANIZATION]', processed_text)
        
        # Count entities found
        entities_found = len(re.findall(r'\[.*?\]', processed_text))
        
        # Add to response headers for security
        response = jsonify({
            'processed_text': processed_text,
            'entities_found': entities_found
        })
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        return response
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e)
        }), 500

# Add this route to handle AI server configuration
@app.route('/ai_servers', methods=['GET'])
@handle_errors
def ai_servers():
    """List all configured AI servers"""
    servers = load_ai_servers()
    return render_template('ai_servers.html', servers=servers)

@app.route('/ai_servers/add', methods=['GET', 'POST'])
@handle_errors
def add_ai_server():
    """Add a new AI server configuration"""
    form = AIServerForm()
    
    if form.validate_on_submit():
        server = {
            'name': form.name.data,
            'provider': form.provider.data,
            'base_url': form.base_url.data,
            'auth_type': form.auth_type.data,
            'auth_key': form.auth_key.data,
            'auth_value': form.auth_value.data,
            'custom_headers': form.custom_headers.data,
            'is_active': form.is_active.data,
            'created_at': datetime.now().isoformat()
        }
        
        servers = load_ai_servers()
        servers.append(server)
        save_ai_servers(servers)
        
        flash(f'AI server "{form.name.data}" added successfully!', 'success')
        return redirect(url_for('ai_servers'))
        
    return render_template('add_ai_server.html', form=form)

@app.route('/ai_servers/edit/<server_name>', methods=['GET', 'POST'])
@handle_errors
def edit_ai_server(server_name):
    """Edit an existing AI server configuration"""
    servers = load_ai_servers()
    server = next((s for s in servers if s['name'] == server_name), None)
    
    if not server:
        flash(f'Server "{server_name}" not found', 'error')
        return redirect(url_for('ai_servers'))
    
    form = AIServerForm(obj=server)
    
    if form.validate_on_submit():
        server['name'] = form.name.data
        server['provider'] = form.provider.data
        server['base_url'] = form.base_url.data
        server['auth_type'] = form.auth_type.data
        server['auth_key'] = form.auth_key.data
        server['auth_value'] = form.auth_value.data
        server['custom_headers'] = form.custom_headers.data
        server['is_active'] = form.is_active.data
        server['updated_at'] = datetime.now().isoformat()
        
        save_ai_servers(servers)
        
        flash(f'AI server "{form.name.data}" updated successfully!', 'success')
        return redirect(url_for('ai_servers'))
        
    return render_template('edit_ai_server.html', form=form, server=server)

@app.route('/ai_servers/delete/<server_name>', methods=['POST'])
@handle_errors
def delete_ai_server(server_name):
    """Delete an AI server configuration"""
    servers = load_ai_servers()
    servers = [s for s in servers if s['name'] != server_name]
    save_ai_servers(servers)
    
    flash(f'AI server "{server_name}" deleted successfully!', 'success')
    return redirect(url_for('ai_servers'))

# Helper functions for AI server management
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
            },
            {
                'name': 'GitHub Copilot',
                'provider': 'github',
                'base_url': 'https://api.githubcopilot.com',
                'auth_type': 'bearer',
                'auth_key': 'Authorization',
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
        logger.error(f"Error loading AI servers: {str(e)}")
        return []

def save_ai_servers(servers):
    """Save AI server configurations to JSON file"""
    servers_file = os.path.join('data', 'ai_servers.json')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(servers_file), exist_ok=True)
    
    try:
        with open(servers_file, 'w') as f:
            json.dump(servers, f, indent=2)
        logger.info(f"Saved {len(servers)} AI server configurations")
    except Exception as e:
        logger.error(f"Error saving AI servers: {str(e)}")

# Add new routes for AI domain management
@app.route('/ai_domains', methods=['GET'])
@handle_errors
def ai_domains():
    """List all configured AI domains"""
    domains_data = load_ai_domains()
    form = AIDomainForm()
    return render_template('ai_domains.html', 
                           domains_data=domains_data, 
                           form=form,
                           categories=domains_data.get('categories', {}))

@app.route('/ai_domains/add', methods=['POST'])
@handle_errors
def add_ai_domain():
    """Add a new AI domain"""
    form = AIDomainForm()
    domains_data = load_ai_domains()
    
    if form.validate_on_submit():
        domain = form.domain.data.strip()
        category = form.category.data
        description = form.description.data
        
        # Add domain to the domains list if not already present
        if domain not in domains_data['domains']:
            domains_data['domains'].append(domain)
            
            # Add domain to the appropriate category
            if category not in domains_data['categories']:
                domains_data['categories'][category] = []
                
            if domain not in domains_data['categories'][category]:
                domains_data['categories'][category].append(domain)
                
            # Save updated domains
            save_ai_domains(domains_data)
            flash(f'Domain "{domain}" added successfully!', 'success')
        else:
            flash(f'Domain "{domain}" already exists!', 'warning')
            
    return redirect(url_for('ai_domains'))

@app.route('/ai_domains/delete/<domain>', methods=['POST'])
@handle_errors
def delete_ai_domain(domain):
    """Delete an AI domain"""
    domains_data = load_ai_domains()
    
    # Remove from main domains list
    if domain in domains_data['domains']:
        domains_data['domains'].remove(domain)
        
        # Remove from all categories
        for category in domains_data['categories']:
            if domain in domains_data['categories'][category]:
                domains_data['categories'][category].remove(domain)
                
        # Save updated domains
        save_ai_domains(domains_data)
        flash(f'Domain "{domain}" deleted successfully!', 'success')
    else:
        flash(f'Domain "{domain}" not found!', 'error')
        
    return redirect(url_for('ai_domains'))

@app.route('/ai_domains/category/<category>', methods=['GET'])
@handle_errors
def ai_domains_by_category(category):
    """View domains by category"""
    domains_data = load_ai_domains()
    form = AIDomainForm()
    form.category.data = category
    
    return render_template('ai_domains_category.html',
                          domains_data=domains_data,
                          current_category=category,
                          form=form)

# Add helper functions for loading and saving AI domains
def load_ai_domains():
    """Load AI domain configurations from JSON file"""
    domains_file = os.path.join('data', 'ai_domains.json')
    
    if not os.path.exists(domains_file):
        # Create the file with default domains if it doesn't exist
        return create_default_domain_config()
    
    try:
        with open(domains_file, 'r') as f:
            domains_data = json.load(f)
            logger.info(f"Loaded {len(domains_data.get('domains', []))} AI domains from configuration")
            return domains_data
    except Exception as e:
        logger.error(f"Error loading AI domains: {str(e)}")
        return create_default_domain_config()

def save_ai_domains(domains_data):
    """Save AI domain configurations to JSON file"""
    domains_file = os.path.join('data', 'ai_domains.json')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(domains_file), exist_ok=True)
    
    try:
        with open(domains_file, 'w') as f:
            json.dump(domains_data, f, indent=2)
        logger.info(f"Saved {len(domains_data.get('domains', []))} AI domains to configuration")
        return True
    except Exception as e:
        logger.error(f"Error saving AI domains: {str(e)}")
        return False

def create_default_domain_config():
    """Create a default domain configuration"""
    # Import this function from proxy_intercept to avoid duplication
    from proxy_intercept import create_default_domain_config as proxy_create_default
    
    # Add some basic structure in case the proxy function changes
    default_domains = {
        "domains": [],
        "categories": {}
    }
    
    try:
        domains_file = os.path.join('data', 'ai_domains.json')
        
        # Check if file already exists
        if os.path.exists(domains_file):
            with open(domains_file, 'r') as f:
                return json.load(f)
                
        # Call the proxy function to create the default configuration
        proxy_create_default()
        
        # Read the created file
        if os.path.exists(domains_file):
            with open(domains_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error creating default domain configuration: {str(e)}")
    
    return default_domains

if __name__ == '__main__':
    # Make sure the data directory exists
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 7070))
    
    # Set debug mode based on environment
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Run the app with production settings if not in development
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, use more workers and disable debug
        try:
            from waitress import serve
            logger.info(f"Starting server in PRODUCTION mode on port {port}")
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            logger.warning("Waitress not installed, falling back to Flask's built-in server")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # In development, use Flask's built-in server with debug mode
        logger.info(f"Starting server in DEVELOPMENT mode on port {port}")
        app.run(host='0.0.0.0', port=port, debug=debug_mode)