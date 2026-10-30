FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Puerto de Sockets de la Central
EXPOSE 5050 

CMD ["python", "WM_Central/WM_Central.py"]