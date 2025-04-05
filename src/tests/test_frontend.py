#!/usr/bin/env python3
"""
Test script for the Private AI Proxy frontend
This script creates a simple Flask application to demonstrate the frontend templates
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import json
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key-for-demo'

# Sample data for demonstration
sample_data = {
    'total_entities': 1245,
    'entity_counts': {
        'PII': 456,
        'DOMAIN': 289,
        'API_KEY': 178,
        'CREDENTIAL': 122,
        'CODE': 98,
        'EMAIL': 56,
        'IP_ADDRESS': 46
    },
    'recent_transformations': [
