from io import BytesIO
import tarfile


def files_to_tar(files: dict, base_path: str) -> BytesIO:
    bio = BytesIO()
    tar = tarfile.open(fileobj=bio, mode='w')
    for name, content in files.items():
        encoded = content.encode()
        file = BytesIO(encoded)
        tarinfo = tarfile.TarInfo(base_path + name)
        tarinfo.size = len(encoded)
        tar.addfile(tarinfo, fileobj=file)
    tar.close()
    bio.seek(0)
    return bio


def get_ext(path: str) -> str:
    arr = path.split('.')
    if len(arr) > 1:
        return arr[len(arr) - 1]
    return ''


def create_file(path, content, allow_rewrite=True):
    mode = 'w' if allow_rewrite else 'x'
    f = open(path, mode)
    f.write(content)
    f.close()
