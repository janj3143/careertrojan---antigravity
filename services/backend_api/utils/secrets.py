"""
Docker Secrets helper — reads secrets from /run/secrets/<name> (Docker)
or falls back to environment variables for local dev.

Usage:
    from services.backend_api.utils.secrets import get_secret
    jwt_key = get_secret("secret_key", env_fallback="SECRET_KEY")
"""

import os
import logging

logger = logging.getLogger("secrets")

SECRETS_DIR = os.getenv("SECRETS_DIR", "/run/secrets")


def get_secret(
    name: str,
    *,
    env_fallback: str | None = None,
    default: str | None = None,
) -> str | None:
    """
    Read a secret value.

    Priority:
      1. Docker secret file at ``SECRETS_DIR/<name>``
      2. Environment variable ``env_fallback``
      3. ``default`` value

    Returns ``None`` if nothing matched and no default given.
    """
    # 1. Docker secret file
    secret_path = os.path.join(SECRETS_DIR, name)
    if os.path.isfile(secret_path):
        try:
            with open(secret_path, "r") as f:
                value = f.read().strip()
            if value:
                logger.debug("Secret '%s' loaded from file", name)
                return value
        except OSError as exc:
            logger.warning("Could not read secret file %s: %s", secret_path, exc)

    # 2. Env-var fallback
    if env_fallback:
        env_value = os.getenv(env_fallback)
        if env_value is not None:
            logger.debug("Secret '%s' loaded from env var %s", name, env_fallback)
            return env_value

    # 3. Default
    if default is not None:
        logger.debug("Secret '%s' using default value", name)
        return default

    return None
