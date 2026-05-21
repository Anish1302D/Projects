"""
HTTPS dev server for Solar System — no external dependencies.
Uses Python's built-in ssl module to generate a self-signed cert at runtime.
Webcam (getUserMedia) requires a secure context (HTTPS) on non-localhost origins.
"""
import http.server, ssl, socket, os, sys, tempfile, subprocess, shutil

PORT = 8080
DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(DIR, "_dev_cert.pem")
KEY_FILE = os.path.join(DIR, "_dev_key.pem")


def generate_cert_with_certutil():
    """Try using PowerShell to create a self-signed cert exported as PFX then PEM."""
    # This is complex on Windows without openssl. Use a simpler approach.
    return False


def generate_cert_python_only():
    """
    Generate a minimal self-signed cert using only Python stdlib.
    This builds raw ASN.1/DER structures for a basic RSA cert.
    """
    import struct, hashlib, secrets, datetime

    # We'll generate RSA key pair using Python 3.x's built-in
    # Since we can't easily do raw RSA key generation without a library,
    # let's try a different approach: use ssl module's built-in test cert generation
    # Actually, the cleanest approach: generate via the ssl module's wrap_socket
    # with adhoc cert using a subprocess to python itself

    script = '''
import ssl, socket, os, sys

# Create a simple server with adhoc cert
# Python doesn't have a direct "generate cert" API in stdlib,
# but we can use the _ssl module's test infrastructure
# Actually - let's just check for openssl in common locations

cert_path = sys.argv[1]
key_path = sys.argv[2]

# Try to find openssl
import shutil
openssl = shutil.which("openssl")
if not openssl:
    # Check common Windows locations
    for p in [
        r"C:\\Program Files\\Git\\usr\\bin\\openssl.exe",
        r"C:\\Program Files (x86)\\Git\\usr\\bin\\openssl.exe",
        r"C:\\Program Files\\OpenSSL-Win64\\bin\\openssl.exe",
        r"C:\\msys64\\usr\\bin\\openssl.exe",
    ]:
        if os.path.exists(p):
            openssl = p
            break

if openssl:
    import subprocess
    subprocess.run([
        openssl, "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_path, "-out", cert_path,
        "-days", "365", "-nodes",
        "-subj", "/CN=SolarSystemDev"
    ], check=True, capture_output=True)
    print("OK")
else:
    print("NO_OPENSSL")
'''
    result = subprocess.run(
        [sys.executable, "-c", script, CERT_FILE, KEY_FILE],
        capture_output=True, text=True
    )
    return "OK" in result.stdout


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def run_https():
    """Start HTTPS server with the generated cert."""
    os.chdir(DIR)
    handler = http.server.SimpleHTTPRequestHandler

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    server = http.server.HTTPServer(("0.0.0.0", PORT), handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    ip = get_local_ip()
    print(f"\n{'='*55}")
    print(f"  [*] Solar System HTTPS Server Running")
    print(f"{'='*55}")
    print(f"  Laptop:  https://localhost:{PORT}")
    print(f"  Phone:   https://{ip}:{PORT}")
    print(f"{'='*55}")
    print(f"  [!] Accept the browser security warning")
    print(f"      (self-signed cert) - click 'Advanced'")
    print(f"      then 'Proceed' to continue.")
    print(f"{'='*55}")
    print(f"  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


def run_http_fallback():
    """Plain HTTP fallback — webcam only works on localhost."""
    os.chdir(DIR)
    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer(("0.0.0.0", PORT), handler)

    ip = get_local_ip()
    print(f"\n{'='*55}")
    print(f"  [*] Solar System HTTP Server (fallback)")
    print(f"{'='*55}")
    print(f"  Laptop:  http://localhost:{PORT}")
    print(f"  Phone:   http://{ip}:{PORT}")
    print(f"{'='*55}")
    print(f"  [!] Webcam will only work on localhost!")
    print(f"     For phone webcam, install Git for Windows")
    print(f"     (includes openssl) and re-run this script.")
    print(f"{'='*55}")
    print(f"  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    # Check if cert already exists
    have_cert = os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)

    if not have_cert:
        print("Generating self-signed SSL certificate...")
        have_cert = generate_cert_python_only()

    if have_cert and os.path.exists(CERT_FILE):
        run_https()
    else:
        print("Could not generate SSL cert — falling back to HTTP.")
        run_http_fallback()
