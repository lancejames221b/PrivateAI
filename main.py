#!/usr/bin/env python3
"""
Private AI - Main entry point

This is the main entry point for the Private AI application.
It provides a simple interface to the various components.
"""

import os
import sys
import argparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for the Private AI application."""
    parser = argparse.ArgumentParser(description='Private AI - AI Tools Privacy Protection')
    parser.add_argument('command', choices=['launch', 'analyze', 'test', 'help'],
                        help='Command to execute')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.command == 'launch':
        from core.ai_proxy import launch_proxy
        launch_proxy(debug=args.debug)
    elif args.command == 'analyze':
        from privacy.analyzer import analyze_traffic
        analyze_traffic(debug=args.debug)
    elif args.command == 'test':
        from tests.test_privacy import run_tests
        run_tests(debug=args.debug)
    elif args.command == 'help':
        parser.print_help()

if __name__ == '__main__':
    main()
