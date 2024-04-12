#!/bin/bash

docker_container_name=$1

# Pull the latest image
docker pull ghcr.io/sailthrough-english/web:latest

# Stop and remove the old container
docker stop my-app
docker rm my-app

# Run the new image
docker run --name ${} -d ghcr.io/sailthrough-english/web:latest

# Clean up unused images
docker image prune -f