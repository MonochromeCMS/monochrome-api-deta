import asyncio

from os import getenv
from deta import Deta
from passlib.hash import bcrypt
from uuid import uuid4


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
        raise EnvironmentError("A DETA_PROJECT_KEY is required to add an admin user")

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
    }

    await db.put(user)
    await db.close()


asyncio.get_event_loop().run_until_complete(main())
