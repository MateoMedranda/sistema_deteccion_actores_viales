"""The controlled upstream remains isolated from private model runtime.
US2 adds a separate gateway process; this module never selects private settings.
"""
from tests.e2e.serve_frontend_test_api import app
