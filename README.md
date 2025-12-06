# PKI & TOTP Two-Factor Authentication Service

## Project Overview
This project implements a secure, containerized microservice that demonstrates enterprise-grade security practices. It combines **Public Key Infrastructure (PKI)** for secure seed transmission and **Time-based One-Time Password (TOTP)** for user authentication.

The service is built with **FastAPI**, containerized with **Docker**, and includes an automated **Cron job** for background auditing.

## Key Features
* **Asymmetric Encryption:** Uses RSA 4096-bit encryption (OAEP padding) to securely receive TOTP seeds.
* **2FA Implementation:** Generates and verifies standard 6-digit TOTP codes (SHA-1, 30s period).
* **Persistence:** Docker volumes ensure seed data and logs survive container restarts.
* **Automated Logging:** A background cron job generates and logs valid 2FA codes every minute.
* **Security:** Implements input validation via Pydantic models and strict error handling.

## Technology Stack
* **Language:** Python 3.11
* **Framework:** FastAPI + Uvicorn
* **Containerization:** Docker & Docker Compose
* **Cryptography:** `cryptography` library (RSA-PSS, RSA-OAEP)
* **TOTP:** `pyotp` library
* **Task Scheduling:** Linux Cron

---

## Getting Started

### Prerequisites
* Docker & Docker Compose installed on your machine.
* Git.
* OpenSSL (for generating keys).

### Configuration & Key Generation
Before running the container, you must generate your own RSA key pair. This service requires a private key to decrypt incoming seeds.

**1. Generate a Private Key:**

openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:4096

**2. Generate the Public Key:**

Bash

openssl rsa -pubout -in private_key.pem -out public_key.pem
Placement: Place these files in the root directory (or update your Dockerfile/docker-compose.yml to reflect their location).

Security Note: Ensure private_key.pem is included in your .gitignore to prevent accidental commitment to version control.

### Installation & Run
**1. Clone the repository:**

Bash

git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
**2. Build and Start the Container:**

Bash

docker-compose up -d --build
This will start the API server on port 8080 and the Cron daemon in the background.

**3. Verify the container is running:**

Bash

docker ps

### API Documentation
The microservice exposes the following REST endpoints on port 8080.

***1. Decrypt Seed***
Receives an encrypted seed, decrypts it using the server's private key, and stores it persistently.

Endpoint: POST /decrypt-seed

Content-Type: application/json

Payload:

JSON

{
  "encrypted_seed": "BASE64_ENCODED_STRING..."
}
Response (200 OK):

JSON

{
  "status": "ok"
}
***2. Generate 2FA Code***
Generates a current TOTP code based on the stored seed.

Endpoint: GET /generate-2fa

Response (200 OK):

JSON

{
  "code": "123456",
  "valid_for": 28
}
***3. Verify 2FA Code***
Verifies a user-provided code against the stored seed. Supports a tolerance of ±1 period (30 seconds).

Endpoint: POST /verify-2fa

Payload:

JSON

{
  "code": "123456"
}
Response (200 OK):

JSON

{
  "valid": true
}
(Returns false if invalid)

### Cron Job & Persistence
***Automated Logging***
A Cron job is configured to run every minute inside the container. It performs the following:

Reads the decrypted seed from /data/seed.txt.

Generates the current 2FA code.

Logs the timestamp (UTC) and code to /cron/last_code.txt.

Verifying Cron Output: To check the automated logs:

Bash

docker exec <container_name> cat /cron/last_code.txt
Output format: YYYY-MM-DD HH:MM:SS - 2FA Code: XXXXXX

### Persistence Volumes
Two Docker volumes are defined in docker-compose.yml to ensure data persists across restarts:

seed-data → Mounted at /data (Stores the decrypted seed).

cron-output → Mounted at /cron (Stores the audit logs).

Security Best Practices
Key Management: In a production environment, private keys should never be stored in the code or Docker image. They should be injected via secret managers (e.g., AWS Secrets Manager, HashiCorp Vault) or environment variables.

Input Validation: This service uses Pydantic models to strictly validate all incoming payloads.

### Testing Guide
You can manually test the flow using curl.

***1. Decrypt the seed (Assuming you have a file encrypted_seed.txt containing the Base64 ciphertext)***

Bash

curl -X POST http://localhost:8080/decrypt-seed \
  -H "Content-Type: application/json" \
  -d "{\"encrypted_seed\": \"$(cat encrypted_seed.txt)\"}"
***2. Get a Code***

Bash

curl http://localhost:8080/generate-2fa
***3. Verify a Code***

Bash

curl -X POST http://localhost:8080/verify-2fa \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
