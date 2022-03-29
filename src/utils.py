import os


def get_ext(path: str) -> str:
    arr = path.split('.')
    if len(arr) > 1:
        return arr[len(arr) - 1]
    return ''


def create_file(path, content):
    f = open(path, 'w')
    f.write(content)
    f.close()


def create_files(files, base_path):
    for path, content in files.items():
        if path.find('..') != -1 or path.startswith('/') or path.startswith('\\'):
            raise Exception('Escape root detected!')

        dir = os.path.dirname(path)
        dir = os.path.join(base_path, dir)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)

        path = os.path.join(base_path, path)
        create_file(path, content)
