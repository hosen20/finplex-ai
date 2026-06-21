import os
from typing import Any

import streamlit as st
from finplex_admin.client import AdminApiError, FinplexAdminClient

DEFAULT_API_URL = "http://localhost:8000"
TENANT_USER_ROLES = ["tenant_admin", "manager", "reviewer", "auditor"]


st.set_page_config(
    page_title="Finplex AI Platform Admin",
    page_icon="🧾",
    layout="wide",
)


def get_api_url() -> str:
    return st.session_state.get(
        "api_url",
        os.getenv("FINPLEX_API_URL", DEFAULT_API_URL),
    )


def get_client() -> FinplexAdminClient:
    return FinplexAdminClient(
        base_url=get_api_url(),
        access_token=st.session_state.get("access_token"),
    )


def login_screen() -> None:
    st.title("Finplex AI Platform Admin")
    st.caption("Create tenants and first tenant admins for the local product.")

    with st.form("platform-admin-login"):
        api_url = st.text_input("API URL", value=get_api_url())
        email = st.text_input("Platform admin email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if not submitted:
        st.info(
            "Bootstrap the first platform admin from the terminal before signing in."
        )
        st.code(
            "uv run --project services/api python scripts/bootstrap-platform-admin.py",
            language="bash",
        )
        return

    st.session_state["api_url"] = api_url.strip() or DEFAULT_API_URL
    client = FinplexAdminClient(base_url=st.session_state["api_url"])

    try:
        token = client.login(email=email.strip(), password=password)
        st.session_state["access_token"] = token["access_token"]
        user = get_client().me()
    except AdminApiError as exc:
        st.error(str(exc))
        return

    if user.get("role") != "platform_admin":
        st.session_state.pop("access_token", None)
        st.error("Only platform admins can use this admin console.")
        return

    st.session_state["current_user"] = user
    st.rerun()


def render_sidebar() -> str:
    user = st.session_state.get("current_user", {})
    st.sidebar.title("Finplex AI")
    st.sidebar.caption("Platform Admin")
    st.sidebar.write(user.get("email", ""))

    page = st.sidebar.radio(
        "Navigation",
        [
            "System Overview",
            "Tenants",
            "Create Tenant",
            "Create User",
            "Users by Tenant",
        ],
    )

    if st.sidebar.button("Sign out"):
        st.session_state.clear()
        st.rerun()

    return page


def tenants_by_name(tenants: list[dict[str, Any]]) -> dict[str, str]:
    return {
        f"{tenant['name']} ({tenant['tenant_id']})": tenant["tenant_id"]
        for tenant in tenants
    }


def system_overview(client: FinplexAdminClient) -> None:
    st.header("System Overview")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("API Health")
        try:
            st.json(client.health())
        except AdminApiError as exc:
            st.error(str(exc))

    with col2:
        st.subheader("Readiness")
        try:
            readiness = client.readiness()
            redacted = dict(readiness)
            if "database_url" in redacted:
                redacted["database_url"] = "configured"
            st.json(redacted)
        except AdminApiError as exc:
            st.error(str(exc))

    st.subheader("Tenant Summary")
    try:
        tenants = client.list_tenants()
    except AdminApiError as exc:
        st.error(str(exc))
        return

    active_count = sum(1 for tenant in tenants if tenant["status"] == "active")
    suspended_count = sum(1 for tenant in tenants if tenant["status"] == "suspended")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total tenants", len(tenants))
    metric_col2.metric("Active tenants", active_count)
    metric_col3.metric("Suspended tenants", suspended_count)


def tenant_table(client: FinplexAdminClient) -> None:
    st.header("Tenants")

    try:
        tenants = client.list_tenants()
    except AdminApiError as exc:
        st.error(str(exc))
        return

    if not tenants:
        st.info("No tenants have been created yet.")
        return

    st.dataframe(tenants, use_container_width=True, hide_index=True)

    st.subheader("Change tenant status")
    options = tenants_by_name(tenants)
    selected = st.selectbox("Tenant", list(options))
    target_status = st.radio("Status", ["active", "suspended"], horizontal=True)

    if st.button("Apply status change"):
        try:
            updated = client.set_tenant_status(
                tenant_id=options[selected],
                status=target_status,
            )
        except AdminApiError as exc:
            st.error(str(exc))
            return
        st.success(f"Tenant status updated to {updated['status']}.")
        st.rerun()


def create_tenant_form(client: FinplexAdminClient) -> None:
    st.header("Create Tenant")

    with st.form("create-tenant"):
        name = st.text_input("Company / tenant name")
        erp_provider = st.text_input("ERP provider", value="local")
        crm_provider = st.text_input("CRM provider", value="local")
        submitted = st.form_submit_button("Create tenant")

    if not submitted:
        return

    try:
        tenant = client.create_tenant(
            name=name.strip(),
            erp_provider=erp_provider.strip() or "local",
            crm_provider=crm_provider.strip() or "local",
        )
    except AdminApiError as exc:
        st.error(str(exc))
        return

    st.success("Tenant created.")
    st.json(tenant)


def create_user_form(client: FinplexAdminClient) -> None:
    st.header("Create User")
    st.caption("Use this to create the first tenant admin or later tenant users.")

    try:
        tenants = client.list_tenants()
    except AdminApiError as exc:
        st.error(str(exc))
        return

    if not tenants:
        st.info("Create a tenant before creating users.")
        return

    options = tenants_by_name(tenants)

    with st.form("create-user"):
        selected_tenant = st.selectbox("Tenant", list(options))
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        role = st.selectbox("Role", TENANT_USER_ROLES)
        password = st.text_input("Temporary password", type="password")
        submitted = st.form_submit_button("Create user")

    if not submitted:
        return

    try:
        user = client.create_user(
            tenant_id=options[selected_tenant],
            email=email.strip(),
            full_name=full_name.strip(),
            password=password,
            role=role,
        )
    except AdminApiError as exc:
        st.error(str(exc))
        return

    st.success(f"Created {user['role']} user: {user['email']}")
    st.json(user)


def users_by_tenant(client: FinplexAdminClient) -> None:
    st.header("Users by Tenant")

    try:
        tenants = client.list_tenants()
    except AdminApiError as exc:
        st.error(str(exc))
        return

    if not tenants:
        st.info("No tenants found.")
        return

    options = tenants_by_name(tenants)
    selected_tenant = st.selectbox("Tenant", list(options))

    try:
        users = client.list_users(tenant_id=options[selected_tenant])
    except AdminApiError as exc:
        st.error(str(exc))
        return

    if not users:
        st.info("This tenant has no users yet.")
        return

    st.dataframe(users, use_container_width=True, hide_index=True)


def main() -> None:
    if "access_token" not in st.session_state:
        login_screen()
        return

    client = get_client()
    page = render_sidebar()

    if page == "System Overview":
        system_overview(client)
    elif page == "Tenants":
        tenant_table(client)
    elif page == "Create Tenant":
        create_tenant_form(client)
    elif page == "Create User":
        create_user_form(client)
    elif page == "Users by Tenant":
        users_by_tenant(client)


if __name__ == "__main__":
    main()
