docker kill agent
docker rm agent
docker build app/ -t virtualagent:latest
docker run --rm -it -p 5000:5000 -w /app --name agent --env-file=.env virtualagent