import os
import sys

# ai-services modules use flat imports; add ai-services/ to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force deterministic demo mode for tests (no OpenRouter key)
os.environ.pop("OPENROUTER_API_KEY", None)

# Re-import code_verifier AFTER clearing the key so its module-level
# _api_key reflects the test environment
import importlib

import code_verifier  # noqa: E402

importlib.reload(code_verifier)
