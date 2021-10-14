# Monochrome
Monochrome's API, implemented with a PostgreSQL backend and FS image storage.

Most users will prefer the Monochrome full stack, which contains the API, the frontend and the backend.

## Usage
### Docker
This service is available on ghcr.io:
```shell
docker pull ghcr.io/monochromecms/monochrome-api-postgres:latest
```
The database needs to be set up, and an admin user created:
```shell
docker run                                                          \
  -e DB_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres \
  ghcr.io/monochromecms/monochrome-api-postgres:latest              \
  create_admin
```
Once done, the image can be launched with the required [env. vars](#environment-variables):
```shell
docker run -p 3000:3000                                             \
  -e DB_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres \
  -e JWT_SECRET_KEY=changeMe                                        \
  -v "$(pwd)/media:/media"                                          \
  ghcr.io/monochromecms/monochrome-api-postgres:latest
```
*The images will be saved in the media_path, so a volume is highly recommended.*
### Makefile
A Makefile is provided with this repository, to simplify the development and usage:
```
help                 Show this help message
up start             Run a container from the image, or start it natively
# Docker utils
build                Build image
up-db                Start a db container
down-db              Stop the db container
logs                 Read the container's logs
sh                   Open a shell in the running container
# Dev utils
lock                 Refresh pipfile.lock
lint                 Lint project code
format               Format project code
revision rev         Create a new database revision
upgrade              Update the database
downgrade            Downgrade the database
# Main utils
secret               Generate a secret
create_admin         Create a new admin user
# Tests
test                 Run the tests
```
So the basic usage would be:
```shell
make create_admin
make start
```
#### .env
While using the Makefile, the image settings can be set with a .env file, see [.env.example](.env.example).
#### Native
Even though Docker is the recommended method, some Makefile rules are native compatible, so
a virtual environment can also be used after cloning this repository:
```shell
#You need to be able to run these commands on your terminal:
tar, 7z, unrar, xz
```
```shell
pip install pipenv
pipenv shell
pipenv install

make native=1 install
```

### Environment variables
```python
# URL to the Postgres database, ex: postgresql+asyncpg://username:password@db:5432/name
DB_URL
# Comma-separated list of origins to allow for CORS, namely the origin of your frontend
CORS_ORIGINS = ""

# Secret used to sign the JWT
JWT_SECRET_KEY
# Algorithm used to sign the JWT
JWT_ALGORITHM = "HS256"
# Amount of minutes a JWT will be valid for
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Path where the images will be stored
MEDIA_PATH = "/media"
# Path where temporary data will be stored
TEMP_PATH = "/temp"

# For pagination, the maximum of elements per request, has to be positive
MAX_PAGE_LIMIT = 50
```

## Tools used
* FastAPI
* SQLAlchemy
* Alembic
* Pydantic

## Progress
* Creation 🟢100% (new features can always be added)
* Documentation 🟡58%
* OpenAPI 🟡66%
* Cleaner code 🟡50%
* Testing 🟠40%
  * Unit 🟢100%
  * Integration 🔴10%
  
Credits:
* Base API template: https://github.com/grillazz/fastapi-sqlalchemy-asyncpg
