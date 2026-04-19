FROM python:3.11-slim
RUN useradd -m appuser
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn
USER appuser
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
