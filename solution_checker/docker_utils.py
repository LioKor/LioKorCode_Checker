import docker

import tarfile
from io import BytesIO

from typing import Union


def create_container():
    client = docker.from_env()
    container = client.containers.run(
        'liokorcode_checker',
        detach=True,
        tty=True,

        network_disabled=True,
        mem_limit='128m',
    )
    return client, container


def remove_container(client, container_id):
    container = client.containers.get(container_id)
    if container.status == 'running':
        container.kill()
    container.remove()


def put_file_to_container(container, path: str, content: str):
    path = path.split('/')
    name, path = path[-1], '/'.join(path[0:-1])

    bio = BytesIO()
    tar = tarfile.open(fileobj=bio, mode='w')
    encoded = content.encode()
    file = BytesIO(encoded)
    tarinfo = tarfile.TarInfo(name)
    tarinfo.size = len(encoded)
    tar.addfile(tarinfo, fileobj=file)
    tar.close()
    bio.seek(0)

    container.put_archive(path, bio.read())


def get_file_from_container(container, fname: str) -> Union[str, None]:
    try:
        bits, stats = container.get_archive(fname)
        bio = BytesIO()
        for chunk in bits:
            bio.write(chunk)
        bio.seek(0)
        tar = tarfile.open(fileobj=bio)
        content = tar.extractfile(tar.getmembers()[0]).read().decode()
        tar.close()

        return content
    except Exception:
        return None
