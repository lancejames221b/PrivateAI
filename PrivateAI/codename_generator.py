"""
Codename Generator for Private AI

This module provides dynamic codename generation for organizations, products, 
and other entities that should be consistently anonymized across sessions.
"""

import os
import json
import random
import hashlib
import sqlite3
from datetime import datetime

# Database connection
DB_PATH = 'data/codename_mappings.db'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Lists for generating random but plausible codenames
ADJECTIVES = [
    "Swift", "Agile", "Secure", "Dynamic", "Global", "Silent", "Rapid", "Strategic", "Quantum", 
    "Smart", "Bright", "Clever", "Nimble", "Keen", "Sharp", "Quick", "Wise", "Astute", "Adept",
    "Calm", "Bold", "Brave", "Clear", "Deft", "Elite", "Epic", "Fast", "Firm", "Grand", "Great",
    "Prime", "Pure", "Safe", "Sage", "Sleek", "Smooth", "Strong", "True", "Vast", "Vital"
]

TECH_NOUNS = [
    "Shield", "Guard", "Sentinel", "Fortress", "Bastion", "Defender", "Protector", "Guardian", 
    "Aegis", "Bulwark", "Citadel", "Barrier", "Firewall", "Rampart", "Vault", "Keep", "Sentry",
    "Peak", "Core", "Nexus", "Hub", "Sphere", "Pulse", "Wave", "Flow", "Link", "Node", "Mind",
    "Logic", "Cloud", "Data", "Force", "Vision", "Insight", "System", "Network", "Matrix", "Path",
    "Portal", "Edge", "Point", "Circuit", "Signal", "Stream", "Vector", "Cipher", "Code"
]

INDUSTRY_PREFIXES = {
    "security": ["Cyber", "Secure", "Guard", "Shield", "Protect", "Defense", "Sentinel", "Fortress"],
    "cloud": ["Cloud", "Sky", "Nimbus", "Stratus", "Cumulus", "Vapor", "Aether", "Nebula"],
    "ai": ["AI", "Neural", "Cognitive", "Smart", "Intellect", "Brain", "Mind", "Logic"],
    "software": ["Soft", "Code", "Dev", "Byte", "Script", "App", "Program", "Logic"],
    "finance": ["Fin", "Capital", "Asset", "Wealth", "Money", "Value", "Equity", "Trust"],
    "healthcare": ["Health", "Care", "Med", "Cure", "Vital", "Life", "Wellness", "Healing"],
    "retail": ["Shop", "Store", "Mart", "Market", "Retail", "Trade", "Commerce", "Bazaar"],
    "manufacturing": ["Manu", "Craft", "Forge", "Build", "Make", "Construct", "Factory", "Works"],
    "telecom": ["Com", "Connect", "Link", "Net", "Signal", "Wave", "Pulse", "Broadcast"],
    "energy": ["Energy", "Power", "Fuel", "Volt", "Current", "Charge", "Force", "Dynamo"],
    "transportation": ["Trans", "Move", "Way", "Path", "Route", "Drive", "Motion", "Journey"],
    "media": ["Media", "Vision", "View", "Cast", "Stream", "Channel", "Sight", "Display"],
    "gaming": ["Game", "Play", "Fun", "Joy", "Quest", "Level", "Arena", "Virtual"]
}

def initialize_db():
    """Initialize the database for storing codename mappings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organization_mappings (
        original TEXT PRIMARY KEY,
        codename TEXT NOT NULL,
        industry TEXT,
        created_at TEXT,
        last_used TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS domain_mappings (
        original TEXT PRIMARY KEY,
        codename TEXT NOT NULL,
        organization_id TEXT,
        created_at TEXT,
        last_used TEXT,
        FOREIGN KEY (organization_id) REFERENCES organization_mappings(original)
    )
    ''')
    
    conn.commit()
    conn.close()

def detect_industry(org_name):
    """Try to detect the industry of an organization based on its name"""
    org_name = org_name.lower()
    
    industry_keywords = {
        "security": ["security", "cyber", "protect", "defense", "guard", "sentinel", "shield", "firewall"],
        "cloud": ["cloud", "aws", "azure", "gcp", "hosting", "saas", "paas", "iaas"],
        "ai": ["ai", "ml", "artificial", "intelligence", "neural", "learning", "cognitive", "nlp"],
        "software": ["software", "app", "tech", "code", "dev", "system", "platform", "digital"],
        "finance": ["bank", "finance", "capital", "invest", "money", "payment", "credit", "loan"],
        "healthcare": ["health", "care", "medical", "pharma", "patient", "hospital", "clinic", "bio"],
        "retail": ["retail", "shop", "store", "market", "commerce", "buy", "sell", "consumer"],
        "manufacturing": ["manufacturing", "factory", "production", "industry", "make", "build", "assemble"],
        "telecom": ["telecom", "communication", "network", "cellular", "mobile", "phone", "broadband"],
        "energy": ["energy", "power", "electric", "utility", "gas", "oil", "renewable", "solar"],
        "transportation": ["transport", "logistics", "shipping", "freight", "delivery", "fleet", "cargo"],
        "media": ["media", "news", "entertainment", "broadcast", "publish", "content", "stream"],
        "gaming": ["game", "gaming", "play", "interactive", "entertainment", "virtual", "console"]
    }
    
    # Count keyword matches for each industry
    matches = {industry: 0 for industry in industry_keywords}
    
    for industry, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword in org_name:
                matches[industry] += 1
    
    # Return the industry with the most matches, or "tech" as a fallback
    best_match = max(matches.items(), key=lambda x: x[1])
    if best_match[1] > 0:
        return best_match[0]
    return "software"  # Default to software/tech industry

def generate_organization_codename(org_name, industry=None):
    """Generate a consistent and natural-sounding codename for an organization"""
    # Determine industry if not provided
    if not industry:
        industry = detect_industry(org_name)
    
    # Create a hash of the organization name for consistency
    # Use first 8 characters of the hash for deterministic random seed
    hash_value = hashlib.md5(org_name.lower().encode()).hexdigest()
    seed_value = int(hash_value[:8], 16)
    random.seed(seed_value)
    
    # Select appropriate industry prefix or general adjective
    if industry in INDUSTRY_PREFIXES:
        prefix = random.choice(INDUSTRY_PREFIXES[industry])
    else:
        prefix = random.choice(ADJECTIVES)
    
    # Select a noun
    noun = random.choice(TECH_NOUNS)
    
    # Format the codename
    codename = f"{prefix}{noun}"
    
    # Reset the random seed
    random.seed()
    
    return codename

def get_organization_codename(org_name):
    """Get existing or generate new codename for an organization"""
    if not org_name:
        return f"UnknownOrg-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6]}"
    
    # Standardize the organization name
    org_name = org_name.lower().strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we already have a mapping
    cursor.execute("SELECT codename, industry FROM organization_mappings WHERE original = ?", (org_name,))
    result = cursor.fetchone()
    
    if result:
        codename, industry = result
        # Update last used time
        cursor.execute("UPDATE organization_mappings SET last_used = ? WHERE original = ?", 
                     (datetime.now().isoformat(), org_name))
        conn.commit()
    else:
        # Generate new codename
        industry = detect_industry(org_name)
        codename = generate_organization_codename(org_name, industry)
        
        # Store the mapping
        cursor.execute("INSERT INTO organization_mappings VALUES (?, ?, ?, ?, ?)",
                     (org_name, codename, industry, 
                     datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
    
    conn.close()
    return codename

def get_domain_codename(domain, associated_org=None):
    """Get existing or generate new codename for a domain"""
    if not domain:
        return f"unknown-domain-{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6]}.example.com"
    
    # Standardize the domain
    domain = domain.lower().strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we already have a mapping
    cursor.execute("SELECT codename FROM domain_mappings WHERE original = ?", (domain,))
    result = cursor.fetchone()
    
    if result:
        codename = result[0]
        # Update last used time
        cursor.execute("UPDATE domain_mappings SET last_used = ? WHERE original = ?", 
                     (datetime.now().isoformat(), domain))
        conn.commit()
    else:
        # Try to associate with organization
        org_id = associated_org
        
        if not org_id:
            # Extract possible organization name from domain
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                possible_org = domain_parts[0]
                # Check if this matches any known organization
                cursor.execute("SELECT original FROM organization_mappings WHERE original LIKE ?", 
                            (f"%{possible_org}%",))
                org_result = cursor.fetchone()
                if org_result:
                    org_id = org_result[0]
        
        if org_id:
            # Get the organization's codename
            cursor.execute("SELECT codename FROM organization_mappings WHERE original = ?", (org_id,))
            org_result = cursor.fetchone()
            if org_result:
                org_codename = org_result[0]
                
                # Create a domain-specific hash for subdomain variety
                domain_hash = hashlib.md5(domain.encode()).hexdigest()[:6]
                codename = f"{org_codename.lower()}-{domain_hash}.example.com"
            else:
                # Fallback to generic domain codename
                domain_hash = hashlib.md5(domain.encode()).hexdigest()[:8]
                codename = f"domain-{domain_hash}.example.com"
        else:
            # Generate generic domain codename
            domain_hash = hashlib.md5(domain.encode()).hexdigest()[:8]
            codename = f"domain-{domain_hash}.example.com"
        
        # Store the mapping
        cursor.execute("INSERT INTO domain_mappings VALUES (?, ?, ?, ?, ?)",
                     (domain, codename, org_id if org_id else None, 
                     datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
    
    conn.close()
    return codename

def export_mappings(output_file='data/codename_mappings.json'):
    """Export all mappings to a JSON file for reference"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all organization mappings
    cursor.execute("SELECT original, codename, industry, created_at, last_used FROM organization_mappings")
    org_rows = cursor.fetchall()
    org_mappings = {row['original']: {
        'codename': row['codename'],
        'industry': row['industry'],
        'created_at': row['created_at'],
        'last_used': row['last_used']
    } for row in org_rows}
    
    # Get all domain mappings
    cursor.execute("SELECT original, codename, organization_id, created_at, last_used FROM domain_mappings")
    domain_rows = cursor.fetchall()
    domain_mappings = {row['original']: {
        'codename': row['codename'],
        'organization_id': row['organization_id'],
        'created_at': row['created_at'],
        'last_used': row['last_used']
    } for row in domain_rows}
    
    # Create the export data
    export_data = {
        'organizations': org_mappings,
        'domains': domain_mappings,
        'export_date': datetime.now().isoformat()
    }
    
    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    conn.close()
    return output_file

def import_mappings(input_file='data/codename_mappings.json'):
    """Import mappings from a JSON file"""
    if not os.path.exists(input_file):
        return False, f"File not found: {input_file}"
    
    try:
        with open(input_file, 'r') as f:
            import_data = json.load(f)
        
        if 'organizations' not in import_data or 'domains' not in import_data:
            return False, "Invalid import file format"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Import organization mappings
        for org_name, org_data in import_data['organizations'].items():
            cursor.execute("""
                INSERT OR REPLACE INTO organization_mappings 
                (original, codename, industry, created_at, last_used)
                VALUES (?, ?, ?, ?, ?)
            """, (
                org_name, 
                org_data['codename'], 
                org_data.get('industry', 'unknown'),
                org_data.get('created_at', datetime.now().isoformat()),
                org_data.get('last_used', datetime.now().isoformat())
            ))
        
        # Import domain mappings
        for domain, domain_data in import_data['domains'].items():
            cursor.execute("""
                INSERT OR REPLACE INTO domain_mappings 
                (original, codename, organization_id, created_at, last_used)
                VALUES (?, ?, ?, ?, ?)
            """, (
                domain, 
                domain_data['codename'], 
                domain_data.get('organization_id', None),
                domain_data.get('created_at', datetime.now().isoformat()),
                domain_data.get('last_used', datetime.now().isoformat())
            ))
        
        conn.commit()
        conn.close()
        
        return True, f"Successfully imported mappings from {input_file}"
    
    except Exception as e:
        return False, f"Error importing mappings: {str(e)}"

# Initialize database on module import
initialize_db()