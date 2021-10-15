from os import path
from tempfile import TemporaryFile
from typing import Optional, List
from .deta import deta


class Drive:
    def __init__(self, name: str, host: Optional[str] = None):
        self.drive = deta.Drive(name, host)

    def put(self, name: str, data):
        return self.drive.put(name, data)

    def get(self, path: str):
        file = self.drive.get(path)
        if not file:
            raise FileNotFoundError(f"{path} not found in the Deta Drive")
        return file

    def copy(self, source: str, dest: str):
        big_file = self.get(source)

        with TemporaryFile() as f:
            for chunk in big_file.iter_chunks(4096):
                f.write(chunk)
            big_file.close()
            f.seek(0)
            self.drive.put(dest, f)

    def move(self, source: str, dest: str):
        self.copy(source, dest)
        self.remove([source])

    def remove(self, names: List[str]):
        if names:
            return self.drive.delete_many(names)

    def ls(self, path: str):
        res = self.drive.list(prefix=path)
        all_items = res["names"]

        while "paging" in res and res["paging"]["last"]:
            res = self.drive.list(prefix=path, last=res["paging"]["last"])
            all_items += res["names"]

        return all_items

    def rmtree(self, path: str):
        names = self.ls(path)
        if names:
            self.drive.delete_many(names)


media = Drive("media")
