import pymongo

class Database:
    
    def __init__(self, uri: str = 'mongodb://localhost:27017/', db_name: str = 'expensetracker'):
        
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        self.expenses_collection = self.db['expenses']
        self.expenses_collection.create_index([('username', 1)], unique=True)