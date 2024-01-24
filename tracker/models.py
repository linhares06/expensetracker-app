from pydantic import BaseModel, Field, TypeAdapter
from decimal import Decimal
from collections import defaultdict
from typing import Optional, List, Tuple

from database import Database
from utils import cursor_to_list


EXPENSES_DATABASE_FIELD = 'expenses'
CATEGORIES_DATABASE_FIELD = 'categories'

db = Database()

class Expense(BaseModel):
    id: str
    description: str
    amount: str
    category_id: str
    category_name: str
    date: Optional[str] = None

    def save(self, username):
        """
        Save the current expense instance for a specific user.

        Parameters:
        - username (str): The username of the user for whom the expense is being saved.

        Note:
        This method updates the expenses collection for the specified user by pushing the current expense data
        using the '$push' operator. It utilizes the `model_dump` method to retrieve the serialized data.
        """
        db.expenses_collection.update_one({'username': username}, {'$push': {EXPENSES_DATABASE_FIELD: self.model_dump()}})

    def update(self, username: str):
        """
        Update the current expense instance in the expenses collection for a specific user.

        Parameters:
        - username (str): The username of the user for whom the expense is being updated.

        Returns:
        int: The number of modified documents in the expenses collection (0 or 1).

        Example:
        expense = Expense(id='123', description='Groceries', amount=50.0, category='Food')
        modified_count = expense.update(username='john_doe')
        if modified_count == 1:
            print("Expense updated successfully.")
        else:
            print("Expense not found or update failed.")
        """
        result = db.expenses_collection.update_one(
            {'username': username, f'{EXPENSES_DATABASE_FIELD}.id': self.id}, 
            {'$set': 
                { 
                    f'{EXPENSES_DATABASE_FIELD}.$.description': self.description, 
                    f'{EXPENSES_DATABASE_FIELD}.$.amount': self.amount, 
                    f'{EXPENSES_DATABASE_FIELD}.$.category_id': self.category_id, 
                    f'{EXPENSES_DATABASE_FIELD}.$.category_name': self.category_name, 
                } 
            }
        )
        return result.modified_count

    def get_expense_from_user(username: str, expense_id: str):
        """
        Retrieve an expense for a specific user based on the expense ID.

        Parameters:
        - username (str): The username of the user for whom the expense is being retrieved.
        - expense_id (str): The unique identifier of the expense to retrieve.

        Returns:
        Optional[Expense]: An Expense object if the expense is found, or None if not found.

        Example:
        expense = get_expense_from_user(username='john_doe', expense_id='123')
        if expense:
            print(f"Expense found: {expense.description}, Amount: {expense.amount}")
        else:
            print("Expense not found.")
        """
        result = db.expenses_collection.find_one(
            {'username': username, f'{EXPENSES_DATABASE_FIELD}.id': expense_id}, {f'{EXPENSES_DATABASE_FIELD}.$': 1, '_id': 0}
        )
        expense_dict = result.get(EXPENSES_DATABASE_FIELD, None)[0]
        expense = TypeAdapter(Expense).validate_python(expense_dict)

        return expense
    
    @staticmethod
    def get_all_expenses_from_user(username: str) -> list:
        """
        Retrieve all expenses associated with a specific user.

        Parameters:
        - username (str): The username of the user whose expenses are to be retrieved.

        Returns:
        list: A list containing dictionaries representing the expenses of the user.
            Each dictionary includes the 'expenses' field and excludes the '_id' field.
        """
        cursor = db.expenses_collection.find({'username': username}, {EXPENSES_DATABASE_FIELD: 1, '_id': 0})
        return cursor_to_list(cursor, EXPENSES_DATABASE_FIELD)
    
    @staticmethod
    def calculate_remaining_budget_by_category(expense_list: list[dict], category_list: list[dict]) -> dict:
        """
        Calculate remaining budget for each category based on user expenses.

        Args:
            expense_list (list[dict]): A list of dictionaries representing user expenses.
                Each dictionary should have keys 'category' and 'amount'.
            category_list (list[dict]): A list of dictionaries representing budget categories.
                Each dictionary should have keys 'name' and 'budget'.

        Returns:
            list[dict]: A list of dictionaries containing the remaining budget for each category.
                Each dictionary has keys 'name' and 'budget', where 'budget' is a string representation
                of the remaining budget for the corresponding category.
        """
        spent_budget = defaultdict(Decimal)
        budget = defaultdict(Decimal, {category.get('name'): Decimal(category.get('budget', 0)) for category in category_list})

        for expense in expense_list:
            category_key = expense.get('category_name', 'Undefined category')
            spent_budget[category_key] += Decimal(expense.get('amount', 0))

        # Calculate the remaining budget and percentage spent for each category.
        result = []
        for key, value in budget.items():
            remaining_budget = value - spent_budget[key]
            percentage_spent = (100 - (spent_budget[key] / value) * 100) if value != 0 else 0
            result.append({'name': key, 'budget': str(remaining_budget), 'percentage_spent': f'{percentage_spent:.2f}%'})

        return result
    
    @staticmethod
    def sum_expenses_by_category(expense_list: List[dict]) -> Tuple[List[str], List[Decimal]]:
        """
        Calculate the total expenses for each category based on the provided list of expenses.

        Parameters:
        - expense_list (List[dict]): A list of dictionaries representing individual expenses.
        Each dictionary should include at least the 'category_name' and 'amount' fields.

        Returns:
        Tuple[List[str], List[Decimal]]: A tuple containing two lists - the category names and their corresponding total expenses.

        Example:
        expenses = [
            {'category_name': 'Groceries', 'amount': '50.0'},
            {'category_name': 'Dining', 'amount': '30.0'},
            {'category_name': 'Entertainment', 'amount': '20.0'}
        ]
        category_names, total_expenses = Expense.sum_expenses_by_category(expenses)
        for category, total in zip(category_names, total_expenses):
            print(f"Category: {category}, Total Expenses: {total}")
        """
        spent_budget = defaultdict(Decimal)
        name_list, value_list = [], []

        for expense in expense_list:
            category_key = expense.get('category_name', 'Undefined category')
            spent_budget[category_key] += Decimal(expense.get('amount', 0))

        spent_budget = dict(spent_budget)

        for key, value in spent_budget.items():
            name_list.append(key)
            value_list.append(value)

        return name_list, value_list

    
    @staticmethod
    def delete_category(username: str, expense_id: str):
        """
        Delete an expense category for a specific user based on the expense ID.

        Parameters:
        - username (str): The username of the user for whom the expense category is being deleted.
        - expense_id (str): The unique identifier of the expense category to be deleted.

        Returns:
        int: The number of modified documents in the expenses collection (0 or 1).

        Example:
        modified_count = Expense.delete_category(username='john_doe', expense_id='123')
        if modified_count == 1:
            print("Expense category deleted successfully.")
        else:
            print("Expense category not found or deletion failed.")
        """
        result = db.expenses_collection.update_one({'username': username}, {'$pull': {EXPENSES_DATABASE_FIELD: {'id': expense_id}}})
        return result.modified_count

    @staticmethod
    def sum_expenses(expense_list: list[dict]) -> Decimal:
        """
        Calculate the total sum of amounts from a list of expenses.

        Parameters:
        - expense_list (list[dict]): A list of dictionaries representing individual expenses.
        Each dictionary should contain an 'amount' field with a numeric value.

        Returns:
        Decimal: The total sum of amounts as a Decimal.
        """
        return sum(Decimal(expense['amount']) for expense in expense_list)  
    
    @staticmethod
    def verify_expense_with_category(username: str, category_id: str) -> bool:
        """
        Verify if there are any expenses associated with a specific category for a given user.

        Parameters:
        - username (str): The username of the user for whom the expenses are being verified.
        - category_id (str): The unique identifier of the category to check for associated expenses.

        Returns:
        bool: True if there are no expenses associated with the category, False otherwise.

        Example:
        has_expenses = Expense.verify_expense_with_category(username='john_doe', category_id='123')
        if not has_expenses:
            print("No expenses found for the category.")
        else:
            print("There are expenses associated with the category.")
        """
        return db.expenses_collection.count_documents({'username': username, f'{EXPENSES_DATABASE_FIELD}.category_id': category_id}) == 0
        

class Category(BaseModel):
    id: str
    name: str
    budget: str

    def save(self, username: str):
        """
        Save the current category instance for a specific user.

        Parameters:
        - username (str): The username of the user for whom the category is being saved.

        Note:
        This method updates the categories collection for the specified user by pushing the current category data
        using the '$push' operator. It utilizes the `model_dump` method to retrieve the serialized data.
        """
        db.expenses_collection.update_one({'username': username}, {'$push': {CATEGORIES_DATABASE_FIELD: self.model_dump()}})

    def update(self, username: str):
        """
        Update the current category instance in the expenses collection for a specific user.

        Parameters:
        - username (str): The username of the user for whom the category is being updated.

        Returns:
        int: The number of modified documents in the expenses collection (0 or 1).

        Example:
        category = Category(id='123', name='Groceries', budget=100.0)
        modified_count = category.update(username='john_doe')
        if modified_count == 1:
            print("Category updated successfully.")
        else:
            print("Category not found or update failed.")
        """
        result = db.expenses_collection.update_one(
            {'username': username, f'{CATEGORIES_DATABASE_FIELD}.id': self.id}, 
            {'$set': { f'{CATEGORIES_DATABASE_FIELD}.$.name': self.name, f'{CATEGORIES_DATABASE_FIELD}.$.budget': self.budget} }
        )
        return result.modified_count

    def get_category_from_user(username: str, category_id: str):
        """
        Retrieve a category for a specific user based on the category ID.

        Parameters:
        - username (str): The username of the user for whom the category is being retrieved.
        - category_id (str): The unique identifier of the category to retrieve.

        Returns:
        Optional[Category]: A Category object if the category is found, or None if not found.

        Example:
        category = get_category_from_user(username='john_doe', category_id='123')
        if category:
            print(f"Category found: {category.name}, Budget: {category.budget}")
        else:
            print("Category not found.")
        """
        result = db.expenses_collection.find_one(
            {'username': username, f'{CATEGORIES_DATABASE_FIELD}.id': category_id}, {f'{CATEGORIES_DATABASE_FIELD}.$': 1, '_id': 0}
        )
        category_dict = result.get(CATEGORIES_DATABASE_FIELD, None)[0]
        category = TypeAdapter(Category).validate_python(category_dict)

        return category

    @staticmethod
    def get_all_categories_from_user(username: str) -> list:
        """
        Retrieve all categories associated with a specific user.

        Parameters:
        - username (str): The username of the user whose categories are to be retrieved.

        Returns:
        list: A list containing dictionaries representing individual categories.
            Each dictionary includes the specified 'categories' field and excludes the '_id' field.
        """
        cursor = db.expenses_collection.find({'username': username}, {CATEGORIES_DATABASE_FIELD: 1, '_id': 0})
        return cursor_to_list(cursor, CATEGORIES_DATABASE_FIELD)
    
    @staticmethod
    def validate_unique_category_name(username: str, category_name: str) -> bool:
        """
        Validate if a category name is unique for a specific user.

        Parameters:
        - username (str): The username of the user for whom the category name uniqueness is being validated.
        - category_name (str): The name of the category to check for uniqueness.

        Returns:
        bool: True if the category name is unique for the user, False otherwise.

        Example:
        is_unique = Category.validate_unique_category_name(username='john_doe', category_name='Groceries')
        if is_unique:
            print("Category name is unique.")
        else:
            print("Category name already exists for the user.")
        """
        return db.expenses_collection.count_documents({'username': username, f'{CATEGORIES_DATABASE_FIELD}.name': category_name}) == 0
    
    @staticmethod
    def delete_category(username: str, category_id: str):
        """
        Delete a category for a specific user based on the category ID.

        Parameters:
        - username (str): The username of the user for whom the category is being deleted.
        - category_id (str): The unique identifier of the category to be deleted.

        Returns:
        int: The number of modified documents in the expenses collection (0 or 1).

        Example:
        modified_count = Category.delete_category(username='john_doe', category_id='123')
        if modified_count == 1:
            print("Category deleted successfully.")
        else:
            print("Category not found or deletion failed.")
        """
        result = db.expenses_collection.update_one({'username': username}, {'$pull': {CATEGORIES_DATABASE_FIELD: {'id': category_id}}})
        return result.modified_count
