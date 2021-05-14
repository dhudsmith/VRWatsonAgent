docker build . -t virtual-agent:latest
docker run -it --rm --env-file .env -v C:\Users\Hudson\PycharmProjects\VRWatsonAgent:/app/ -w /app/ -p 5000:5000 virtual-agent:latest python3.8 app/app.py