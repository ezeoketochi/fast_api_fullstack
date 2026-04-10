"""
=============================================================================
MODELS.PY - Pydantic Models (Data Validation & Serialization)
=============================================================================

Pydantic models define the SHAPE of your data. They serve multiple purposes:
1. INPUT VALIDATION  - Automatically validate incoming request data
2. OUTPUT SERIALIZATION - Control what gets sent back to the client
3. DOCUMENTATION - Auto-generate OpenAPI schema (visible at /docs)
4. TYPE SAFETY - IDE autocomplete and type checking

FRONTEND CONNECTION:
These models mirror the TypeScript interfaces in frontend/src/types.ts
When you change a model here, update types.ts to match!

KEY PATTERN:
- UserCreate = what the client SENDS (no id - server generates it)
- User = what the server RETURNS (includes id)
This separation is called "Input/Output DTOs" (Data Transfer Objects)
=============================================================================
"""

from pydantic import BaseModel, EmailStr


# -----------------------------------------------------------------------------
# UserCreate - Used for CREATE and UPDATE operations
# -----------------------------------------------------------------------------
# This is what the frontend sends when creating or updating a user.
# Notice: NO id field - the server assigns IDs, not the client.
#
# FRONTEND USAGE (see frontend/src/api/users.ts):
#   fetch('/api/users', {
#     method: 'POST',
#     body: JSON.stringify({ name: "John", email: "john@example.com" })
#   })
#
# VALIDATION:
# - name: str → must be a string (Pydantic rejects numbers, nulls, etc.)
# - email: EmailStr → must be valid email format (Pydantic validates this!)
#   Invalid emails like "notanemail" will return 422 Unprocessable Entity
class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Built-in email validation! Try sending "bad" - it fails

class PharmacyCreate(BaseModel):
    name: str
    address: str
    phone_number: str
# -----------------------------------------------------------------------------
# User - Used for READ operations (responses)
# -----------------------------------------------------------------------------
# This is what the frontend RECEIVES from the API.
# Inherits from UserCreate (gets name, email) and adds id.
#
# WHY INHERIT?
# - DRY (Don't Repeat Yourself) - name and email defined once
# - If you add a field to UserCreate, User automatically gets it
#
# FRONTEND CONNECTION:
# This matches the User interface in frontend/src/types.ts:
#   interface User { id: number; name: string; email: string; }
class User(UserCreate):
    id: int  # Server-generated, auto-incrementing (see database.py)

class Pharmacy(PharmacyCreate):
    id: int

class User(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class TokenData(BaseModel):
    username: str | None = None
    scopes : list[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str