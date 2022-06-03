import tarfile
from io import BytesIO


def remove_container(client, container_id):
    container = client.containers.get(container_id)
    if container.status == 'running':
        container.kill()
    container.remove()


def get_file_from_container(container, fname):
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
