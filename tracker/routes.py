from flask import Blueprint, render_template, request, redirect, flash, url_for
from bson import ObjectId
from flask_login import login_required, current_user
from decimal import Decimal
from datetime import datetime

from tracker.forms import ExpenseForm, CategoryForm
from tracker.models import Expense, Category
from utils import generate_form_select_field
from analytics.plot_generator import generate_expense_by_category_pie_chart


bp = Blueprint('tracker', __name__)

@bp.route('/')
@login_required
def home():
    """
    Render the home page with expense-related data for the authenticated user.

    Returns:
    render_template: Renders the 'home.html' template with the user's expenses, total expenses,
        and a pie chart showing the distribution of expenses by category.
    """
    # Retrieve all expenses for the current user
    expense_list = Expense.get_all_expenses_from_user(current_user.username)

    # Calculate the total expenses and prepare data for the pie chart
    expense_name_list, expense_amount_list = Expense.sum_expenses_by_category(expense_list)

    # Generate a pie chart image representing expense distribution by category
    expense_by_category_chart = generate_expense_by_category_pie_chart(expense_name_list, expense_amount_list)

    # Calculate the overall total expenses
    expense_total = Expense.sum_expenses(expense_list)

    # Render the home page with the calculated data
    return render_template(
        'home.html', 
        expenses=expense_list, 
        total=expense_total, 
        expense_by_category_chart=expense_by_category_chart,
    )

@bp.route('/expenses', methods = ['GET'])
@login_required
def list_expenses():
    """
    Render the page displaying a list of expenses for the authenticated user.

    Returns:
    render_template: Renders the 'expense_list.html' template with the user's expenses,
        remaining budget by category, and the total expenses.
    """
    # Retrieve all categories and expenses for the current user
    categories = Category.get_all_categories_from_user(current_user.username)
    expenses = Expense.get_all_expenses_from_user(current_user.username)

    # Calculate the remaining budget by category and the overall total expenses
    budget = Expense.calculate_remaining_budget_by_category(expenses, categories)
    expense_total = Expense.sum_expenses(expenses)

    # Render the expense list page with the calculated data
    return render_template('expense_list.html', budget=budget, expenses=expenses, total=expense_total)

@bp.route('/add_expense', methods = ['GET', 'POST'])
@login_required
def add_expense():
    """
    Render the page for adding a new expense and handle the form submission.

    Returns:
    render_template or redirect: Renders the 'expense_form.html' template with the expense form
        or redirects to the expense list page after successful form submission.
    """
    # Retrieve all categories for the current user
    form = ExpenseForm()

    # Retrieve all categories for the current user
    categories = Category.get_all_categories_from_user(current_user.username)

    # Set the choices for the category field in the form
    form.category.choices = generate_form_select_field(categories)

    if form.validate_on_submit():
        # Generate a new ID, retrieve form data, and format the date
        new_id = str(ObjectId())
        description = form.description.data
        amount = form.amount.data
        category_id = form.category.data
        category_name = dict(form.category.choices).get(category_id)
        date = str(datetime.utcnow().strftime('%d-%m-%Y'))

        # Validate the amount to be a positive number
        if not Decimal(amount) > 0:
            flash('Amount must be a positive number.', 'danger')
            return render_template('expense_form.html', form=form)

        # Create an Expense instance and save it to the database
        expense = Expense(id=new_id, description=description, amount=amount, category_id=category_id, date=date, category_name=category_name)
        expense.save(current_user.username)

        flash('Expense form submitted successfully!', 'success')

        # Redirect to the expense list page after successful form submission
        return redirect(url_for('tracker.list_expenses'))

    # Render the expense form page with the form
    return render_template('expense_form.html', form=form)

@bp.route('/edit_expense/<expense_id>', methods = ['GET', 'POST'])
@login_required
def edit_expense(expense_id: str):
    """
    Render the page for editing an existing expense and handle the form submission.

    Parameters:
    - expense_id (str): The unique identifier of the expense to be edited.

    Returns:
    render_template or redirect: Renders the 'expense_form.html' template with the expense form
        or redirects to the expense list page after successful form submission.
    """
    # Retrieve all categories for the current user
    categories = Category.get_all_categories_from_user(current_user.username)

    # Retrieve the expense to be edited
    expense = Expense.get_expense_from_user(username=current_user.username, expense_id=expense_id)

    # Populate the form with the existing expense data
    form = ExpenseForm(obj=expense)
    form.category.choices = generate_form_select_field(categories)

    if form.validate_on_submit():
        # Retrieve form data for the updated expense
        new_description = form.description.data
        new_amount = form.amount.data
        new_category_id = form.category.data
        new_category_name = dict(form.category.choices).get(new_category_id)

        # Validate the amount to be a positive number
        if not Decimal(new_amount) > 0:
            flash('Amount must be a positive number.', 'danger')
        else:
            # Create an Expense instance and update it in the database
            expense = Expense(id=expense_id, description=new_description, amount=new_amount, category_id=new_category_id, category_name=new_category_name)
            expense.update(current_user.username)

            flash('Expense form submitted successfully!', 'success')
            # Redirect to the expense list page after successful form submission
            return redirect(url_for('tracker.list_expenses'))
        
    # Render the expense form page with the form
    return render_template('expense_form.html', form=form)
    
@bp.route('/delete_expense/<expense_id>', methods = ['GET'])
@login_required
def delete_expense(expense_id: str):
    """
    Delete an expense and redirect to the expense list page.

    Parameters:
    - expense_id (str): The unique identifier of the expense to be deleted.

    Returns:
    redirect: Redirects to the expense list page after deleting the expense.
    """
    # Attempt to delete the expense and get the result
    result = Expense.delete_category(username=current_user.username, expense_id=expense_id)
    
    if result == 1:
        flash('Expense deleted successfully!', 'success')
    else:
        flash('Expense not found or unable to delete.', 'danger')

    # Redirect to the expense list page
    return redirect(url_for('tracker.list_expenses'))


@bp.route('/add_category', methods = ['GET', 'POST'])
@login_required
def add_category():
    """
    Render the page for adding a new category and handle the form submission.

    Returns:
    render_template or redirect: Renders the 'category_form.html' template with the category form
        or redirects to the category list page after successful form submission.
    """
    form = CategoryForm()

    if form.validate_on_submit():
        # Generate a new ID and retrieve form data
        new_id = str(ObjectId())
        name = form.name.data.strip()
        budget = form.budget.data

        # Validate that the budget is a positive number
        if not Decimal(budget) > 0:
            flash('Budget must be a positive number.', 'danger')
            return render_template('category_form.html', form=form)

        # Validate that the category name is unique for the user
        if Category.validate_unique_category_name(username=current_user.username, category_name=name):
            # Create a Category instance and save it to the database
            category = Category(id=new_id, name=name, budget=budget)
            category.save(current_user.username)

            flash('Category form submitted successfully!', 'success')

            # Redirect to the category list page after successful form submission
            return redirect(url_for('tracker.list_categories'))
        
        flash(f'Category "{name}" already exists.', 'info')
    
    # Render the category form page with the form
    return render_template('category_form.html', form=form)

@bp.route('/edit_category/<category_id>', methods = ['GET', 'POST'])
@login_required
def edit_category(category_id: str):
    """
    Render the page for editing an existing category and handle the form submission.

    Parameters:
    - category_id (str): The unique identifier of the category to be edited.

    Returns:
    render_template or redirect: Renders the 'category_form.html' template with the category form
        or redirects to the category list page after successful form submission.
    """
    # Retrieve the category to be edited
    category = Category.get_category_from_user(username=current_user.username, category_id=category_id)

    # Populate the form with the existing category data
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        # Retrieve form data for the updated category
        new_name = form.name.data.strip()
        new_budget = form.budget.data

        # Validate that the budget is a positive number
        if not Decimal(new_budget) > 0:
            flash('Budget must be a positive number.', 'danger')
        # Validate that the new name is unique (if changed)
        elif new_name != category.name and not Category.validate_unique_category_name(username=current_user.username, category_name=new_name):
            flash(f'Category "{new_name}" already exists.', 'info')
        else:
            # Create a Category instance and update it in the database
            category = Category(id=category_id, name=new_name, budget=new_budget)
            category.update(current_user.username)

            flash('Category form submitted successfully!', 'success')
             # Redirect to the category list page after successful form submission
            return redirect(url_for('tracker.list_categories'))
    # Render the category form page with the form
    return render_template('category_form.html', form=form)

@bp.route('/delete_category/<category_id>', methods = ['GET'])
@login_required
def delete_category(category_id: str):
    """
    Delete a category and redirect to the category list page.

    Parameters:
    - category_id (str): The unique identifier of the category to be deleted.

    Returns:
    redirect: Redirects to the category list page after deleting the category.
    """
    # Check if there are no associated expenses with the category
    if Expense.verify_expense_with_category(username=current_user.username, category_id=category_id):
        # Attempt to delete the category and get the result
        result = Category.delete_category(username=current_user.username, category_id=category_id)
        
        if result == 1:
            flash('Category deleted successfully!', 'success')
        else:
            flash('Category not found or unable to delete.', 'danger')
    else:
        flash('Can\'t delete Category with Expenses. ', 'warning')

    # Redirect to the category list page
    return redirect(url_for('tracker.list_categories'))

@bp.route('/categories', methods = ['GET'])
@login_required
def list_categories():
    """
    Render the page displaying a list of categories for the authenticated user.

    Returns:
    render_template: Renders the 'category_list.html' template with the user's categories.
    """
    # Retrieve all categories for the current user
    categories = Category.get_all_categories_from_user(current_user.username)
    
    # Render the category list page with the categories
    return render_template('category_list.html', categories=categories)