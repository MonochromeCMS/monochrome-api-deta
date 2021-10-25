from typing import ClassVar, List, Union, Callable
from pydantic import BaseModel, Field
from math import inf
from contextlib import asynccontextmanager
from aiohttp import ClientError
from uuid import UUID, uuid4
from fastapi.encoders import jsonable_encoder

from ..db import deta
from ..config import get_settings
from ..exceptions import UnprocessableEntityHTTPException, NotFoundHTTPException

settings = get_settings()


@asynccontextmanager
async def async_client(db_name: str):
    client = deta.AsyncBase(db_name)
    try:
        yield client
    except ClientError:
        UnprocessableEntityHTTPException("Database error")
    finally:
        await client.close()


class DetaBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    version: int = 1
    db_name: ClassVar

    def dict(self, *args, **kwargs):
        return {**super().dict(*args, **kwargs), "key": str(self.id)}

    async def save(self):
        async with async_client(self.db_name) as db:
            self.version += 1
            await db.put(jsonable_encoder(self))

    async def delete(self):
        async with async_client(self.db_name) as db:
            await db.delete(str(self.id))
        return "OK"

    async def update(self, **kwargs):
        async with async_client(self.db_name) as db:
            new_version = self.version + 1
            new_dict = {**self.dict(), **kwargs, "version": new_version}
            new_instance = self.__class__(**new_dict)
            await db.put(jsonable_encoder(new_instance))

            self.__dict__.update(new_instance.__dict__)

    @staticmethod
    async def delete_many(instances: List["DetaBase"]):
        for instance in instances:
            await instance.delete()

    @classmethod
    async def find(cls, _id: Union[UUID, str], exception=NotFoundHTTPException()):
        async with async_client(cls.db_name) as db:
            instance = await db.get(str(_id))
            if instance is None and exception:
                raise exception
            elif instance:
                return cls(**instance)
            else:
                return None

    @classmethod
    async def fetch(cls, query, limit: int = inf):
        async with async_client(cls.db_name) as db:
            query = jsonable_encoder(query)
            res = await db.fetch(query, limit=min(limit, settings.max_page_limit))
            all_items = res.items

            while len(all_items) <= limit and res.last:
                res = await db.fetch(query, last=res.last)
                all_items += res.items

            return [cls(**instance) for instance in all_items]

    @classmethod
    async def pagination(cls, query, limit: int, offset: int, order_by: Callable[["DetaBase"], str], reverse=False):
        if query is None:
            query = dict()
        results = await cls.fetch(query, limit + offset + 5)
        count = len(results)
        top = limit + offset
        page = sorted(results, key=order_by, reverse=reverse)[offset:top]
        return count, page
