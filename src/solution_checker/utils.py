from io import BytesIO
import tarfile


def files_to_tar(files: dict[str, str], base_path: str) -> BytesIO:
    bio = BytesIO()
    tar = tarfile.open(fileobj=bio, mode="w")
    for name, content in files.items():
        encoded = content.encode()
        file = BytesIO(encoded)
        tarinfo = tarfile.TarInfo(base_path + name)
        tarinfo.size = len(encoded)
        tar.addfile(tarinfo, fileobj=file)
    tar.close()
    bio.seek(0)
    return bio
