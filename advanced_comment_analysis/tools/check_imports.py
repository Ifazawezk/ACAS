modules = [
    'app.main',
    'app.database.session',
    'app.models.user',
    'app.models.comment',
    'app.models.ticket',
    'app.api.auth',
    'app.api.ai',
    'app.api.comments',
    'app.api.tickets',
    'app.api.dashboard',
    'app.services.ai_service',
    'app.services.openai_client',
    'app.services.auth_service',
    'app.services.comment_ticket_service',
    'app.services.csv_service',
    'app.utils.security',
    'app.utils.roles',
    'app.utils.logging_config'
]

import importlib
import os
import sys

# Ensure project root is on sys.path so 'app' package imports work when running the script
root = os.path.abspath(os.getcwd())
if root not in sys.path:
    sys.path.insert(0, root)

for m in modules:
    try:
        importlib.import_module(m)
        print('OK', m)
    except Exception as e:
        print('ERR', m, repr(e))
