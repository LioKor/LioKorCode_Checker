import tarfile
from io import BytesIO

import docker
from docker.client import DockerClient
from docker.models.containers import Container


def create_container() -> tuple[DockerClient, Container]:
    client = docker.from_env()
    container = client.containers.run(
        "liokorcode_checker",
        detach=True,
        tty=True,
        network_disabled=True,
        mem_limit="128m",
    )
    return client, container


def remove_container(client: DockerClient, container_id: str) -> None:
    container = client.containers.get(container_id)
    if container.status == "running":
        container.kill()
    container.remove()


def put_file_to_container(container: Container, path: str, content: str) -> None:
    path_parts = path.split("/")
    name, directory = path_parts[-1], "/".join(path_parts[0:-1])

    bio = BytesIO()
    tar = tarfile.open(fileobj=bio, mode="w")
    encoded = content.encode()
    file = BytesIO(encoded)
    tarinfo = tarfile.TarInfo(name)
    tarinfo.size = len(encoded)
    tar.addfile(tarinfo, fileobj=file)
    tar.close()
    bio.seek(0)

    container.put_archive(directory, bio.read())


def get_file_from_container(container: Container, fname: str) -> str | None:
    try:
        bits, stats = container.get_archive(fname)
        bio = BytesIO()
        for chunk in bits:
            bio.write(chunk)
        bio.seek(0)

        tar = tarfile.open(fileobj=bio)
        file = tar.extractfile(tar.getmembers()[0])
        tar.close()

        if file is None:
            return None

        return file.read().decode()
    except Exception:
        return None
