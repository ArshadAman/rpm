import json
import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509 import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

# Load API keys from environment variables (if needed)
API_KEY_NAME = os.getenv("API_KEY_NAME", "X-API-KEY")
API_KEY_VALUE = os.getenv("API_KEY_VALUE", "your-api-key")

# Load valid certificates from file
try:
    with open("validCertificates.json", "r") as f:
        valid_certificates = json.load(f)
except FileNotFoundError:
    valid_certificates = {}

def save_valid_certificates():
    """Saving certificates so we don’t lose them when the script stops."""
    with open("validCertificates.json", "w") as f:
        json.dump(valid_certificates, f, indent=2)

def validate_api_key(api_key):
    """Check if the API key is legit. We don’t want any fakes here!"""
    if api_key != API_KEY_VALUE:
        print("Oops! Unauthorized - That API Key doesn’t look right.")
        return False
    return True

def generate_custom_keys_and_certificate(device_id):
    """Generate an RSA key pair and a self-signed certificate for the given device_id."""
    # Generate RSA private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Build self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, device_id),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).sign(private_key, hashes.SHA256())

    certificate_pem = cert.public_bytes(Encoding.PEM).decode('utf-8')
    private_key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.TraditionalOpenSSL,
        NoEncryption()
    ).decode('utf-8')

    return {
         "certificateId": cert.serial_number,
         "certificatePem": certificate_pem,
         "privateKeyPem": private_key_pem
    }

def sign_certificate(device_id, model_number, api_key):
    """Sign and register a device certificate. Let's get this party started!"""
    if not validate_api_key(api_key):
        return

    if not device_id or not model_number:
        print("Hold up! We need both deviceId and modelNumber. Can you fill those in?")
        return

    print(f"Signing certificate for device {device_id} ({model_number})... Let's do this!")
    cert = generate_custom_keys_and_certificate(device_id)
    valid_certificates[str(cert["certificateId"])] = device_id
    save_valid_certificates()
    print(f"🎉 Certificate generated: {json.dumps(cert, indent=2)}")

def sync_device_certificate(device_id, model_number, certificate_id, certificate_pem, api_key):
    """Sync an existing device certificate. Just making sure everything is in place."""
    if not validate_api_key(api_key):
        return

    if not all([device_id, model_number, certificate_id, certificate_pem]):
        print("Wait a sec! You're missing some required details. Double-check and try again.")
        return

    valid_certificates[certificate_id] = device_id
    save_valid_certificates()
    print("✅ Certificate synced successfully. Nice job!")

def telemetry_data(api_key, data):
    """Receive and print telemetry data. Let’s see what’s going on!"""
    if not validate_api_key(api_key):
        return

    print(f"Telemetry data received: {json.dumps(data, indent=2)}")

def status_data(api_key, data):
    """Receive and print status data. How's everything looking?"""
    if not validate_api_key(api_key):
        return

    print(f"Status data received: {json.dumps(data, indent=2)}")

def device_telemetry(api_key, device_id, data):
    """Handle device telemetry with optional device ID. What’s the scoop?"""
    if not validate_api_key(api_key):
        return

    print(f"Device Telemetry (Device: {device_id}): {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    api_key = "api-key"  
    sign_certificate("device123", "modelXYZ", api_key)
    sync_device_certificate("device123", "modelXYZ", "cert456", "sample_cert_pem", api_key)
    telemetry_data(api_key, {"temperature": 36.5, "status": "ok"})
    status_data(api_key, {"battery": "80%", "network": "Connected"})
    device_telemetry(api_key, "device123", {"sensor": "active"})