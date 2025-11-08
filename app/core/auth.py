from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from supabase import create_client, Client

from app.core.config import settings

security = HTTPBearer()

def get_supabase_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    if not credentials:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            options={"verify_signature": False}
        )
        return payload.get("sub")
    except:
        return None