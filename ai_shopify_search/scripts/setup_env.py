#!/usr/bin/env python3
"""
Setup script voor environment variables.
Dit script helpt bij het aanmaken van een .env bestand na een fresh clone.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

def setup_env():
    """Setup environment variables door env.example te kopiëren naar .env"""
    
    # Bepaal de huidige directory
    current_dir = Path(__file__).parent
    env_example = current_dir / "env.example"
    env_file = current_dir / ".env"
    
    print("🔧 Setting up environment variables...")
    
    # Check of env.example bestaat
    if not env_example.exists():
        print("❌ env.example bestand niet gevonden!")
        print("   Maak eerst een env.example bestand aan met de benodigde variabelen.")
        return False
    
    # Check of .env al bestaat
    if env_file.exists():
        print("⚠️  .env bestand bestaat al!")
        response = input("   Wil je het overschrijven? (y/N): ").lower().strip()
        if response != 'y':
            print("   Setup geannuleerd.")
            return False
    
    try:
        # Kopieer env.example naar .env
        shutil.copy2(env_example, env_file)
        print("✅ .env bestand succesvol aangemaakt!")
        print("📝 Vergeet niet om de waarden in .env aan te passen met je echte API keys.")
        print("   Belangrijke variabelen om in te vullen:")
        print("   - OPENAI_API_KEY")
        print("   - SHOPIFY_API_KEY")
        print("   - SHOPIFY_API_SECRET")
        print("   - SHOPIFY_STORE_URL")
        return True
        
    except Exception as e:
        print(f"❌ Fout bij het aanmaken van .env: {e}")
        return False

def check_env():
    """Check of alle benodigde environment variables zijn ingesteld"""
    
    # Laad .env bestand als het bestaat
    current_dir = Path(__file__).parent
    env_file = current_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    required_vars = [
        "OPENAI_API_KEY",
        "SHOPIFY_API_KEY", 
        "SHOPIFY_API_SECRET",
        "SHOPIFY_STORE_URL"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  De volgende environment variables zijn niet ingesteld:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   Vul deze in in je .env bestand.")
        return False
    else:
        print("✅ Alle benodigde environment variables zijn ingesteld!")
        return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_env()
    else:
        setup_env() 