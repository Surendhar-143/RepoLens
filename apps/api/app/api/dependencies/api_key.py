import hashlib
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.database.models import User, APIKey

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_user_from_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Authorize access tokens passed via header tags"""
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key header token credentials."
        )

    # Hash the header key to compare
    hashed_key = hashlib.sha256(api_key_header.encode()).hexdigest()

    # Query key and map user bounds
    query = select(APIKey).where(APIKey.key_hash == hashed_key)
    res = await db.execute(query)
    api_key_record = res.scalar_one_or_none()
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key credentials."
        )

    # Fetch mapping developer
    user_query = select(User).where(User.id == api_key_record.user_id)
    user_res = await db.execute(user_query)
    user = user_res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Developer account mapped to API Key not found."
        )

    return user
