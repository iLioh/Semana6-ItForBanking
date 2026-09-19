"""Validacion de tokens Microsoft Entra ID y autorizacion por roles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from src.app.config import AppSettings, get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    object_id: str
    roles: frozenset[str]
    scopes: frozenset[str]


def _decode_token(token: str, settings: AppSettings) -> dict:
    jwks_url = f"https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys"
    signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.entra_audience,
        issuer=settings.entra_issuer,
        options={"require": ["exp", "iss", "aud"]},
    )


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> Principal:
    if not settings.auth_required:
        return Principal("local-developer", frozenset({"Analyst", "Reviewer"}), frozenset())
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere token de Microsoft Entra ID")
    try:
        claims = _decode_token(credentials.credentials, settings)
    except jwt.PyJWTError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido o vencido") from error
    scopes = frozenset(str(claims.get("scp", "")).split())
    roles = frozenset(claims.get("roles", []))
    if settings.entra_required_scope not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Scope insuficiente")
    return Principal(str(claims.get("oid", "unknown")), roles, scopes)


def require_roles(*allowed: str):
    def dependency(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
        if principal.roles.isdisjoint(allowed):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Rol insuficiente")
        return principal

    return dependency
