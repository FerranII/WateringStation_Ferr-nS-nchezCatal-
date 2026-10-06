# Dockerfile 
FROM python:3.12-alpine 
WORKDIR /app 
COPY . . 
EXPOSE 3000 
CMD ["python", "server.py"]