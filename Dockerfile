FROM python:3.11-slim

# Create working folder 
WORKDIR /app
COPY Pipfile Pipfile.lock ./

#Install dependencies

RUN python -m pip install --upgrade pip pipenv && \
    pipenv install --system --deploy

# Copy application files
COPY wsgi.py .
COPY service/ ./service/

# Switch to a non-root user
RUN useradd --uid 1001 theia && \
    chown -R theia:theia /app
USER theia

# Expose any ports the app is expecting in the environment
EXPOSE 8080
ENV PORT=8080

# Run the service
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "wsgi:app"]


