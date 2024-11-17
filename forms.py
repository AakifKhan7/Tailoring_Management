from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SubmitField, SelectField, FloatField, IntegerField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length


class SignUp(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=30)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=30)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=15)])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=20)])
    
    submit = SubmitField("Sign Me Up!")
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(max=30)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=15)])

    submit = SubmitField("Login!")

class AddClient(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=30)])
    street = StringField("Street Address", validators=[DataRequired(), Length(max=100)])
    city = StringField("City", validators=[DataRequired(), Length(max=50)])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    
    submit = SubmitField("Add Client!")
    
    
class EditClientForm(FlaskForm):
    name = StringField('Client Name', validators=[DataRequired(), Length(max=100)])
    street = StringField('Street Address', validators=[Length(max=250)])
    city = StringField('City', validators=[Length(max=15)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    submit = SubmitField('Save Changes')
    
class AddOrder(FlaskForm):
    product_name = StringField("Product", validators=[DataRequired(), Length(max=30)])
    price = IntegerField('Price', validators=[DataRequired()])
    detail = TextAreaField('Detail', validators=[DataRequired()])
    quantity = IntegerField('quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class EditOrderForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Delivered', 'Delivered'), ('Paid', 'Paid')], validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    order_date = DateTimeField('Order Date', format='%d-%m-%Y', validators=[DataRequired()])
    deadline = DateTimeField('Deadline', format='%d-%m-%Y', validators=[DataRequired()])
    submit = SubmitField('Submit')