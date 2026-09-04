import os
import sys
from pathlib import Path
import pytest

# Ensure backend paths are on sys.path
BACKEND_APP = Path(__file__).resolve().parent.parent / "backend" / "app"
if str(BACKEND_APP) not in sys.path:
    sys.path.insert(0, str(BACKEND_APP))

from main import validate_production_secrets, INSECURE_SECRET_KEYS


def test_development_mode_bypasses_strict_secrets(monkeypatch):
    """Development mode must not block startup with default dev keys."""
    monkeypatch.setenv("SECUROX_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "dev-key")
    # Should not raise
    validate_production_secrets()


def test_production_mode_fails_when_secret_key_missing(monkeypatch):
    """Production mode must fail safely when SECRET_KEY is missing."""
    monkeypatch.setenv("SECUROX_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secrets()
    assert "SECRET_KEY environment variable is missing or empty" in str(exc_info.value)


def test_production_mode_fails_when_secret_key_too_short(monkeypatch):
    """Production mode must fail safely when SECRET_KEY is under 32 characters."""
    monkeypatch.setenv("SECUROX_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "too-short-secret")
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secrets()
    assert "SECRET_KEY is too short" in str(exc_info.value)


def test_production_mode_fails_when_secret_key_is_insecure_default(monkeypatch):
    """Production mode must fail safely when SECRET_KEY matches known default placeholders."""
    monkeypatch.setenv("SECUROX_ENV", "production")
    for insecure_key in INSECURE_SECRET_KEYS:
        monkeypatch.setenv("SECRET_KEY", insecure_key)
        with pytest.raises(RuntimeError) as exc_info:
            validate_production_secrets()
        assert "SECRET_KEY is set to a known insecure default placeholder" in str(exc_info.value)


def test_production_mode_fails_when_database_password_insecure(monkeypatch):
    """Production mode must fail safely when database password is an insecure placeholder."""
    monkeypatch.setenv("SECUROX_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "c79f9d22b27a3e746e50ef1295b9317208d132c3f81e358b68832a890a88fb0e")
    monkeypatch.setenv("DATABASE_URL", "postgresql://securox_user:postgres@securox-db:5432/securox")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_secrets()
    assert "POSTGRES_PASSWORD is set to an insecure default placeholder" in str(exc_info.value)


def test_production_mode_passes_with_cryptographically_strong_secrets(monkeypatch):
    """Production mode must succeed when all secrets meet cryptographic requirements."""
    monkeypatch.setenv("SECUROX_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "c79f9d22b27a3e746e50ef1295b9317208d132c3f81e358b68832a890a88fb0e")
    monkeypatch.setenv("DATABASE_URL", "postgresql://securox_user:k9#XmP8$vL2@qR5!wZ@securox-db:5432/securox")
    monkeypatch.setenv("POSTGRES_PASSWORD", "k9#XmP8$vL2@qR5!wZ")
    monkeypatch.setenv("REDIS_PASSWORD", "m3*WbQ7&tN9#yP1$kF")
    # Should not raise
    validate_production_secrets()
