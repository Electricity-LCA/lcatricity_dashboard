FROM python:3.12.3-slim-bullseye

# Set environment variables
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="${PYTHONPATH}:/usr/src/app" \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /usr/src/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python3 -m venv $VIRTUAL_ENV && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code
COPY ./ ./lcatricity_dashboard

# Set entrypoint and healthcheck
ENTRYPOINT ["streamlit", "run", "lcatricity_dashboard/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health