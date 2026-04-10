"""
=============================================================================
DATABASE.PY - Data Storage Layer
=============================================================================

This is a SIMPLIFIED in-memory database for learning purposes.
Data is stored in Python dictionaries and LOST when the server restarts.

IN PRODUCTION, you would replace this with:
- PostgreSQL + SQLAlchemy (most common)
- MongoDB + Motor (for document databases)
- SQLite (for small apps or prototyping)

WHY SEPARATE THIS FILE?
This is the "Repository Pattern" - isolating data access:
1. Routers don't know HOW data is stored (dict? SQL? MongoDB?)
2. You can swap databases without changing router code
3. Easier to test - mock the database in tests

PATTERN: In production, this would be a class like:
    class UserRepository:
        def get_all(self) -> list[User]: ...
        def get_by_id(self, id: int) -> User | None: ...
        def create(self, user: UserCreate) -> User: ...
        def update(self, id: int, user: UserCreate) -> User: ...
        def delete(self, id: int) -> bool: ...
=============================================================================
"""

# -----------------------------------------------------------------------------
# IN-MEMORY "DATABASE"
# -----------------------------------------------------------------------------
# users_db: Dictionary storing users, keyed by user ID
# Structure: { 1: {"id": 1, "name": "John", "email": "john@example.com"}, ... }
#
# Type hint dict[int, dict] means:
#   - Keys are integers (user IDs)
#   - Values are dictionaries (user data)
users_db: dict[int, dict] = {}
pharmacies_db : dict[int, dict] = {}

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$V2l/SOPyl1ztNhwL4m/E0Q$3TI/nDMBOHDRsbwkK3pVQhfPkkyFosDIRse38HLpINc",
        "disabled": True,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$8ms1QajIh3I2FPNXFYvOvQ$71fmg4O7WD8xc5Jg7Hhyjqux7ytwlI1TT13IoU50N6k",
        "disabled": False,
    },
}

# user_id_counter: Auto-incrementing ID generator
# In SQL databases, this is handled by AUTO_INCREMENT or SERIAL
# Every time we create a user, we increment this
user_id_counter = 1
pharmacy_id_counter = 1
