from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class ExpenseForm(FlaskForm):
    description = StringField('Description', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    amount = StringField('Amount', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    category = SelectField('Category', render_kw={'class': 'form-control'}, validators=[DataRequired()])

class CategoryForm(FlaskForm):
    name = StringField('Name', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    budget = StringField('Budget', render_kw={'class': 'form-control'}, validators=[DataRequired()])