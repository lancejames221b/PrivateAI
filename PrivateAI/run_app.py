#!/usr/bin/env python3
"""
Run script for the Private AI Proxy frontend.
Starts the proxy automatically in the background.
"""

import os
import socket
import subprocess
import atexit
import signal
import time
import logging
import platform
from app import app

# Configure logging for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
script_logger = logging.getLogger("run_app")

proxy_process = None

def is_proxy_running_internal():
    """Internal check if proxy process/port seems active."""
    try:
        # Check common proxy ports
        ports_to_check = [8080] 
        if 'PROXY_PORT' in os.environ:
             try:
                 ports_to_check.append(int(os.environ['PROXY_PORT']))
             except ValueError:
                 pass
        
        port_open = False
        for port in set(ports_to_check): # Use set to avoid duplicates
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    if s.connect_ex(('localhost', port)) == 0:
                        port_open = True
                        break
            except Exception:
                continue # Ignore errors checking specific port
        
        if not port_open:
            # Check if process is running even if port check failed
             result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True, check=False)
             output = result.stdout
             if 'mitmdump' in output or 'mitmproxy' in output or 'ai_proxy.py' in output:
                  script_logger.warning("Proxy process found but port check failed.")
                  # Decide if this counts as running - let's say yes for now if process exists
                  return True 
             return False
             
        return port_open
    except Exception as e:
        script_logger.error(f"Error checking proxy status internally: {e}")
        return False

def start_background_proxy():
    """Starts the proxy script (run_proxy.sh or ai_proxy.py) in the background."""
    global proxy_process
    
    if is_proxy_running_internal():
        script_logger.info("Proxy appears to be already running.")
        return

    script_logger.info("Attempting to start proxy in the background...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(current_dir, 'proxy_auto_start.log')
    proxy_script_sh = os.path.join(current_dir, 'run_proxy.sh')
    proxy_script_py = os.path.join(current_dir, 'ai_proxy.py')

    cmd = None
    if os.path.exists(proxy_script_sh):
        # Make sure the script is executable
        try:
            os.chmod(proxy_script_sh, 0o755)
            cmd = ['/bin/bash', proxy_script_sh]
            script_logger.info(f"Using script: {proxy_script_sh}")
        except OSError as e:
             script_logger.error(f"Failed to set executable permission on {proxy_script_sh}: {e}")
             # Fall through to try ai_proxy.py
             cmd = None

    if cmd is None and os.path.exists(proxy_script_py):
        cmd = ['python3', proxy_script_py]
        script_logger.info(f"Using script: {proxy_script_py}")
    
    if cmd:
        try:
            with open(log_path, 'w') as log_file:
                proxy_process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT, # Combine stdout and stderr
                    cwd=current_dir,
                    preexec_fn=os.setsid if platform.system() != 'Windows' else None # Create process group
                )
                script_logger.info(f"Started proxy process with PID: {proxy_process.pid}. Logs at: {log_path}")
                time.sleep(2) # Give it a moment to start
                if not is_proxy_running_internal():
                     script_logger.warning("Proxy process started but port not responding yet.")
        except Exception as e:
            script_logger.error(f"Failed to start proxy process: {e}")
            proxy_process = None
    else:
        script_logger.error("Could not find run_proxy.sh or ai_proxy.py to start the proxy.")

def stop_background_proxy():
    """Attempts to stop the background proxy process."""
    global proxy_process
    script_logger.info("Attempting to stop background proxy process...")

    killed_via_pid = False
    if proxy_process:
        try:
            script_logger.info(f"Terminating proxy process group with PID: {proxy_process.pid}")
            # Send SIGTERM to the entire process group
            if platform.system() != 'Windows':
                 os.killpg(os.getpgid(proxy_process.pid), signal.SIGTERM)
                 proxy_process.wait(timeout=5) # Wait a bit for clean exit
                 script_logger.info("Proxy process terminated via PID.")
                 killed_via_pid = True
            else:
                 # Windows requires different handling
                 proxy_process.terminate()
                 proxy_process.wait(timeout=5)
                 script_logger.info("Proxy process terminated via PID (Windows).")
                 killed_via_pid = True
        except ProcessLookupError:
             script_logger.info("Proxy process already exited.")
             killed_via_pid = True # Consider it "killed" if it's gone
        except subprocess.TimeoutExpired:
             script_logger.warning(f"Proxy process {proxy_process.pid} did not terminate gracefully, attempting SIGKILL.")
             try:
                 if platform.system() != 'Windows':
                      os.killpg(os.getpgid(proxy_process.pid), signal.SIGKILL)
                      script_logger.info("Proxy process group killed via SIGKILL.")
                 else:
                      proxy_process.kill()
                      script_logger.info("Proxy process killed (Windows).")
                 killed_via_pid = True
             except Exception as e:
                  script_logger.error(f"Error force killing proxy process group: {e}")
        except Exception as e:
            script_logger.error(f"Error stopping proxy process via PID {proxy_process.pid}: {e}")
        proxy_process = None # Reset global var

    # Fallback/Double check using pkill/killall if PID method failed or wasn't available
    if not killed_via_pid:
         script_logger.info("Using pkill/killall as fallback to stop proxy processes.")
         try:
             # Use check=False as these might fail if no process is found
             subprocess.run(['pkill', '-f', 'mitmdump'], check=False, capture_output=True)
             subprocess.run(['pkill', '-f', 'mitmproxy'], check=False, capture_output=True)
             subprocess.run(['pkill', '-f', 'ai_proxy.py'], check=False, capture_output=True)
             
             # More aggressive kill if needed, especially on macOS
             if platform.system() == "Darwin":
                  subprocess.run(['killall', '-9', 'mitmdump'], check=False, capture_output=True)
                  # Be careful killing all python3 processes
                  # subprocess.run(['killall', '-9', 'python3'], check=False, capture_output=True)
                  subprocess.run("ps aux | grep -E 'mitm|ai_proxy' | grep -v grep | awk '{print $2}' | xargs kill -9", shell=True, check=False, capture_output=True)

             script_logger.info("Fallback kill commands executed.")
             time.sleep(0.5)
             if not is_proxy_running_internal():
                  script_logger.info("Proxy appears stopped after fallback.")
             else:
                  script_logger.warning("Proxy might still be running after fallback kill attempts.")

         except Exception as kill_error:
             script_logger.error(f"Error during fallback process kill: {str(kill_error)}")

def find_available_port(start_port=7070, max_attempts=10):
    """Find an available port starting from start_port"""
    port = start_port
    for i in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                script_logger.info(f"Found available port: {port}")
                return port
            except OSError:
                script_logger.warning(f"Port {port} is in use, trying next.")
                port += 1
    script_logger.error(f"Could not find available port after {max_attempts} attempts. Trying last port {port}.")
    return port # Return the last attempted port

# Register the cleanup function to run on exit
atexit.register(stop_background_proxy)

# Handle termination signals
def signal_handler(sig, frame):
    script_logger.info(f"Received signal {sig}, stopping proxy and exiting.")
    stop_background_proxy()
    # Exiting explicitly after cleanup
    raise SystemExit(0) 

if platform.system() != 'Windows':
     signal.signal(signal.SIGTERM, signal_handler)
     signal.signal(signal.SIGINT, signal_handler) # Handles Ctrl+C

if __name__ == '__main__':
    # Disable basic authentication for testing
    os.environ['BASIC_AUTH_ENABLED'] = 'false'

    # Start the proxy in the background
    start_background_proxy()
    
    # Find an available port for the Flask app
    flask_port = find_available_port(start_port=7070)
    
    print("\nStarting Private AI Proxy Frontend...")
    print(f"Access the application at http://localhost:{flask_port}")
    print("Proxy service should be running in the background.")
    
    # Run the Flask app
    # Use use_reloader=False to prevent the script from running twice in debug mode,
    # which would cause issues with starting/stopping the background proxy.
    try:
         app.run(host='0.0.0.0', port=flask_port, debug=True, use_reloader=False)
    except SystemExit:
         script_logger.info("Flask app exited.")
    except Exception as e:
         script_logger.error(f"Flask app encountered an error: {e}")
    finally:
         # Ensure cleanup is attempted even if app.run fails unexpectedly
         stop_background_proxy()
         script_logger.info("run_app.py finished.")