FROM python:3.12-slim

WORKDIR /code

# Install uv
RUN pip install uv

# Copy requirements file
COPY pyproject.toml /code/pyproject.toml

# Install dependencies with uv
RUN uv sync

# Copy the rest of the application
COPY . /code

CMD uv run main.py
