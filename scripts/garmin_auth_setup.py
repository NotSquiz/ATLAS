#!/usr/bin/env python3
"""
Garmin Connect Authentication Setup

One-time interactive login that saves session tokens to ~/.garth/
for automated Garmin data sync.

Usage:
    # Option 1: Set credentials in .env, then run
    export GARMIN_USERNAME="your@email.com"
    export GARMIN_PASSWORD="your_password"
    python scripts/garmin_auth_setup.py

    # Option 2: Interactive prompt
    python scripts/garmin_auth_setup.py

After successful auth:
    - Tokens saved to ~/.garth/
    - Remove GARMIN_PASSWORD from .env (keep username for reference)
    - Tokens auto-refresh on subsequent runs
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

GARTH_HOME = Path.home() / ".garth"


def main():
    """Run one-time Garmin authentication setup."""
    try:
        import garth
    except ImportError:
        print("Error: garth library not installed.")
        print("Run: pip install garth==0.4.46")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  GARMIN CONNECT AUTHENTICATION SETUP")
    print("=" * 60)
    print()

    # Get credentials from env or prompt
    email = os.environ.get("GARMIN_USERNAME")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email:
        email = input("Garmin Connect email: ").strip()
    else:
        print(f"Using GARMIN_USERNAME from environment: {email}")

    if not password:
        import getpass
        password = getpass.getpass("Garmin Connect password: ")
    else:
        print("Using GARMIN_PASSWORD from environment")

    if not email or not password:
        print("Error: Email and password are required.")
        sys.exit(1)

    print()
    print("Authenticating with Garmin Connect...")

    try:
        # Authenticate
        garth.login(email, password)

        # Save session tokens
        GARTH_HOME.mkdir(parents=True, exist_ok=True)
        garth.save(GARTH_HOME)

        print()
        print("SUCCESS! Session tokens saved.")
        print()
        print(f"Token location: {GARTH_HOME}")
        print()
        print("Next steps:")
        print("  1. Remove GARMIN_PASSWORD from your .env file")
        print("  2. Keep GARMIN_USERNAME for reference")
        print("  3. Test sync: python -m atlas.health.cli garmin sync")
        print()
        print("Tokens will auto-refresh on subsequent runs.")
        print("=" * 60)

    except garth.exc.GarthHTTPError as e:
        print()
        print(f"Authentication failed: {e}")
        print()
        print("Common issues:")
        print("  - Wrong email/password")
        print("  - Account locked (too many attempts)")
        print("  - 2FA enabled (not supported by garth)")
        print()
        sys.exit(1)
    except Exception as e:
        print()
        print(f"Unexpected error: {e}")
        sys.exit(1)


def verify_session():
    """Verify that saved session is valid."""
    try:
        import garth
    except ImportError:
        return False

    if not GARTH_HOME.exists():
        return False

    try:
        garth.resume(GARTH_HOME)
        # Test with lightweight API call
        garth.connectapi("/userprofile-service/socialProfile")
        return True
    except Exception:
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        valid = verify_session()
        print(f"Session valid: {valid}")
        sys.exit(0 if valid else 1)
    else:
        main()
