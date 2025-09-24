FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV PORT=5001
ENV FLASK_APP=main.py

# ENV NINJAS_API_KEY=b9FhwPGn7OfSVBldusYSIQ==GmuSYcf89k55jRaS

EXPOSE 5001

CMD ["python", "main.py"]