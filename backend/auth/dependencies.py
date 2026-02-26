"""Authentication dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt as jose_jwt, ExpiredSignatureError, JWTError

from backend.config import settings
from backend.models.schemas import CurrentUser

# HTTPBearer security scheme - extracts Bearer token from Authorization header
security = HTTPBearer(
    description="JWT token from Better Auth",
    auto_error=True  # Automatically return 401 if no token
)

_ALGORITHM = "HS256"
_CLOCK_SKEW_LEEWAY = 10  # seconds


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Verify JWT token using BETTER_AUTH_SECRET.

    This dependency:
    1. Extracts token from Authorization: Bearer <token> header
    2. Decodes and verifies the JWT signature with settings.jwt_secret
    3. Validates standard claims (exp, sub) with 10-second clock skew leeway
    4. Returns user info from token claims

    Raises:
        HTTPException: 401 Unauthorized for any verification failure
    """
    token = credentials.credentials

    try:
        payload = jose_jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[_ALGORITHM],
            options={"leeway": _CLOCK_SKEW_LEEWAY},
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email", ""),
    )


async def verify_user_owns_resource(
    user_id: str = Path(..., description="User ID from URL path"),
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Verify that the authenticated user matches the user_id in the URL path.

    This prevents users from accessing other users' resources (IDOR prevention).
    Returns 404 (not 403) to prevent information leakage about resource existence.
    """
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    return current_user
