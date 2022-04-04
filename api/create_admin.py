import asyncio
from logging import getLogger
from os import getenv
from uuid import uuid4

from deta import Deta
from passlib.hash import bcrypt

logger = getLogger(__name__)


async def main():
    PROJECT_KEY = getenv("DETA_PROJECT_KEY")

    if getenv("MONOCHROME_TEST"):
        USERNAME = "admin"
        PASSWORD = "pass"
        uuid = "c603ef4f-08f9-4130-a770-3a34defa44b3"
    else:
        USERNAME = input("Username: ")
        PASSWORD = input("Password: ")
        uuid = uuid4()

    if not PROJECT_KEY:
        raise OSError("A DETA_PROJECT_KEY is required to add an admin user")

    hashed_password = bcrypt.hash(PASSWORD)

    deta = Deta(PROJECT_KEY)
    db = deta.AsyncBase("users")

    user = {
        "username": USERNAME,
        "email": None,
        "hashed_password": hashed_password,
        "version": 1,
        "id": str(uuid),
        "key": str(uuid),
        "role": "admin",
    }

    await db.put(user)
    await db.close()


async def deta_init():
    PROJECT_KEY = getenv("DETA_PROJECT_KEY")

    if not PROJECT_KEY:
        raise OSError("A DETA_PROJECT_KEY is required to add the default admin user")

    deta = Deta(PROJECT_KEY)
    db_users = deta.AsyncBase("users")
    db_init = deta.AsyncBase("init")

    initialized = await db_init.get("initialized")

    user_id = uuid4()

    if initialized:
        await db_users.close()
        await db_init.close()
        return

    logger.info("First install, creating default user...")
    
    await db_init.put({"key":"initialized"})
    await db_init.close()

    user = {
        "username": "admin",
        "email": None,
        "hashed_password": bcrypt.hash("admin"),
        "version": 1,
        "id": str(user_id),
        "key": str(user_id),
        "role": "admin",
    }

    await db_users.put(user)
    await db_users.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
