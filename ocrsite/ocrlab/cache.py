"""
OCR-specific nodetree cacher classes.
"""
import os
import shutil
from contextlib import contextmanager

from nodetree import cache

from .. import deepzoom
import hashlib
import bencode

from pymongo import Connection
import gridfs

class UnsupportedCacheTypeError(StandardError):
    pass


class BaseCacher(cache.BasicCacher):
    cachetype = "memory"
    def __init__(self, path="", key="", **kwargs):
        super(BaseCacher, self).__init__(**kwargs)
        self._key = key
        self._path = path

    def set_cache(self, n, data):
        pass

    def get_cache(self, n):
        pass

    def has_cache(self, n):
        return False

    def get_path(self, n):
        hash = hashlib.md5(bencode.bencode(n.hash_value())).hexdigest()
        return os.path.join(self._path, self._key, n.label, hash)

    def clear(self):
        pass

    def clear_cache(self, n):
        pass

    def size(self):
        pass



class PersistantFileCacher(BaseCacher):
    """
    Store data in files for persistance.
    """
    cachetype = "file"

    def read_node_data(self, node, path):
        """
        Get the file data under path and return it.
        """
        readpath = os.path.join(path, node.get_file_name())
        self.logger.debug("Reading %s cache: %s", self.cachetype, readpath)
        with self.get_read_handle(readpath) as fh:
            return node.reader(fh)

    def write_node_data(self, node, path, data):
        filepath = os.path.join(path, node.get_file_name())
        self.logger.info("Writing %s cache: %s", self.cachetype, filepath)
        if data is not None:
            with self.get_write_handle(filepath) as fh:
                node.writer(fh, data)

    def get_cache(self, n):
        path = self.get_path(n)
        if self.has_cache(n):
            return self.read_node_data(n, path)

    @contextmanager
    def get_read_handle(self, readpath):
        try:
            h = open(readpath, "rb")
            yield h
        finally:
            h.close()

    @contextmanager
    def get_write_handle(self, filepath):
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath), 0777)
        try:
            h = open(filepath, "wb")
            yield h
        finally:
            h.close()

    def set_cache(self, n, data):
        self.write_node_data(n, self.get_path(n), data)

    def has_cache(self, n):
        return os.path.exists(os.path.join(self.get_path(n), n.get_file_name()))

    def clear(self):
        shutil.rmtree(os.path.join(self._path, self._key), True)

    def clear_cache(self, n):
        if self.has_cache(n):
            path = self.get_path(n)
            fpath = os.path.join(path, n.get_file_name())
            os.unlink(fpath)
            try:
                os.rmdir(path)
            except OSError, (errno, strerr):
                if errno != 39:
                    raise

    def size(self):
        folder = os.path.join(self._path, self._key)
        size = 0
        for (path, dirs, files) in os.walk(folder):
            for file in files:
                filename = os.path.join(path, file)
                size += os.path.getsize(filename)
        return size


class MongoDBCacher(PersistantFileCacher):
    """
    Write data to MongoDB instead of the FS.
    """
    cachetype = "MongoDB"
    def __init__(self, *args, **kwargs):
        super(MongoDBCacher, self).__init__(*args, **kwargs)
        self._db = getattr(Connection(), self._key)
        self._fs = gridfs.GridFS(self._db)

    @contextmanager
    def get_read_handle(self, readpath):
        try:
            yield self._fs.get_last_version(readpath)
        finally:
            pass

    @contextmanager
    def get_write_handle(self, filepath):
        try:
            h = self._fs.new_file(filename=filepath, encoding="utf-8")
            yield h
        finally:
            h.close()

    def has_cache(self, n):
        return self._fs.exists(filename=os.path.join(self.get_path(n), n.get_file_name()))

    def clear_cache(self, n):
        if self.has_cache(n):
            path = self.get_path(n)
            filepath = os.path.join(path, n.get_file_name())
            gridout = self._fs.get_last_version(filepath)
            self._fs.delete(gridout._id)

    def clear(self):
        self._db.drop_collection("fs.files")
        self._db.drop_collection("fs.chunks")


class DziFileCacher(PersistantFileCacher):
    """
    Write a DZI after having written a PNG.
    """
    def write_node_data(self, node, path, data):
        super(DziFileCacher, self).write_node_data(node, path, data)
        filepath = os.path.join(path, node.get_file_name())
        if not filepath.endswith(".png"):
            return
        with self.get_read_handle(filepath) as fh:
            if not os.path.exists(path):
                os.makedirs(path)
            creator = deepzoom.ImageCreator(tile_size=512,
                    tile_overlap=2, tile_format="png",
                    image_quality=1, resize_filter="nearest")
            creator.create(fh, "%s.dzi" % os.path.splitext(filepath)[0])

    def clear_cache(self, n):
        super(DziFileCacher, self).clear_cache(n)
        if self.has_cache(n):
            path = self.get_path(n)
            fpath = os.path.join(path, n.get_file_name())
            if fpath.endswith(".png"):
                dzipath = "%s.dzi" % os.path.splitext(filepath)[0]
                os.unlink(fpath)
                try:
                    os.rmdir(path)
                except OSError, (errno, strerr):
                    if errno != 39:
                        raise

    def clear(self):
        super(DziFileCacher, self).clear()
        if os.path.exists(os.path.join(self._path, self._key)):
            shutil.rmtree(os.path.join(self._path, self._key))


class TestMockCacher(BaseCacher):
    """
    Mock cacher that doesn't do anything.
    """
    pass



