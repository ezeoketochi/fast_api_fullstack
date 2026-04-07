"""
=============================================================================
ROUTERS/USERS.PY - User CRUD Endpoints
=============================================================================

This file defines all API endpoints for the "users" resource.
It implements the standard REST CRUD operations:

| Operation | HTTP Method | Endpoint         | Frontend Function      |
|-----------|-------------|------------------|------------------------|
| Create    | POST        | /api/users       | createUser()           |
| Read All  | GET         | /api/users       | getUsers()             |
| Read One  | GET         | /api/users/{id}  | getUser()              |
| Update    | PUT         | /api/users/{id}  | updateUser()           |
| Delete    | DELETE      | /api/users/{id}  | deleteUser()           |

FRONTEND CONNECTION:
Each endpoint here has a matching function in frontend/src/api/users.ts
The frontend calls these endpoints using fetch().

KEY CONCEPTS:
1. APIRouter groups related endpoints
2. Path parameters like {user_id} are extracted automatically
3. Request body is validated against Pydantic models
4. response_model controls what gets returned to the client
5. HTTPException returns error responses (404, 400, etc.)
=============================================================================
"""

from fastapi import APIRouter, HTTPException
from models import Pharmacy, PharmacyCreate
import database as db

# -----------------------------------------------------------------------------
# CREATE THE ROUTER
# -----------------------------------------------------------------------------
# APIRouter is like a "mini FastAPI app" that gets mounted to the main app.
# In main.py, this router is mounted at /api/users
router = APIRouter()


# -----------------------------------------------------------------------------
# GET /api/users - List all users (READ)
# -----------------------------------------------------------------------------
# FRONTEND: Called by getUsers() in frontend/src/api/users.ts
# REACT: Used in loadUsers() in App.tsx to populate the user list
#
# response_model=list[Pharmacy] does two things:
# 1. VALIDATION: Ensures response matches the Pharmacy model
# 2. DOCUMENTATION: Shows response schema in /docs
#
# HTTP Response: 200 OK with JSON array
# Example: [{"id": 1, "name": "John", "email": "john@example.com"}]
@router.get("/", response_model=list[Pharmacy])
def get_pharmacies():
    # dict.values() returns all pharmacies, list() converts to array for JSON
    return list(db.pharmacies_db.values())


# -----------------------------------------------------------------------------
# GET /api/pharmacies/{pharmacy_id} - Get single pharmacy (READ)
# -----------------------------------------------------------------------------
# FRONTEND: Called by getPharmacy(id) in frontend/src/api/pharmacies.ts
#
# PATH PARAMETER: {pharmacy_id} in the URL becomes a function argument
# FastAPI automatically converts "123" (string) to 123 (int)
#
# HTTP Responses:
#   200 OK - Pharmacy found, returns pharmacy data
#   404 Not Found - Pharmacy doesn't exist
@router.get("/{pharmacy_id}", response_model=Pharmacy)
def get_pharmacy(pharmacy_id: int):
    # Check if pharmacy exists; if not, return 404
    if pharmacy_id not in db.pharmacies_db:
        # HTTPException stops execution and returns error response
        # Frontend catches this in the try/catch block
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    return db.pharmacies_db[pharmacy_id]


# -----------------------------------------------------------------------------
# POST /api/users - Create new user (CREATE)
# -----------------------------------------------------------------------------
# FRONTEND: Called by createUser(user) in frontend/src/api/users.ts
# REACT: Triggered by handleCreate() when form is submitted
#
# REQUEST BODY: FastAPI automatically parses JSON body into UserCreate model
# If validation fails (bad email, missing fields), returns 422 Unprocessable Entity
#
# status_code=201 indicates "Created" (not default 200 "OK")
# This is REST convention for successful creation
#
# HTTP Responses:
#   201 Created - User created successfully, returns new user with ID
#   422 Unprocessable Entity - Validation failed (bad email, missing fields)
@router.post("/", response_model=Pharmacy, status_code=201)
def create_pharmacy(pharmacy: PharmacyCreate):
    print("=" * 50)
    print("5. BACKEND: create_pharmacy() endpoint hit")
    print(f"   Received data: {pharmacy}")
    print(f"   Will assign ID: {db.pharmacy_id_counter}")
    # Access the global counter to assign new ID
    # In SQL: INSERT INTO users (name, email) VALUES (...) RETURNING id
    global pharmacy_id_counter  # Needed to modify module-level variable

    # Create pharmacy dict with server-generated ID
    # pharmacy.dict() converts Pydantic model to dictionary
    # ** unpacks: {"name": "John", "email": "john@example.com"}
    new_pharmacy = {"id": db.pharmacy_id_counter, **pharmacy.model_dump()}
    print(f"6. BACKEND: Created pharmacy dict: {new_pharmacy}")

    # Store in "database"
    db.pharmacies_db[db.pharmacy_id_counter] = new_pharmacy
    print(f"7. BACKEND: Stored in database. DB now has {len(db.pharmacies_db)} pharmacy(s)")

    # Increment for next pharmacy
    db.pharmacy_id_counter += 1

    # Return created pharmacy (with ID) - frontend uses this to update UI
    print(f"8. BACKEND: Returning new_pharmacy to frontend")
    print("=" * 50)
    return new_pharmacy


# -----------------------------------------------------------------------------
# PUT /api/users/{user_id} - Update existing user (UPDATE)
# -----------------------------------------------------------------------------
# FRONTEND: Called by updateUser(id, user) in frontend/src/api/users.ts
# REACT: Triggered by handleUpdate() when editing form is submitted
#
# COMBINES: Path parameter (user_id) + Request body (user: UserCreate)
# FastAPI handles both automatically
#
# HTTP Responses:
#   200 OK - User updated successfully, returns updated user
#   404 Not Found - User doesn't exist
#   422 Unprocessable Entity - Validation failed
@router.put("/{pharmacy_id}", response_model=Pharmacy)
def update_pharmacy(pharmacy_id: int, pharmacy: PharmacyCreate):
    # Can't update a pharmacy that doesn't exist
    if pharmacy_id not in db.pharmacies_db:
        raise HTTPException(status_code=404, detail="Pharmacy not found")

    # Replace entire pharmacy record (keeping the same ID)
    # In SQL: UPDATE pharmacies SET name=?, email=? WHERE id=?
    db.pharmacies_db[pharmacy_id] = {"id": pharmacy_id, **pharmacy.model_dump()}

    return db.pharmacies_db[pharmacy_id]


# -----------------------------------------------------------------------------
# DELETE /api/pharmacies/{pharmacy_id} - Delete pharmacy (DELETE)
# -----------------------------------------------------------------------------
# FRONTEND: Called by deletePharmacy(id) in frontend/src/api/pharmacies.ts
# REACT: Triggered by handleDelete() when Delete button is clicked
#
# status_code=204 means "No Content" - success but nothing to return
# This is REST convention for successful deletion
#
# HTTP Responses:
#   204 No Content - Pharmacy deleted successfully (empty response body)
#   404 Not Found - Pharmacy doesn't exist
@router.delete("/{pharmacy_id}", status_code=204)
def delete_pharmacy(pharmacy_id: int):
    if pharmacy_id not in db.pharmacies_db:
        raise HTTPException(status_code=404, detail="Pharmacy not found")

    # Remove from "database"
    # In SQL: DELETE FROM pharmacies WHERE id=?
    del db.pharmacies_db[pharmacy_id]
    # No return statement = empty response body (204 No Content)


@router.delete("/", status_code=204)
def delete_all_pharmacies():
    if not db.pharmacies_db:
        raise HTTPException(status_code=404, detail="No pharmacies to delete")
    db.pharmacies_db.clear()