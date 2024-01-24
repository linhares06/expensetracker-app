from flask_login import UserMixin
from pydantic import BaseModel, TypeAdapter, Field
from bson import ObjectId

from database import Database

db = Database()

class RegisterUser(BaseModel):
    username: str
    password: str

    def save(self) -> str:
        """
        Save the current expense instance to the expenses collection.

        Returns:
        str: The string representation of the inserted document's ObjectId.
        """
        result = db.expenses_collection.insert_one(self.model_dump())
        return str(result.inserted_id)

class User(UserMixin, BaseModel):
    id: str = Field(alias='_id')
    username: str
    password: str

    @staticmethod
    def get_user(username: str = None, user_id: str = None) -> dict:
        """
        Retrieve user information based on either the username or user_id.

        Parameters:
        - username (str, optional): The username of the user to retrieve.
        - user_id (str, optional): The user_id of the user to retrieve.

        Returns:
        dict or None: A dictionary containing user information if the user is found,
                    or None if no user is found with the provided criteria.

        Note:
        The method uses either the 'username' or '_id' field, depending on which parameter is provided.
        If 'username' is provided, the method searches for a user with that username;
        if 'user_id' is provided, it searches for a user with that user_id (converted to ObjectId).

        The returned user information includes only the 'username' and 'password' fields from the database.
        The '_id' field is converted to a string before returning.

        If a user is found, the retrieved dictionary is passed through TypeAdapter(User).validate_python
        to convert it to a User object before returning.
        """
        field = 'username' if username else '_id'
        value = username or ObjectId(user_id)

        user_dict = db.expenses_collection.find_one({field: value}, {'username': 1, 'password': 1})

        if user_dict:
            user_dict['_id'] = str(user_dict.get('_id'))
        else: 
            return None
        
        user = TypeAdapter(User).validate_python(user_dict)
        
        return user
    
    @staticmethod
    def validate_unique_username(username: str) -> bool:
        """
        Validate if a username is unique.

        Parameters:
        - username (str): The username to be checked for uniqueness.

        Returns:
        bool: True if the username is unique, False otherwise.
        """
        return db.expenses_collection.count_documents({'username': username}, limit=1) == 0