FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
#PUERTO Central
EXPOSE 5050 
CMD ["python", "WM_Central/WM_Central.py", "5050", "metro.proxy.rlwy.net:15921"]