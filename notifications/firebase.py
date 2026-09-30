import os, json, base64
import firebase_admin
from firebase_admin import credentials

if not firebase_admin._apps:
    firebase_b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_B64")
    if not firebase_b64:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_B64 is not set!")

    # Decode Base64 and load JSON
    service_account_info = json.loads(base64.b64decode(firebase_b64))
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized successfully")

