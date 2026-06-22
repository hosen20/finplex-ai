# Secrets Handling Policy

Secrets must not be committed to the repository. Local credentials belong in `.env` files or local environment variables.

The repository includes a secret-check script to catch obvious committed secrets before pull requests are merged.
