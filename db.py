from pymongo import MongoClient
from bson.objectid import ObjectId
import model
import config


class __DAO:
    def __init__(self, coll, item_type):
        self.coll = coll
        self.count = coll.find({}).count()
        assert issubclass(item_type, model.Model)
        self.type = item_type

    def get_by_id(self, item_id):
        db_rec = self.coll.find_one({'_id': item_id})
        return self.type(**db_rec) if db_rec else None

    def get_all(self):
        return [self.type(**db_rec) for db_rec in self.coll.find({})]

    def update(self, item):
        result = self.coll.update_one({'_id': item.id}, {'$set': item.to_dic()}, upsert=True)
        if result.upserted_id:
            self.count += 1

    def delete(self, item_id):
        self.coll.delete_one({'_id': item_id})

    def create(self, item):
        if self.coll.insert_one(item.to_dic()):
            self.count += 1

    def _get_page(self, page_no=1, page_size=10, query={}):
        cursor = self.coll.find(query).skip(page_size * (page_no - 1)).limit(page_size)
        return [self.type(**db_rec) for db_rec in cursor]

    def get_pages_count(self, page_size=10):
        pages_count = self.count // page_size
        if self.count % page_size:
            pages_count += 1
        return pages_count


class __UserDAO(__DAO):
    def __init__(self, coll):
        super().__init__(coll, model.User)

    def get_blocked_page(self, page_no=1, page_size=10):
        return self._get_page(page_no, page_size, {'blocked': True})

    def get_page(self, page_no=1, page_size=10):
        return self._get_page(page_no, page_size, {'blocked': False})


class __MessageDAO(__DAO):
    def __init__(self, coll):
        super().__init__(coll, model.Message)


class __CommonData(__DAO):
    def __init__(self, coll):
        self.coll = coll
        try:
            self.data = coll.find({})[0]
        except IndexError:
            self.data = {
                'availability': 'available',
                'blockmsg': "uh..oh you're blocked",
                'nonavailmsg': "I'm sorry i'm apparently offline"
            }
            result = self.coll.insert_one(self.data)
            self.data['_id'] = result.inserted_id

    @property
    def availability(self):
        return self.data['availability']

    @availability.setter
    def availability(self, value):
        if value in ['available', 'unavailable']:
            self.data['availability'] = value
        self.coll.update_one({'_id': self.data['_id']}, {'$set': self.data})

    @property
    def blockmsg(self):
        return self.data['blockmsg']

    @blockmsg.setter
    def blockmsg(self, value):
        self.data['blockmsg'] = value
        self.coll.update_one({'_id': self.data['_id']}, {'$set': self.data})

    @property
    def nonavailmsg(self):
        return self.data['nonavailmsg']

    @nonavailmsg.setter
    def nonavailmsg(self, value):
        self.data['nonavailmsg'] = value
        self.coll.update_one({'_id': self.data['_id']}, {'$set': self.data})


__db_client = MongoClient(config.db_auth)
__db = __db_client[config.db_name]


def __get_coll(coll_name):
    if coll_name not in __db.collection_names():
        __db.create_collection(coll_name)
    return __db[coll_name]

usr = __UserDAO(__get_coll('usr'))
msg = __MessageDAO(__get_coll('msg'))
common = __CommonData(__get_coll('common'))
