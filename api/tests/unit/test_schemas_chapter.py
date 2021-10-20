from datetime import datetime
from uuid import UUID

from api.tests.unit.utils import BaseModelTest
from api.tests.unit.test_schemas_base import TestPaginationResponse
from api.tests.unit.test_schemas_manga import TestMangaResponse

import api.schemas.chapter as sch


class TestChapterSchema(BaseModelTest):
    schema = sch.ChapterSchema
    example_data = {
        "name": "A World That Won't Reject Me",
        "volume": 1,
        "number": 19.5,
        "scan_group": "no group",
        "webtoon": True,
    }
    correct_data = [
        {
            "name": "A World That Won't Reject Me",
            "number": 19.5,
            "volume": None,
            "scan_group": "no group",
            "webtoon": True,
        }
    ]
    wrong_data = [
        # Missing fields
        {
            "volume": 1,
            "number": 19.5,
            "scan_group": "no group",
            "webtoon": True,
        },
        {
            "name": "A World That Won't Reject Me",
            "volume": 1,
            "scan_group": "no group",
            "webtoon": True,
        },
        {
            "name": "A World That Won't Reject Me",
            "volume": 1,
            "number": 19.5,
            "scan_group": "no group",
        },
    ]
    irregular_data = [
        # String to bool
        {
            "name": "A World That Won't Reject Me",
            "volume": 1,
            "number": 19.5,
            "scan_group": "no group",
            "webtoon": "t",
        },
        # String to number
        {
            "name": "A World That Won't Reject Me",
            "volume": "1",
            "number": 19.5,
            "scan_group": "no group",
            "webtoon": True,
        },
        {
            "name": "A World That Won't Reject Me",
            "volume": 1,
            "number": "19.5",
            "scan_group": "no group",
            "webtoon": True,
        },
        # Default values
        {
            "name": "A World That Won't Reject Me",
            "volume": 1,
            "number": "19.5",
            "webtoon": True,
        },
    ]


class TestChapterResponse(BaseModelTest):
    schema = sch.ChapterResponse
    parent = TestChapterSchema
    example_data = {
        **parent.example_data,
        "length": 15,
        "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
        "version": 2,
        "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
        "upload_time": datetime(2000, 8, 24),
        "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
    }
    wrong_data = [
        # Missing fields
        {
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
    ]
    irregular_data = [
        # String to number
        {
            "length": "15",
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": "2",
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        # String to UUID
        {
            "length": 15,
            "manga_id": "1e01d7f6-c4e1-4102-9dd0-a6fccc065978",
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": datetime(2000, 8, 24),
            "owner_id": "3f01d7dd-c4e1-4102-9dd0-a6fccc065978",
        },
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": "4abe53f4-0eaa-4f31-9210-a625fa665e23",
            "upload_time": datetime(2000, 8, 24),
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
        # String to datetime
        {
            "length": 15,
            "manga_id": UUID("1e01d7f6-c4e1-4102-9dd0-a6fccc065978"),
            "version": 2,
            "id": UUID("4abe53f4-0eaa-4f31-9210-a625fa665e23"),
            "upload_time": "2000-08-24 00:00:00",
            "owner_id": UUID("3f01d7dd-c4e1-4102-9dd0-a6fccc065978"),
        },
    ]


class TestDetailedChapterResponse(BaseModelTest):
    schema = sch.DetailedChapterResponse
    parent = TestChapterResponse
    example_data = {**parent.example_data, "manga": TestMangaResponse.example_data}


class TestLatestChaptersResponse(BaseModelTest):
    schema = sch.LatestChaptersResponse
    parent = TestPaginationResponse
    example_data = {**parent.example_data, "results": [TestDetailedChapterResponse.example_data]}
