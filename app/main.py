from fastapi import FastAPI, HTTPException, Response
import os
import sys

# Import our logic modules
# We add the parent directory to path so imports work cleanly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import DecryptRequest, VerifyRequest
from app.crypto_utils import decrypt_seed
from app.totp_utils import generate_totp_code, verify_totp_code

app = FastAPI()

# CONSTANTS
# In Docker, this will use the volume mount /data
# In Windows Local, we'll try to use C:\data, or fall back to local folder
DATA_DIR = "/data"
if os.name == 'nt' and not os.path.exists(DATA_DIR):
     # If on Windows and C:\data doesn't exist, use current directory for testing
     DATA_DIR = os.path.abspath("data_test")
     os.makedirs(DATA_DIR, exist_ok=True)
     print(f"WARNING: Running on Windows without C:\\data. Using local test folder: {DATA_DIR}")

SEED_FILE_PATH = os.path.join(DATA_DIR, "seed.txt")
PRIVATE_KEY_PATH = "student_private.pem"

@app.post("/decrypt-seed")
async def api_decrypt_seed(req: DecryptRequest):
    """
    Endpoint 1: Decrypts the seed and saves it to storage.
    """
    try:
        # 1. Load Private Key
        # We assume the key is in the root app directory (Docker workdir)
        if not os.path.exists(PRIVATE_KEY_PATH):
             return Response(content='{"error": "Private key not found"}', media_type="application/json", status_code=500)

        # 2. Decrypt
        hex_seed = decrypt_seed(req.encrypted_seed, PRIVATE_KEY_PATH)

        # 3. Save to /data/seed.txt
        # Ensure directory exists
        os.makedirs(os.path.dirname(SEED_FILE_PATH), exist_ok=True)

        with open(SEED_FILE_PATH, "w") as f:
            f.write(hex_seed)

        return {"status": "ok"}

    except Exception as e:
        # Requirement: Return HTTP 500 on failure with specific JSON
        print(f"Decryption Error: {e}")
        return Response(content='{"error": "Decryption failed"}', media_type="application/json", status_code=500)

@app.get("/generate-2fa")
async def api_generate_2fa():
    """
    Endpoint 2: Generates a TOTP code from the stored seed.
    """
    # 1. Check if seed exists
    if not os.path.exists(SEED_FILE_PATH):
        return Response(content='{"error": "Seed not decrypted yet"}', media_type="application/json", status_code=500)

    try:
        # 2. Read seed
        with open(SEED_FILE_PATH, "r") as f:
            hex_seed = f.read().strip()

        # 3. Generate Code
        code, valid_for = generate_totp_code(hex_seed)
        return {"code": code, "valid_for": valid_for}

    except Exception as e:
        return Response(content=f'{{"error": "{str(e)}"}}', media_type="application/json", status_code=500)

@app.post("/verify-2fa")
async def api_verify_2fa(req: VerifyRequest):
    """
    Endpoint 3: Verifies a provided TOTP code.
    """
    # 1. Validate input (Handled by Pydantic, but explicit check for empty)
    if not req.code:
         return Response(content='{"error": "Missing code"}', media_type="application/json", status_code=400)

    # 2. Check if seed exists
    if not os.path.exists(SEED_FILE_PATH):
        return Response(content='{"error": "Seed not decrypted yet"}', media_type="application/json", status_code=500)

    try:
        # 3. Read seed
        with open(SEED_FILE_PATH, "r") as f:
            hex_seed = f.read().strip()

        # 4. Verify
        is_valid = verify_totp_code(hex_seed, req.code)
        return {"valid": is_valid}

    except Exception as e:
         return Response(content=f'{{"error": "{str(e)}"}}', media_type="application/json", status_code=500)