from uuid import UUID

from api.tests.unit.utils import BaseModelTest
from api.tests.unit.test_schemas_base import TestPaginationResponse

import api.schemas.user as sch


class TestTokenResponse(BaseModelTest):
    schema = sch.TokenResponse
    example_data = {
        "access_token": "ThisIsAToken",
        "refresh_token": "ThisIsAlsoToken",
        "token_type": "bearer",
    }
    wrong_data = [
        # Missing fields
        {
            "refresh_token": "ThisIsAlsoToken",
            "token_type": "bearer",
        },
        {
            "access_token": "ThisIsAToken",
            "token_type": "bearer",
        },
        # Constant
        {
            "access_token": "ThisIsAToken",
            "refresh_token": "ThisIsAlsoToken",
            "token_type": "NotBearer",
        },
    ]
    irregular_data = [
        # Default values
        {
            "access_token": "ThisIsAToken",
            "refresh_token": "ThisIsAlsoToken",
        }
    ]


class TestUser(BaseModelTest):
    schema = sch.User
    example_data = {
        "username": "user",
        "email": "user@example.com",
    }
    correct_data = [
        {
            "username": "user",
            "email": None,
        }
    ]
    wrong_data = [
        # Missing fields
        {
            "email": "user@example.com",
        },
        # Max username length
        {
            "username": "userAbove15Characters",
            "email": "user@example.com",
        },
        # Bad email
        {
            "username": "user",
            "email": "NotAnEm@il",
        },
    ]


class TestUserRegisterSchema(BaseModelTest):
    schema = sch.UserRegisterSchema
    parent = TestUser
    example_data = {
        **parent.example_data,
        "password": "password",
    }
    wrong_data = [
        # Missing fields
        {}
    ]


class TestUserSchema(BaseModelTest):
    schema = sch.UserSchema
    parent = TestUserRegisterSchema
    example_data = {
        **parent.example_data,
        "role": "uploader",
    }
    wrong_data = [
        # Missing fields
        {},
        # Value not in enum
        {
            "role": "RandomRoleThatDoesntExist",
        },
    ]


class TestUserResponse(BaseModelTest):
    schema = sch.UserResponse
    parent = TestUser
    example_data = {
        **parent.example_data,
        "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
        "version": 2,
        "role": "uploader",
    }
    wrong_data = [
        # Missing fields
        {
            "version": 2,
            "role": "uploader",
        },
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "role": "uploader",
        },
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "version": 2,
        },
        # Value not in enum
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "version": 2,
            "role": "RandomRoleThatDoesntExist",
        },
    ]
    irregular_data = [
        # String to uuid
        {
            "id": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
            "version": 2,
            "role": "uploader",
        },
        # String to int
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "version": "2",
            "role": "uploader",
        },
    ]


class TestUsersResponse(BaseModelTest):
    schema = sch.UsersResponse
    parent = TestPaginationResponse
    example_data = {**parent.example_data, "results": [TestUserResponse.example_data]}


class TestUserFilters(BaseModelTest):
    schema = sch.UserFilters
    example_data = {
        "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
        "email": "user@example.com",
        "role": "uploader",
    }
    correct_data = [
        {
            "id": None,
            "email": "user@example.com",
            "role": "uploader",
        },
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "email": None,
            "role": "uploader",
        },
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "email": "user@example.com",
            "role": None,
        },
    ]
    wrong_data = [
        # Bad email
        {
            "id": UUID("6901d7f6-c4e1-4200-9dd0-a6fccc065978"),
            "email": "NotAnEm@il",
            "role": "uploader",
        },
    ]
    irregular_data = [
        # String to uuid
        {
            "id": "6901d7f6-c4e1-4200-9dd0-a6fccc065978",
            "email": "user@example.com",
            "role": "uploader",
        },
    ]
