import matplotlib
from io import BytesIO
import base64


matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_expense_by_category_pie_chart(categories, expenses):
    """
    Generate a pie chart representing the distribution of expenses by category.

    Parameters:
    - categories (List[str]): A list of category names.
    - expenses (List[float]): A list of corresponding expense amounts.

    Returns:
    str: Base64-encoded PNG image of the generated pie chart.

    Example:
    categories = ['Groceries', 'Dining', 'Entertainment']
    expenses = [50.0, 30.0, 20.0]
    pie_chart_image = generate_expense_by_category_pie_chart(categories, expenses)
    # Use the pie_chart_image in HTML or other contexts to display the chart.
    """
    plt.pie(expenses, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title('Expense Distribution by Category')
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')
    plt.close()

    return encoded_image