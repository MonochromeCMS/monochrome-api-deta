FROM python:3.9-slim as builder
WORKDIR /pipfiles

# INSTALL DEPS.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tar p7zip unrar-free xz-utils && \
    rm -rf /var/lib/apt/lists/*

# INSTALL REQUIREMENTS
COPY Pipfile* ./
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -U setuptools wheel pipenv && \
    pipenv install --system && \
    apt-get remove -y gcc libc-dev && \
    apt-get autoremove -y && \
    pip uninstall -y setuptools wheel pipenv pip
    

FROM builder as final
ENV PYTHONUNBUFFERED=1
WORKDIR /

# TINI INSTALLATION
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# COPY APP SOURCE CODE
COPY ./api /api
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/tini", "--", "/entrypoint.sh"]

ENV PORT 3000
EXPOSE 3000
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
