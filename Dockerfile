FROM python:3-slim as builder
WORKDIR /pipfiles

# INSTALL THE BUILD DEP.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tar p7zip unrar-free xz-utils gcc libc-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -U setuptools wheel

# INSTALL PIPENV
RUN set -ex && pip install pipenv --upgrade

# INSTALL DEPENDENCIES
COPY Pipfile* ./
RUN set -ex && pipenv install --system

FROM builder as final
ENV PYTHONUNBUFFERED=1
WORKDIR /

# COPY APP SOURCE CODE
COPY ./api /api
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x entrypoint.sh

EXPOSE 3000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["hypercorn", "api.main:app", "-b", "0.0.0.0:3000"]
