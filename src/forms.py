from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, SubmitField, PasswordField, BooleanField, SelectField, TextField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email


class SignUpForm(FlaskForm):
    username = TextField('User Name', validators= [ DataRequired(), Length(min=5)])
    password = PasswordField('Password',validators=[ DataRequired(), Length(min=5)])
    # user_active = BooleanField('User Active', validators=[ DataRequired()])
    user_access = SelectField('User Access', validators= [DataRequired()])
    user_mobile = TextField('User Mobile', validators= [ DataRequired()])
    submit = SubmitField('Sign Up')


class SignInForm(FlaskForm):
    username = TextField('User Name', validators= [ DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators = [DataRequired(), Length(min=6, max=30)])
    selBranchCode = SelectField('Branch Code', validators= [DataRequired()])
    submit = SubmitField('Sign In')


class FillingForm(FlaskForm):
    existingItemBarCode = SelectField('Existing Item Barcode')
    newItemBarCode = TextField('New Item Barcode')
    itemName = TextField('Item Name')
    updatePrice = TextField('Updated Price')
    itemQuantity = TextField('Item Import Quantity')
    submit = SubmitField('Add Item')

    def validate(self):
        if (self.existingItemBarCode.data != '0' and self.newItemBarCode.data != ''):
            return "Either do Select or fill new item barcode"
        elif (self.existingItemBarCode.data == '0' and self.newItemBarCode.data == ''):
            return " Select and fill new item barcode cannot be filled at same time"
        elif self.newItemBarCode.data != '' and self.itemName.data == '':
            return "New Item bar code requires its item name to be filled"
        elif self.updatePrice.data == '' and self.itemQuantity.data == '':# and self.itemName.data == '':
            return "atleast one should be filled between updated Price or Item Quantity"
        return True

class BranchForm(FlaskForm):
    branchCode = SelectField('Branch Code')
    branchAddress = TextField('Branch Address', validators=[DataRequired()])
    submit = SubmitField('Add Branch')


class BillForm(FlaskForm):
    customerName = TextField('Customer Name', validators=[DataRequired()])
    itemBarcode = SelectField('Item Barcode ')
    itemQuantity = TextField('Item Quantity', validators=[DataRequired()])
    next = SubmitField('Proceed')
    submit = SubmitField('Bill')
