import os
import shutil
import tarfile

import requests

# Writing an uploaded file to file 'tarfile_path'
def upload(task, tarfile_path, file):
    # get file size
    file.seek(0, os.SEEK_END)
    total_size = file.tell()
    file.seek(0)

    size = 0
    with open(tarfile_path, 'wb') as tar:
        while True:
            progress = size * 100 // total_size
            task.update_state(state='DOWNLOADING', meta={'PROGRESS': progress})
            chunk = file.read(1024)
            if not chunk:
                break
            tar.write(chunk)
            size += len(chunk)


# Writing to file 'tarfile_path' from the url by celery worker
def download(task, tarfile_path, url):
    with open(tarfile_path, 'wb') as file:
        req = requests.get(url, stream=True)
        total = int(req.headers['content-length'])
        size = 0

        for chunk in req.iter_content(1024):
            size += len(chunk)
            progress = size * 100 // total
            task.update_state(state='DOWNLOADING', meta={'PROGRESS': progress})
            file.write(chunk)


# Unpacking an archive_path from tarfile_path into archive_path directory by celery worker
def unpack(task, tarfile_path, archive_path):
    with tarfile.open(tarfile_path) as tar:
        size = 0
        total = get_size(tarfile_path)

        for member in tar.getmembers():
            tar.extract(member, path=archive_path)
            size += member.size
            progress = size * 100 // total
            task.update_state(state='UNPACKING', meta={'PROGRESS': progress})


# Get archive size from tarfile
def get_size(filename):
    size = 0
    with tarfile.open(filename) as tar:
        for member in tar.getmembers():
            size += member.size
    return size


# Delete files and directories
def delete(*args):
    for path in args:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)


# Get all files from archive
def get_files_path(directory):
    files_path = []
    for root, _, files in os.walk(directory):
        for file in files:
            files_path.append(os.path.join(root, file).replace('\\', '/'))
    return files_path
