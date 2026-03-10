"""
Router diagnostic script.
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = os.getenv('BOROFONE_TEST_BASE_URL', 'http://localhost:8000').rstrip('/')

print('\n' + '=' * 60)
print('Router Diagnostic')
print('=' * 60 + '\n')

try:
    from app.main import app
    print('app imported successfully')
except Exception as exc:
    print(f'Failed to import app: {exc}')
    sys.exit(1)

routes = app.routes
auth_routes = [route for route in routes if '/auth' in str(route.path)]
print(f'Found {len(auth_routes)} auth routes')

for method, path in [
    ('POST', '/auth/login'),
    ('POST', '/auth/register'),
    ('POST', '/auth/refresh'),
    ('POST', '/auth/logout'),
    ('GET', '/auth/me'),
]:
    found = any(method in getattr(route, 'methods', []) and route.path == path for route in routes)
    print(f'{method} {path}: {found}')

print('\nUse this login endpoint when testing manually:')
print(f'{BASE_URL}/auth/login')
