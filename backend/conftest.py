import os
import sys
from pathlib import Path

# Default mock environment variables for unit tests (runs when no .env is present)
DEFAULT_TEST_ENV = {
    "PROJECT_NAME": "KRNL Test",
    "DEBUG": "True",
    "PORT": "8000",
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_ANON_KEY": "mock_anon",
    "SUPABASE_SERVICE_ROLE_KEY": "mock_role",
    "ENCRYPTION_KEY": "1234567890123456789012345678901234567890123=",
    "REDIS_URL": "redis://localhost:6379/0",
    "GEMINI_API_KEY": "mock_gemini_key",
    "QDRANT_URL": "http://localhost:6333",
    "QDRANT_API_KEY": "mock_qdrant_key",
    "VAPID_PRIVATE_KEY": "mock_vapid_key",
}

for k, v in DEFAULT_TEST_ENV.items():
    os.environ.setdefault(k, v)

# Add backend directory to Python path so imports like 'from app.utils...' work
sys.path.insert(0, str(Path(__file__).parent))
