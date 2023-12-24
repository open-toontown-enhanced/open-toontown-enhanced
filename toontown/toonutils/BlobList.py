from panda3d.core import *
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
import functools

class BlobList:

    def __init__(self, source = None, store = 0):
        self.store = store
        self._blob = None
        self._list = None
        if isinstance(source, bytes):
            self.__blob = source
        elif isinstance(source, list):
            self._list = source[:]
        elif isinstance(source, self.__class__):
            if source.store == store:
                if source._list != None:
                    self._list = source._list[:]
                self.__blob = source.__blob
            else:
                self._list = source[:]

    def markDirty(self):
        if self._list:
            self._blob = None

    def getBlob(self, store = None):
        if store == None or store == self.store:
            if self._blob == None:
                self.__encodeList()
            return self._blob
        return self.makeBlob(store)

    def __encodeList(self):
        self._blob = self.makeBlob(self.store)

    def makeBlob(self, store):
        return NotImplementedError

    def __decodeList(self):
        self._list = self.makeList(self.store)

    def makeList(self, store):
        return NotImplementedError

    def append(self, item):
        if self._list == None:
            self.__decodeList()
        self._list.append(item)
        self._blob = None

    def extend(self, items):
        self += items

    def count(self, item):
        if self._list == None:
            self.__decodeList()
        return self._list.count(item)

    def index(self, item):
        if self._list == None:
            self.__decodeList()
        return self._list.index(item)

    def insert(self, index, item):
        if self._list == None:
            self.__decodeList()
        self._list.insert(index, item)
        self._blob = None

    def pop(self, index = None):
        if self._list == None:
            self.__decodeList()
        self._blob = None
        if index == None:
            return self._list.pop()
        else:
            return self._list.pop(index)

    def remove(self, item):
        if self._list == None:
            self.__decodeList()
        self._list.remove(item)
        self._blob = None

    def reverse(self):
        if self._list == None:
            self.__decodeList()
        self._list.reverse()
        self._blob = None

    def sort(self, cmpfunc = None):
        if self._list == None:
            self.__decodeList()
        if cmpfunc == None:
            self._list.sort()
        else:
            self._list.sort(key=functools.cmp_to_key(cmpfunc))
        self._blob = None

    def __len__(self):
        if self._list == None:
            self.__decodeList()
        return len(self._list)

    def __getitem__(self, index):
        if self._list == None:
            self.__decodeList()
        if isinstance(index, slice):
            return self.__class__(self._list[index.start:index.stop], store=self.store)
        return self._list[index]

    def __setitem__(self, index, item):
        if self._list == None:
            self.__decodeList()
        if isinstance(index, slice):
            if isinstance(item, self.__class__):
                self._list[index.start:index.stop] = item._list
            else:
                self._list[index.start:index.stop] = item
        else:
            self._list[index] = item
        self._blob = None

    def __delitem__(self, index):
        if self._list == None:
            self.__decodeList()
        if isinstance(index, slice):
            del self._list[index.start:index.stop]
        else:
            del self._list[index]
        self._blob = None

    def __iadd__(self, other):
        if self._list == None:
            self.__decodeList()
        self._list += list(other)
        self._blob = None
        return self

    def __add__(self, other):
        copy = self.__class__(self, store=self.store)
        copy += other
        return copy

    def __repr__(self):
        return self.output()

    def __str__(self):
        return self.output()

    def output(self, store = -1):
        if self._list == None:
            self.__decodeList()
        inner = ''
        for item in self._list:
            inner += ', %s' % item.output(store)

        return f'{self.__class__.__name__}([%s])' % inner[2:]