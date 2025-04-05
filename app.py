import os
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
import html
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
import requests
from logger import get_logger, log_exception

# Import production enhancements if available
try:
    from flask_talisman import Talisman
    from flask_compress import Compress
    from flask_caching import Cache
    from prometheus_flask_exporter import PrometheusMetrics
    PRODUCTION_ENHANCEMENTS_AVAILABLE = True
except ImportError:
    PRODUCTION_ENHANCEMENTS_AVAILABLE = False

# Initialize logger
logger = get_logger("ai-security-proxy-admin", "logs/admin_ui.log")

# Load environment variables
load_dotenv()

# Define default privacy settings if not in environment
default_privacy_settings = {
    'BLOCK_ALL_DOMAINS': 'false',
    'ENABLE_AI_INFERENCE_PROTECTION': 'true',
    'INFERENCE_PROTECTION_LEVEL': 'medium',
    'USE_PRESIDIO': 'true',
    'ENCRYPT_DATABASE': 'true'
}

# Set defaults if not already in environment
for key, default_value in default_privacy_settings.items():
    if key not in os.environ:
        os.environ[key] = default_value
        logger.info(f"Setting default privacy setting: {key}={default_value}")
load_dotenv()

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
            'script-src': ["'self'", "cdn.jsdelivr.net", "'nonce-%(nonce)s'"],
            'style-src': ["'self'", "cdn.jsdelivr.net", "'nonce-%(nonce)s'"],
            'img-src': ["'self'", "data:"],
            'font-src': ["'self'", "cdn.jsdelivr.net"],
            'frame-ancestors': "'none'",  # Prevents clickjacking
            'form-action': "'self'",      # Restricts form submissions
            'base-uri': "'self'",         # Restricts base URI
            'object-src': "'none'"        # Prevents object injection
        },
        force_https=os.environ.get('FLASK_ENV') == 'production',  # Force HTTPS in production
        strict_transport_security=True,   # Enable HSTS
        session_cookie_secure=os.environ.get('FLASK_ENV') == 'production',
        session_cookie_http_only=True,
        feature_policy={
            'geolocation': "'none'",
            'microphone': "'none'",
            'camera': "'none'"
        }
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
    domain = StringField('Domain', validators=[DataRequired()], render_kw={"placeholder": "api.example.com"})
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
    description = StringField('Description', validators=[Optional()],
                             render_kw={"placeholder": "Brief description of this domain"})
    submit = SubmitField('Add Domain')
    
    def validate_domain(self, field):
        # Remove any http:// or https:// prefixes
        if field.data.startswith(('http://', 'https://')):
            field.data = field.data.split('://', 1)[1]
        
        # Remove any trailing paths
        if '/' in field.data:
            field.data = field.data.split('/', 1)[0]

# Error handling decorator
def handle_errors(route_function):
    def wrapper(*args, **kwargs):
        try:
            return route_function(*args, **kwargs)
        except sqlite3.Error as e:
            log_exception(logger, e, f"Database operation in {route_function.__name__}")
            flash(f"Database error: {str(e)}", 'error')
            flash("The application encountered a database error. Please check the logs for details.", 'warning')
            return redirect(url_for('index'))
        except subprocess.SubprocessError as e:
            log_exception(logger, e, f"Subprocess in {route_function.__name__}")
            flash(f"Error executing command: {str(e)}", 'error')
            flash("The system failed to execute a command. Please check the logs for details.", 'warning')
            return redirect(url_for('index'))
        except Exception as e:
            log_exception(logger, e, f"Unexpected error in {route_function.__name__}")
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            flash("The application encountered an unexpected error. Please check the logs for details.", 'warning')
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
        log_exception(logger, e, "start_proxy")
        flash(f'Error starting proxy: {str(e)}', 'error')
        flash('Check the logs for more details on the proxy startup failure.', 'warning')
    
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
            log_exception(logger, kill_error, "stop_proxy - killing processes")
            flash('Error while attempting to kill proxy processes. Some processes may still be running.', 'warning')
        
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
                log_exception(logger, e, "stop_proxy - force kill")
                flash('Failed to stop proxy server. Please stop it manually.', 'error')
                flash('Check the logs for more details on the proxy stop failure.', 'warning')
    except Exception as e:
        log_exception(logger, e, "stop_proxy")
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
    # Sanitize domain input to prevent XSS
    domain = re.sub(r'[^a-zA-Z0-9.-]', '', domain)
    
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
        flash(f'Domain {html.escape(domain)} added to blocklist', 'success')
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

@app.route('/install_cert', methods=['GET', 'POST'])
@csrf.exempt  # Exempt this route from CSRF protection
@handle_errors
def install_cert():
    """DEPRECATED: Install mitmproxy certificates via script (Unreliable due to sudo).
       Use /download_cert instead for manual installation.
    """
    # --- Deprecated Script Execution Logic --- #
    # This logic is kept for reference but is prone to timeouts due to sudo prompts.
    # The primary method is now manual installation via /download_cert.
    logger.warning("The /install_cert route is deprecated and may be unreliable. Use /download_cert.")
    # Return a message indicating deprecation for POST requests (AJAX)
    if request.method == 'POST':
        return jsonify({
            'success': False,
            'message': 'Deprecated: Certificate installation via script is unreliable.',
            'details': 'Please use the Download Certificate button and follow manual instructions.'
        }), 410 # 410 Gone

    # For GET requests, redirect to the main page with a flash message
    flash('The automatic certificate installation is deprecated. Please use the \'Install Certificate\' button for manual download and instructions.', 'warning')
    return redirect(url_for('one_page'))
    # --- End of Deprecated Logic --- #

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
    
    # Calculate protection rate (percentage of successful transformations)
    protection_rate = 0
    if total_mappings > 0:
        # Assuming all mappings are successful transformations
        protection_rate = 100
    
    return jsonify({
        'total_mappings': total_mappings,
        'entity_types': entity_types,
        'inference_count': inference_count,
        'proxy_running': is_proxy_running(),
        'replacements': total_mappings,
        'blocked': inference_count,
        'protection_rate': protection_rate
    })

# Utility functions
def is_proxy_running():
    """Enhanced check if the proxy is running"""
    try:
        # Check if we're running in Docker
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        
        # If in Docker, check for the proxy service differently
        if in_docker:
            logger.debug("Running in Docker environment, checking for proxy service")
            # In Docker, we primarily check if the proxy port is accessible
            proxy_host = os.environ.get('PROXY_HOST', 'proxy')  # Docker service name from env var
            proxy_port = int(os.environ.get('PROXY_PORT', 8080))
            
            logger.debug(f"Checking Docker proxy at {proxy_host}:{proxy_port}")
            
            try:
                # Try to connect to the proxy service
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    result = s.connect_ex((proxy_host, proxy_port))
                    if result == 0:  # Port is open
                        logger.debug(f"Docker proxy service is available on {proxy_host}:{proxy_port}")
                        return True
                    else:
                        # Fallback to localhost check
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                            s2.settimeout(1.0)
                            result = s2.connect_ex(('localhost', proxy_port))
                            if result == 0:
                                logger.debug(f"Proxy available on localhost:{proxy_port}")
                                return True
            except Exception as docker_error:
                log_exception(logger, docker_error, "is_proxy_running - Docker check")
                logger.debug("Continuing with standard process checks as fallback")
                # Continue with standard checks as fallback
        
        # Standard process check for non-Docker environments
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
            log_exception(logger, e, "is_proxy_running - process check")
            logger.error("Unable to check for running proxy processes")
            return False
            
    except Exception as e:
        log_exception(logger, e, "is_proxy_running")
        logger.error("Critical error in proxy status check")
        return False

# Make is_proxy_running available to templates
app.jinja_env.globals.update(is_proxy_running=is_proxy_running)

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
        
        # Create .env file if it doesn't exist
        if not os.path.exists(env_path):
            logger.info(f"Creating new .env file at {env_path}")
            # Copy from example if available
            if os.path.exists('.env.example'):
                with open('.env.example', 'r') as example_file:
                    with open(env_path, 'w') as env_file:
                        env_file.write(example_file.read())
                logger.info("Created .env file from .env.example")
        
        # Load current settings
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        # More secure parsing of environment variables
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            k, v = parts
                        env_dict[k] = v
        
        # Update setting
        env_dict[key] = value
        logger.info(f"Updating environment setting: {key}={value}")
        
        # Write back
        # Write back with secure handling
        with open(env_path, 'w') as f:
            for k, v in env_dict.items():
                # Validate key and value to prevent injection
                if re.match(r'^[A-Za-z0-9_]+$', k) and '\n' not in v:
                f.write(f"{k}={v}\n")
                else:
                    logger.warning(f"Skipping invalid environment variable: {k}")
        
        # Update environment
        os.environ[key] = value
        
        # Log the change
        logger.info(f"Environment setting updated: {key}={value}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating environment setting {key}: {str(e)}")
        logger.error(traceback.format_exc())
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
        
        # Get stats for the protection summary
        stats = {
            'replacements': 0,
            'blocked': 0,
            'protection_rate': '0%'
        }
        
        try:
            # Try to get stats from the API
            response = requests.get('http://localhost:8080/api/stats', timeout=1)
            if response.status_code == 200:
                api_stats = response.json()
                stats['replacements'] = api_stats.get('replacements', 0)
                stats['blocked'] = api_stats.get('blocked', 0)
                stats['protection_rate'] = f"{api_stats.get('protection_rate', 0)}%"
        except Exception as stats_error:
            logger.warning(f"Could not fetch stats: {str(stats_error)}")
        
        # Add cache control headers for production
        response = make_response(render_template('one_page.html',
                              proxy_running=proxy_running,
                              total_mappings=total_mappings,
                              entity_types=entity_types,
                              patterns=patterns,
                              ai_servers=ai_servers,
                              stats=stats))
        
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
                              stats={
                                  'replacements': 0,
                                  'blocked': 0,
                                  'protection_rate': '0%'
                              },
                              error=str(e))

# API endpoint for processing text in the one-page interface
@app.route('/api/process-text', methods=['POST'])
@handle_errors
@csrf.exempt  # Explicitly mark as CSRF exempt since it's an API endpoint
def process_text():
    """Process text through the privacy filters and return the result."""
    try:
        # Validate input
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        # Rate limiting check
        client_ip = request.remote_addr
        current_time = datetime.now()
        rate_limit_key = f"rate_limit:{client_ip}"
        
        # Simple in-memory rate limiting (could be replaced with Redis in production)
        if hasattr(app, 'rate_limit_store') and rate_limit_key in app.rate_limit_store:
            last_request_time, count = app.rate_limit_store[rate_limit_key]
            if (current_time - last_request_time).total_seconds() < 60:  # 1 minute window
                if count >= 30:  # Max 30 requests per minute
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                app.rate_limit_store[rate_limit_key] = (last_request_time, count + 1)
            else:
                # Reset if window expired
                app.rate_limit_store[rate_limit_key] = (current_time, 1)
        else:
            # Initialize rate limiting store if needed
            if not hasattr(app, 'rate_limit_store'):
                app.rate_limit_store = {}
            app.rate_limit_store[rate_limit_key] = (current_time, 1)
            
        text = request.json.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        # Limit input size to prevent DoS
        if len(text) > 100000:  # 100KB limit
            return jsonify({'error': 'Text too large. Maximum size is 100KB'}), 413
            
        # Import the PII transformation logic
        from pii_transform import detect_and_transform
        
        # Process the text using the actual PII transformation logic
        processed_text, transformations_log = detect_and_transform(text)
        
        # Count entities found based on the transformations log
        entities_found = len(transformations_log)
        
        # Add to response headers for security
        response = jsonify({
            'processed_text': processed_text,
            'entities_found': entities_found,
            'transformations': transformations_log
        })
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        
        return response
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': html.escape(str(e))
        }), 500

# Add this route to handle AI server configuration
@app.route('/ai_servers', methods=['GET'])
@handle_errors
def ai_servers():
    """List all configured AI servers"""
    servers = load_ai_servers()
    return render_template('ai_servers_standalone.html', servers=servers)

@app.route('/ai_servers_direct', methods=['GET'])
@handle_errors
def ai_servers_direct():
    """Direct access to AI server management without template inheritance"""
    servers = load_ai_servers()
    return render_template('ai_servers_standalone.html', servers=servers)

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
        
    return render_template('add_ai_server_standalone.html', form=form)

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
        
    return render_template('edit_ai_server_standalone.html', form=form, server=server)

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
            
            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'Domain "{domain}" added successfully!'
                })
            
            flash(f'Domain "{domain}" added successfully!', 'success')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'Domain "{domain}" already exists!'
                })
            
            flash(f'Domain "{domain}" already exists!', 'warning')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'Form validation failed',
                'errors': form.errors
            }), 400
            
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
        
        # If this is an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Domain "{domain}" deleted successfully!'
            })
            
        flash(f'Domain "{domain}" deleted successfully!', 'success')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'Domain "{domain}" not found!'
            }), 404
            
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

@app.route('/ai_domains/save', methods=['POST'])
@handle_errors
def save_ai_domains_changes():
    """Save all domain changes and update the proxy configuration"""
    try:
        domains_data = load_ai_domains()
        
        # Save the domains data
        success = save_ai_domains(domains_data)
        
        # Update the proxy's domain list
        # This will be picked up by the proxy on its next request
        from proxy_intercept import load_ai_servers
        load_ai_servers()
        
        if success:
            logger.info("Domain changes saved successfully")
            return jsonify({"success": True, "message": "Domain changes saved successfully"})
        else:
            logger.error("Failed to save domain changes")
            return jsonify({"success": False, "message": "Failed to save domain changes"}), 500
    except Exception as e:
        logger.error(f"Error saving domain changes: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

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

@app.route('/api/connection-settings', methods=['GET'])
def get_connection_settings():
    """Return the current connection settings for the proxy"""
    try:
        # In a real implementation, this would fetch the actual settings
        # For now, we'll return some default values
        settings = {
            "proxy_port": 8080,
            "ai_endpoints": [
                {"name": "OpenAI", "url": "https://api.openai.com/v1/chat/completions"},
                {"name": "Anthropic", "url": "https://api.anthropic.com/v1/messages"},
                {"name": "Google", "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"},
                {"name": "Mistral", "url": "https://api.mistral.ai/v1/chat/completions"}
            ]
        }
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting connection settings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test_proxy_connection', methods=['POST'])
@csrf.exempt  # Exempt this route from CSRF protection
def test_proxy_connection():
    """Test if the proxy is running and properly configured"""
    try:
        data = request.get_json()
        proxy_port = data.get('proxy_port', 8080)
        
        # Check if we're running in Docker
        in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'
        
        if in_docker:
            # In Docker, use the service name from environment
            proxy_host = os.environ.get('PROXY_HOST', 'proxy')
            logger.debug(f"Testing Docker proxy connection to {proxy_host}:{proxy_port}")
        else:
            # Not in Docker, use localhost
            proxy_host = '127.0.0.1'
            logger.debug(f"Testing local proxy connection to {proxy_host}:{proxy_port}")
        
        # First, check if the proxy port is open and responding
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((proxy_host, int(proxy_port)))
        sock.close()
        
        if result != 0:
            return jsonify({
                'success': False,
                'message': f'Proxy is not running on {proxy_host}:{proxy_port}. Please start the proxy service first.'
            })
        
        # Now check if we can make a simple request through the proxy
        try:
            # This uses Python's socket to test a simple connection
            # We'll try to connect to a known endpoint via the proxy
            # Note: We're reusing the proxy_host from above, which is already Docker-aware
            logger.debug(f"Testing HTTP request through proxy at {proxy_host}:{proxy_port}")
            
            # Create and configure the socket for testing
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # 5 second timeout
            
            # Try connecting to the proxy
            s.connect((proxy_host, int(proxy_port)))
            
            # Send a simple HTTP request through the proxy to a test domain
            test_request = (
                f"GET http://httpbin.org/status/200 HTTP/1.1\r\n"
                f"Host: httpbin.org\r\n"
                f"Connection: close\r\n\r\n"
            )
            s.sendall(test_request.encode())
            
            # Get response
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            
            s.close()
            
            # Check if we got a successful response
            if b"200 OK" in response:
                return jsonify({
                    'success': True,
                    'message': f'Proxy connection successful on port {proxy_port}. The proxy is operational.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Proxy is running on port {proxy_port}, but returned an unexpected response. Check proxy configuration.'
                })
        
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Proxy is running on port {proxy_port}, but could not process requests: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f"Proxy connection test error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error testing proxy connection: {str(e)}'
        }), 500

@app.route('/download_cert')
def download_cert():
    """Provides the mitmproxy CA certificate for download."""
    try:
        # Standard mitmproxy certificate location
        cert_path_home = os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem")
        # Fallback location within the project data directory
        cert_path_data = os.path.abspath("data/mitmproxy-ca-cert.pem")

        cert_path = None
        if os.path.exists(cert_path_home):
            cert_path = cert_path_home
        elif os.path.exists(cert_path_data):
            cert_path = cert_path_data
        else:
             # If cert doesn't exist, try to generate it using the setup script
            logger.warning("Certificate not found, attempting to generate...")
            setup_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'deployment', 'setup_certificates.sh')
            if os.path.exists(setup_script_path):
                try:
                    # Run script without sudo first
                    subprocess.run([setup_script_path], check=True, timeout=10, capture_output=True, text=True)
                    logger.info("Certificate generated successfully by script.")
                    # Re-check for the cert path
                    if os.path.exists(cert_path_home):
                        cert_path = cert_path_home
                    elif os.path.exists(cert_path_data):
                        cert_path = cert_path_data
                except Exception as script_e:
                    logger.error(f"Failed to generate certificate using script: {script_e}")
            
            if not cert_path:
                 logger.error(f"mitmproxy CA certificate not found at {cert_path_home} or {cert_path_data} and generation failed.")
                 return "Certificate file not found. Please ensure mitmproxy has run at least once or run setup_certificates.sh manually.", 404

        logger.info(f"Serving certificate file from: {cert_path}")
        return send_file(cert_path, as_attachment=True, download_name='mitmproxy-ca-cert.pem')

    except Exception as e:
        logger.error(f"Error serving certificate file: {str(e)}")
        logger.error(traceback.format_exc())
        return "Error serving certificate file.", 500

# Patterns route
@app.route('/patterns')
@handle_errors
def patterns():
    """Render the patterns management page"""
    try:
        # Get custom patterns
        patterns = get_custom_patterns()
        
        # Create a new pattern form
        form = PatternForm()
        
        return render_template('patterns.html',
                              patterns=patterns,
                              form=form)
    except Exception as e:
        logger.error(f"Error in patterns route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading patterns: {str(e)}", 'error')
        return render_template('patterns.html',
                              patterns={},
                              form=PatternForm())

# Mappings route
@app.route('/mappings')
@handle_errors
def mappings():
    """Render the mappings management page"""
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Get mappings with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        # Get total count
        cursor = conn.execute('SELECT COUNT(*) FROM mappings')
        total_mappings = cursor.fetchone()[0]
        
        # Get mappings for current page
        cursor = conn.execute('''
            SELECT original, replacement, entity_type, created_at
            FROM mappings
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        mappings_list = cursor.fetchall()
        
        # Calculate total pages
        total_pages = (total_mappings + per_page - 1) // per_page
        
        conn.close()
        
        return render_template('mappings.html',
                              mappings=mappings_list,
                              page=page,
                              per_page=per_page,
                              total_pages=total_pages,
                              total_mappings=total_mappings)
    except Exception as e:
        logger.error(f"Error in mappings route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading mappings: {str(e)}", 'error')
        return render_template('mappings.html',
                              mappings=[],
                              page=1,
                              per_page=20,
                              total_pages=1,
                              total_mappings=0)

# Domains route
@app.route('/domains')
@handle_errors
def domains():
    """Render the domains management page"""
    try:
        # Load domain blocklist
        blocklist = []
        if os.path.exists('data/domain_blocklist.txt'):
            with open('data/domain_blocklist.txt', 'r') as f:
                blocklist = [line.strip() for line in f if line.strip()]
        
        # Get block all domains setting
        block_all_domains = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'
        
        return render_template('domains.html',
                              domains=blocklist,
                              block_all_domains=block_all_domains)
    except Exception as e:
        logger.error(f"Error in domains route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading domains: {str(e)}", 'error')
        return render_template('domains.html',
                              domains=[],
                              block_all_domains=False)

# Setup route
@app.route('/setup')
@handle_errors
def setup():
    """Render the setup page"""
    try:
        # Get proxy status
        proxy_running = is_proxy_running()
        
        # Get certificate status
        cert_path = os.path.expanduser('~/.mitmproxy/mitmproxy-ca-cert.pem')
        cert_exists = os.path.exists(cert_path)
        
        return render_template('setup.html',
                              proxy_running=proxy_running,
                              cert_exists=cert_exists,
                              cert_path=cert_path)
    except Exception as e:
        logger.error(f"Error in setup route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading setup page: {str(e)}", 'error')
        return render_template('setup.html',
                              proxy_running=False,
                              cert_exists=False,
                              cert_path='')

# Logs route
@app.route('/logs')
@handle_errors
def logs():
    """Render the logs page"""
    try:
        # Get log files
        log_files = ['proxy.log', 'admin_ui.log']
        selected_log = request.args.get('log', 'proxy.log')
        
        # Read selected log file
        log_content = []
        if selected_log in log_files and os.path.exists(selected_log):
            with open(selected_log, 'r') as f:
                log_content = f.read().splitlines()
                # Get the last 100 lines
                log_content = log_content[-100:]
        
        return render_template('logs.html',
                              log_files=log_files,
                              selected_log=selected_log,
                              log_content=log_content)
    except Exception as e:
        logger.error(f"Error in logs route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading logs: {str(e)}", 'error')
        return render_template('logs.html',
                              log_files=[],
                              selected_log='',
                              log_content=[])

# Security check route
@app.route('/security_check')
@handle_errors
def security_check():
    """Render the security check page"""
    try:
        # Perform basic security checks
        security_checks = [
            {
                'name': 'Basic Authentication',
                'status': 'Enabled' if os.environ.get('BASIC_AUTH_ENABLED', 'true').lower() == 'true' else 'Disabled',
                'passed': os.environ.get('BASIC_AUTH_ENABLED', 'true').lower() == 'true',
                'description': 'Basic authentication protects the admin interface from unauthorized access.'
            },
            {
                'name': 'Default Password Changed',
                'status': 'Changed' if os.environ.get('BASIC_AUTH_PASSWORD') != 'change_this_password' else 'Default',
                'passed': os.environ.get('BASIC_AUTH_PASSWORD') != 'change_this_password',
                'description': 'The default admin password should be changed for security.'
            },
            {
                'name': 'Database Encryption',
                'status': 'Enabled' if os.environ.get('ENCRYPT_DATABASE', 'true').lower() == 'true' else 'Disabled',
                'passed': os.environ.get('ENCRYPT_DATABASE', 'true').lower() == 'true',
                'description': 'Database encryption protects sensitive mapping data.'
            },
            {
                'name': 'AI Inference Protection',
                'status': 'Enabled' if os.environ.get('ENABLE_AI_INFERENCE_PROTECTION', 'true').lower() == 'true' else 'Disabled',
                'passed': os.environ.get('ENABLE_AI_INFERENCE_PROTECTION', 'true').lower() == 'true',
                'description': 'AI inference protection prevents AI models from inferring sensitive information.'
            }
        ]
        
        # Calculate overall security score
        passed_checks = sum(1 for check in security_checks if check['passed'])
        total_checks = len(security_checks)
        security_score = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
        
        return render_template('security_check.html',
                              security_checks=security_checks,
                              security_score=security_score)
    except Exception as e:
        logger.error(f"Error in security_check route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error performing security check: {str(e)}", 'error')
        return render_template('security_check.html',
                              security_checks=[],
                              security_score=0)

# Privacy Control Panel route
@app.route('/privacy_control')
@handle_errors
def privacy_control():
    """Render the privacy control panel with current settings"""
    try:
        # Get current privacy settings from .env
        privacy_settings = {
            'block_all_domains': os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true',
            'enable_ai_inference_protection': os.environ.get('ENABLE_AI_INFERENCE_PROTECTION', 'true').lower() == 'true',
            'inference_protection_level': os.environ.get('INFERENCE_PROTECTION_LEVEL', 'medium'),
            'use_presidio': os.environ.get('USE_PRESIDIO', 'true').lower() == 'true',
            'encrypt_database': os.environ.get('ENCRYPT_DATABASE', 'true').lower() == 'true'
        }
        
        # Get database stats for the panel
        conn = get_db_connection()
        
        # Get total entities detected
        cursor = conn.execute('SELECT COUNT(*) FROM mappings')
        total_entities = cursor.fetchone()[0]
        
        # Get entity types for status indicators
        cursor = conn.execute('SELECT entity_type, COUNT(*) as count FROM mappings GROUP BY entity_type')
        entity_counts = {row['entity_type']: row['count'] for row in cursor.fetchall()}
        
        # Get recent transformations
        cursor = conn.execute('''
            SELECT original, replacement, entity_type, created_at
            FROM mappings
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        recent_transformations = cursor.fetchall()
        
        conn.close()
        
        return render_template('privacy_control.html',
                              privacy_settings=privacy_settings,
                              total_entities=total_entities,
                              entity_counts=entity_counts,
                              recent_transformations=recent_transformations)
    except Exception as e:
        logger.error(f"Error in privacy_control route: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Error loading privacy settings: {str(e)}", 'error')
        return render_template('privacy_control.html',
                              privacy_settings={},
                              total_entities=0,
                              entity_counts={},
                              recent_transformations=[])

# API endpoint to update privacy settings
@app.route('/api/update_privacy_settings', methods=['POST'])
@handle_errors
def update_privacy_settings():
    """Update privacy settings in .env file"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        settings = request.json
        
        # Update each setting in .env
        if 'block_all_domains' in settings:
            update_env_setting('BLOCK_ALL_DOMAINS', str(settings['block_all_domains']).lower())
            
        if 'enable_ai_inference_protection' in settings:
            update_env_setting('ENABLE_AI_INFERENCE_PROTECTION', str(settings['enable_ai_inference_protection']).lower())
            
        if 'inference_protection_level' in settings:
            update_env_setting('INFERENCE_PROTECTION_LEVEL', settings['inference_protection_level'])
            
        if 'use_presidio' in settings:
            update_env_setting('USE_PRESIDIO', str(settings['use_presidio']).lower())
            
        if 'encrypt_database' in settings:
            update_env_setting('ENCRYPT_DATABASE', str(settings['encrypt_database']).lower())
        
        logger.info(f"Privacy settings updated: {settings}")
        
        return jsonify({
            'success': True,
            'message': 'Privacy settings updated successfully',
            'settings': settings
        })
    except Exception as e:
        logger.error(f"Error updating privacy settings: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': html.escape(str(e))
        }), 500

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