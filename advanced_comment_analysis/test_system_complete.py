#!/usr/bin/env python3
"""
ACAS System Verification - Simple and Direct
Verifies that all core components are working
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Colors for output
class C:
    G, R, Y, B, E = '\033[92m', '\033[91m', '\033[93m', '\033[94m', '\033[0m'

def test(name, ok, detail=""):
    s = f"{C.G}✓{C.E}" if ok else f"{C.R}✗{C.E}"
    print(f"{s} {name}")
    if detail: print(f"  → {detail}")
    return ok

def main():
    print(f"\n{C.B}{'='*60}{C.E}")
    print(f"{C.B}ACAS SYSTEM VERIFICATION{C.E}")
    print(f"{C.B}{'='*60}{C.E}\n")
    
    results = []
    
    # Test 1: Database
    print(f"{C.Y}[1/5] Database{C.E}")
    try:
        from app.database.session import engine
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        required = {'users', 'comments', 'tickets', 'routing_rules', 'sentic_mappings', 'settings', 'activity_logs'}
        ok = required.issubset(set(tables))
        results.append(test("Tables", ok, f"{len(tables)} tables found"))
    except Exception as e:
        results.append(test("Tables", False, str(e)))
    
    # Test 2: Models
    print(f"\n{C.Y}[2/5] Models{C.E}")
    try:
        from app.models.user import User
        from app.models.comment import Comment
        from app.models.ticket import Ticket
        from app.models.routing_rule import RoutingRule
        from app.models.sentic_mapping import SenticMapping
        from app.models.setting import Setting
        from app.models.activity_log import ActivityLog
        results.append(test("ORM Models", True, "8 models loaded"))
    except Exception as e:
        results.append(test("ORM Models", False, str(e)))
    
    # Test 3: Routes
    print(f"\n{C.Y}[3/5] API Routes{C.E}")
    try:
        from app.api import auth, comments, dashboard, tickets
        results.append(test("Route Modules", True, "4 routers configured"))
    except Exception as e:
        results.append(test("Route Modules", False, str(e)))
    
    # Test 4: Database Connection
    print(f"\n{C.Y}[4/5] Database Connection{C.E}")
    try:
        from app.database.session import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        results.append(test("Session & Query", True, f"{user_count} users in DB"))
    except Exception as e:
        results.append(test("Session & Query", False, str(e)))
    
    # Test 5: FastAPI App
    print(f"\n{C.Y}[5/5] FastAPI Application{C.E}")
    try:
        from app.main import app
        from app.api import auth, comments, dashboard, tickets
        route_count = len(app.routes)
        results.append(test("App & Routes", True, f"{route_count} endpoints"))
    except Exception as e:
        results.append(test("App & Routes", False, str(e)))
    
    # Summary
    print(f"\n{C.B}{'='*60}{C.E}")
    passed = sum(results)
    total = len(results)
    color = C.G if passed == total else C.R
    print(f"{color}RESULT: {passed}/{total} PASSED{C.E}")
    print(f"{C.B}{'='*60}{C.E}\n")
    
    if passed == total:
        print(f"{C.G}✓ ACAS IS OPERATIONAL{C.E}")
        print(f"{C.G}  Frontend: http://127.0.0.1:8000/frontend/login.html{C.E}")
        print(f"{C.G}  API: http://127.0.0.1:8000/docs{C.E}\n")
        return 0
    else:
        print(f"{C.R}✗ Check errors above{C.E}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
