# Tenant Isolation Policy

Every tenant-owned record must be scoped by `tenant_id`. Users should only access data that belongs to their authenticated tenant unless they are platform administrators performing platform operations.

Database queries, file paths, Kafka events, vector records, review records, and audit events should preserve tenant scope. Cross-tenant access must be blocked and tested.
