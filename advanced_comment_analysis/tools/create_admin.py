#!/usr/bin/env python3
"""Create an admin account. Run this on the server, because no public route can make an admin.

    python tools/create_admin.py --username owner --email owner@example.com

It asks for the password. For scripts, set ACAS_ADMIN_PASSWORD instead. There is no password
option, because command line arguments end up in shell history and process lists.
"""
import argparse
import getpass
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: F401  Registers every table before they are created.
from app.database.session import Base, SessionLocal, engine
from app.models.user import UserRole
from app.services import auth_service
from app.utils.security import MAX_PASSWORD_BYTES

MIN_PASSWORD_LENGTH = 12


def read_password() -> str:
    password = os.getenv("ACAS_ADMIN_PASSWORD")
    if password:
        return password
    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Password again: "):
        sys.exit("The passwords do not match.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin account.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if auth_service.get_user_by_username(db, args.username):
            sys.exit(f"The username {args.username} is already taken. Nothing was changed.")

        password = read_password()
        if len(password) < MIN_PASSWORD_LENGTH:
            sys.exit(f"The password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            sys.exit(f"The password must be at most {MAX_PASSWORD_BYTES} bytes.")

        auth_service.add_user(db, args.username, password, UserRole.admin, args.email)
        print(f"Created admin account: {args.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
