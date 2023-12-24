from . import CatalogItem
from toontown.toonutils.BlobList import *

class CatalogItemList(BlobList):

    def getNextDeliveryDate(self):
        if len(self) == 0:
            return
        nextDeliveryDate = None
        for item in self:
            if item:
                if nextDeliveryDate == None or item.deliveryDate < nextDeliveryDate:
                    nextDeliveryDate = item.deliveryDate

        return nextDeliveryDate

    def getNextDeliveryItem(self):
        if len(self) == 0:
            return
        nextDeliveryDate = None
        nextDeliveryItem = None
        for item in self:
            if item:
                if nextDeliveryDate == None or item.deliveryDate < nextDeliveryDate:
                    nextDeliveryDate = item.deliveryDate
                    nextDeliveryItem = item

        return nextDeliveryItem

    def extractDeliveryItems(self, cutoffTime):
        beforeTime = []
        afterTime = []
        for item in self:
            if item.deliveryDate <= cutoffTime:
                beforeTime.append(item)
            else:
                afterTime.append(item)

        return (CatalogItemList(beforeTime, store=self.store), CatalogItemList(afterTime, store=self.store))

    def extractOldestItems(self, count):
        return (self[0:count], self[count:])

    def makeBlob(self, store):
        dg = PyDatagram()
        if self._list:
            dg.addUint8(CatalogItem.CatalogItemVersion)
            for item in self.__list:
                CatalogItem.encodeCatalogItem(dg, item, store)

        return dg.getMessage()

    def makeList(self, store):
        _list = []
        if self._blob:
            dg = PyDatagram(self.__blob)
            di = PyDatagramIterator(dg)
            versionNumber = di.getUint8()
            while di.getRemainingSize() > 0:
                item = CatalogItem.decodeCatalogItem(di, versionNumber, store)
                _list.append(item)

        return _list
