from flask import Flask, request
from docker import auth
import yaml
import os

app = Flask(__name__)

# Create a Docker client
client = docker.from_env() # type: ignore

@app.route('/', methods=['POST'])
def respond():
    # Load the Docker container - repository mapping
    with open('mapping.yml', 'r') as f:
        mapping = yaml.safe_load(f)

    # Parse the webhook payload
    payload = request.get_json()

    # Extract the repository name and the tag
    repo_name = payload['repository']['full_name']
    ref = payload['ref']
    tag = ref.split('/')[-1] if ref.startswith('refs/tags/') else 'latest'

    # Find the Docker container name corresponding to the repository name
    for container_name, repo in mapping.items():
        if repo == repo_name:
            docker_container_name = container_name
            break

    # Login to the GitHub Container Registry
    username = os.getenv('GHCR_USERNAME')
    password = os.getenv('GHCR_TOKEN')
    auth_config = auth.encode_docker_auth(username, password)
    client.api.login(username=username, password=password, registry='https://ghcr.io', reauth=True, dockercfg_path=auth_config)

    # Pull the latest image
    image = client.images.pull('ghcr.io/' + repo_name, tag=tag)

    # Stop and remove the old container
    try:
        container = client.containers.get(docker_container_name)
        container.stop()
        container.remove()
    except docker.errors.NotFound: # type: ignore
        pass

    # Run the new image
    client.containers.run(image.id, name=docker_container_name, detach=True)

    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)