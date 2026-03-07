#!/usr/bin/env python3
"""
HTTPS Server Runner for Borofone Chat

This script runs the FastAPI application with HTTPS support.
Use this for local development with Radmin VPN to enable voice chat.

Usage:
    python run_https.py [--host HOST] [--port PORT] [--cert CERT] [--key KEY]
    python run_https.py --pfx ssl/voice.pfx --pfx-password 1234

Requirements:
    - SSL certificates in ./ssl/ directory (run scripts/generate_ssl.ps1 first)
    - Or specify custom paths with --cert and --key
    - For PFX support: pip install pyOpenSSL
"""

import argparse
import os
import sys
import tempfile
import uvicorn

def convert_pfx_to_pem(pfx_path: str, password: str) -> tuple[str, str]:
    """
    Convert PFX file to PEM format using cryptography library.
    Returns tuple of (cert_pem_path, key_pem_path) as temporary files.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import pkcs12
    except ImportError:
        print("Error: cryptography library required for PFX support")
        print("Install with: pip install cryptography")
        sys.exit(1)
    
    with open(pfx_path, "rb") as f:
        pfx_data = f.read()
    
    # Extract private key and certificate
    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, password.encode()
    )
    
    # Create temporary files
    cert_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
    key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
    
    # Write certificate
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    cert_file.write(cert_pem.decode())
    cert_file.close()
    
    # Write private key
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    key_file.write(key_pem.decode())
    key_file.close()
    
    return cert_file.name, key_file.name

def main():
    parser = argparse.ArgumentParser(description="Run Borofone Chat with HTTPS")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0 for external access)"
    )
    parser.add_argument(
        "--port", 
        default=443, 
        type=int,
        help="Port to bind to (default: 443 for HTTPS)"
    )
    parser.add_argument(
        "--cert",
        default="ssl/cert.pem",
        help="Path to SSL certificate file (default: ssl/cert.pem)"
    )
    parser.add_argument(
        "--key",
        default="ssl/key.pem",
        help="Path to SSL private key file (default: ssl/key.pem)"
    )
    parser.add_argument(
        "--pfx",
        default=None,
        help="Path to PFX file (alternative to cert/key). Auto-converts to PEM."
    )
    parser.add_argument(
        "--pfx-password",
        default="1234",
        help="Password for PFX file (default: 1234)"
    )
    
    args = parser.parse_args()
    
    cert_file = args.cert
    key_file = args.key
    temp_files = []
    
    # Handle PFX file
    if args.pfx:
        if not os.path.exists(args.pfx):
            print(f"Error: PFX file not found: {args.pfx}")
            sys.exit(1)
        
        print(f"Converting PFX to PEM: {args.pfx}")
        cert_file, key_file = convert_pfx_to_pem(args.pfx, args.pfx_password)
        temp_files = [cert_file, key_file]
        print("PFX converted successfully!")
    else:
        # Check if PEM files exist, if not try PFX
        if not os.path.exists(args.cert) or not os.path.exists(args.key):
            pfx_path = "ssl/voice.pfx"
            if os.path.exists(pfx_path):
                print(f"PEM files not found, using PFX: {pfx_path}")
                cert_file, key_file = convert_pfx_to_pem(pfx_path, "1234")
                temp_files = [cert_file, key_file]
                print("PFX converted successfully!")
            else:
                if not os.path.exists(args.cert):
                    print(f"Error: Certificate file not found: {args.cert}")
                if not os.path.exists(args.key):
                    print(f"Error: Private key file not found: {args.key}")
                print("\nTo generate SSL certificates, run:")
                print("  PowerShell (as Admin): .\\scripts\\generate_ssl.ps1")
                sys.exit(1)
    
    print("=" * 50)
    print("Borofone Chat - HTTPS Server")
    print("=" * 50)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Certificate: {cert_file}")
    print(f"Private Key: {key_file}")
    print("=" * 50)
    print(f"\nServer starting at: https://{args.host}:{args.port}/")
    print("For Radmin VPN friends: https://26.150.183.241/")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run uvicorn with SSL
        # max_request_body_size=50MB allows uploading larger GIFs and files
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            ssl_certfile=cert_file,
            ssl_keyfile=key_file,
            reload=False,  # Disable reload for HTTPS
            access_log=True,
            limit_concurrency=100,
            limit_max_requests=1000,
            timeout_keep_alive=30,
            # Increase max request body size for file uploads (50MB)
            http_max_header_size=65536,
            max_request_body_size=50 * 1024 * 1024
        )
    finally:
        # Cleanup temporary files
        for f in temp_files:
            try:
                os.unlink(f)
            except:
                pass

if __name__ == "__main__":
    main()
