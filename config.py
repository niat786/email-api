# config.py

import os

# Get the absolute path of the directory where this config.py file is located.
# This makes file loading reliable, regardless of where the server is run from.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_domains_from_file(filename: str) -> set:
    """Helper function to load domains from a text file using an absolute path."""
    absolute_path = os.path.join(_BASE_DIR, filename)
    try:
        with open(absolute_path, "r") as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        print(f"Warning: Domain file not found at '{absolute_path}'.")
        return set()

# Load the disposable domains list.
# Ensure you have a 'disposable_domains.txt' file in your project root.
DISPOSABLE_DOMAINS = load_domains_from_file("disposable_domains.txt")
SUSPICIOUS_TLDS = load_domains_from_file("suspicious_tlds.txt")
FREE_EMAIL_DOMAINS = load_domains_from_file("free_email_domains.txt")