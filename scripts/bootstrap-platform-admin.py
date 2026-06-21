#!/usr/bin/env python3
# ruff: noqa: E402, I001
"""Create or update the first local platform admin for Finplex AI.

This is intentionally a CLI-only bootstrap. The React product has no public
signup, and tenant creation happens from the Streamlit Platform Admin app after
this admin user signs in.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
API_SERVICE_DIR = ROOT_DIR / "services" / "api"

if str(API_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_DIR))

from app.database import SessionLocal  # noqa: E402
from app.domain.enums import TenantStatus, UserRole  # noqa: E402
from app.infrastructure.db.models.tenant_model import TenantModel  # noqa: E402
from app.infrastructure.db.models.user_model import UserModel  # noqa: E402
from app.infrastructure.db.repositories.tenant_repository import (
    TenantRepository,  # noqa: E402
)
from app.infrastructure.db.repositories.user_repository import (
    UserRepository,  # noqa: E402
)
from app.security import hash_password  # noqa: E402

PLATFORM_TENANT_ID = "tenant_platform"
PLATFORM_TENANT_NAME = "Finplex Platform Operations"
PLATFORM_ADMIN_USER_ID = "user_platform_admin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update the local Finplex platform admin account."
    )
    parser.add_argument(
        "--email",
        default=os.getenv(
            "FINPLEX_PLATFORM_ADMIN_EMAIL",
            "platform.admin@finplexai.com",
        ),
        help="Platform admin email address.",
    )
    parser.add_argument(
        "--full-name",
        default=os.getenv(
            "FINPLEX_PLATFORM_ADMIN_NAME",
            "Finplex Platform Admin",
        ),
        help="Platform admin full name.",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("FINPLEX_PLATFORM_ADMIN_PASSWORD"),
        help="Platform admin password. If omitted, an interactive prompt is shown.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Platform admin password: ")

    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    with SessionLocal() as session:
        tenants = TenantRepository(session)
        users = UserRepository(session)

        platform_tenant = tenants.get(PLATFORM_TENANT_ID)
        if platform_tenant is None:
            platform_tenant = TenantModel(
                tenant_id=PLATFORM_TENANT_ID,
                name=PLATFORM_TENANT_NAME,
                status=TenantStatus.ACTIVE,
                erp_provider="internal",
                crm_provider="internal",
            )
            tenants.add(platform_tenant)

        existing_by_email = users.get_by_email(args.email)
        existing_by_id = users.get(PLATFORM_ADMIN_USER_ID)

        if (
            existing_by_email is not None
            and existing_by_email.user_id != PLATFORM_ADMIN_USER_ID
        ):
            raise SystemExit(
                f"Email already belongs to another user: {args.email}"
            )

        if existing_by_id is not None:
            existing_by_id.tenant_id = PLATFORM_TENANT_ID
            existing_by_id.email = args.email
            existing_by_id.full_name = args.full_name
            existing_by_id.hashed_password = hash_password(password)
            existing_by_id.role = UserRole.PLATFORM_ADMIN
            existing_by_id.is_active = True
            session.commit()

            print("Platform admin updated.")
            print(f"Email: {args.email}")
            print("Open Streamlit admin at http://localhost:8501")
            return

        user = UserModel(
            user_id=PLATFORM_ADMIN_USER_ID,
            tenant_id=PLATFORM_TENANT_ID,
            email=args.email,
            full_name=args.full_name,
            hashed_password=hash_password(password),
            role=UserRole.PLATFORM_ADMIN,
            is_active=True,
        )
        users.add(user)
        session.commit()

    print("Platform admin created.")
    print(f"Email: {args.email}")
    print("Open Streamlit admin at http://localhost:8501")


if __name__ == "__main__":
    main()
