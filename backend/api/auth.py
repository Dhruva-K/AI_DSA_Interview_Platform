from fastapi import APIRouter, HTTPException, status

from backend.models.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.services.auth import create_token, hash_password, verify_password
from backend.services.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    async with get_db() as db:
        row = await db.execute("SELECT id FROM users WHERE email = ?", (body.email,))
        if await row.fetchone():
            raise HTTPException(status_code=409, detail="Email already registered")
        row = await db.execute("SELECT id FROM users WHERE username = ?", (body.username,))
        if await row.fetchone():
            raise HTTPException(status_code=409, detail="Username already taken")

        cursor = await db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (body.username, body.email, hash_password(body.password)),
        )
        await db.commit()
        user_id = cursor.lastrowid

    return TokenResponse(
        token=create_token(user_id, body.username),
        user_id=user_id,
        username=body.username,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    async with get_db() as db:
        row = await db.execute(
            "SELECT id, username, password_hash FROM users WHERE email = ?", (body.email,)
        )
        user = await row.fetchone()

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(
        token=create_token(user["id"], user["username"]),
        user_id=user["id"],
        username=user["username"],
    )
