from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, SubmitField, PasswordField, BooleanField, SelectField, TextField\
, DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email
from . models import Branch, User, Item

import datetime


class SignUpForm(FlaskForm):
    username = TextField('User Name', validators= [ DataRequired(), Length(min=5)])
    password = PasswordField('Password',validators=[ DataRequired(), Length(min=5)])
    # user_active = BooleanField('User Active', validators=[ DataRequired()])
    userAccess = SelectField('User Access', validators= [DataRequired()])
    branchArea = SelectField('Branch Area', validators=[DataRequired()])
    branchOutletOrNot = SelectField('Branch Type', choices=[('1', 'Shop'), ('0', 'Storage')],\
    validators= [DataRequired()])
    branchUnitName = SelectField('Branch Unit')
    # user_mobile = TextField('User Mobile', validators= [ DataRequired()])
    submit = SubmitField('Sign Up')

    def validate(self):
        userLog = User.query.filter(User.username == self.username.data).first()
        if userLog:
            return [False, "Username duplicate"]
        elif self.userAccess.data == 'U':
            branchLog = Branch.query.filter(Branch.branchArea == self.branchArea.data.lower(), \
            Branch.branchUnitName == self.branchUnitName.data.lower()).first()
            if branchLog is None:
                return [False, "Branch unit in the selected area does not exists"]
            else:
                return [True, branchLog.branchId]
        elif self.userAccess.data == 'M':
            branchLog = Branch.query.filter(Branch.branchArea == self.branchArea.data.lower()).first()
            return [True, branchLog.branchId]


class SignInForm(FlaskForm):
    username = TextField('User Name', validators= [ DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators = [DataRequired(), Length(min=6, max=30)])
    submit = SubmitField('Sign In')


class FillingForm(FlaskForm):
    branchArea = SelectField('Branch Area', validators=[DataRequired()])
    branchOutletOrNot = SelectField('Branch Type', choices=[('1', 'Shop'), ('0', 'Storage')],\
    validators= [DataRequired()])
    branchUnitName = SelectField('Branch Name')
    addOrRemove = SelectField('Add or Remove', choices=[('0', 'Add/Update'), ('1', 'Remove')],\
    validators= [DataRequired()])
    locationCheck = SubmitField('Lock Parameters')

    # removeReason = SelectField('Reason to Remove', choices=[('0', 'Expired/Faulty'), ('1', \
    removeReason = TextField('Reason to Remove', validators=[DataRequired()])
    existingItemBarcode = SelectField('Existing Item Barcode')
    newItemBarCode = TextField('New Item Barcode')
    itemName = TextField('New Item Name')
    itemGST = TextField('New Item GST')
    #add expiry date validation when adding element
    expiryDate = TextField('Expiry Date')
    expiryDateSel = SelectField('Expiry Date Selection')
    updatePrice = TextField('Updated Price')
    itemQuantity = TextField('Add/Remove Quantity')
    submit = SubmitField('Submit')

    def validate(self):
        if self.expiryDate.data != '':
            try:
                year, month, day = self.expiryDate.data.split('-')
                if len(year) != 4:
                    raise ValueError("")
                date = datetime.datetime(int(year),int(month),int(day))
                if datetime.datetime.now() > date:
                    raise ValueError("")
            except ValueError :
                return "Expiry Date not in proper format or less than today"
        if self.existingItemBarcode.data == '0' and self.newItemBarCode.data == '':
            return "Either do Select or fill new item barcode"
        elif self.newItemBarCode.data != '':
            if self.itemName.data == '' or self.updatePrice.data == '' or self.itemGST.data == '':
                return "New Item bar code requires its item name and updated price and Item GST"
            if Item.query.filter(Item.itemBarcode == self.newItemBarCode.data).first():
                return "New Item barcode entered already exists"
        if self.addOrRemove.data == '1' and self.existingItemBarcode.data == '0':
            return "select an item to remove"
        return True

class BranchForm(FlaskForm):
    branchArea = TextField('Branch Area', validators=[DataRequired()])
    branchOutletOrNot = SelectField('Branch Type', choices=[('1', 'Shop'), ('0', 'Storage')],\
    validators= [DataRequired()])
    branchUnitName = TextField('Branch Name', validators=[DataRequired()])
    submit = SubmitField('Add Branch')

    def validate(self):
        branchLog = Branch.query.filter(Branch.branchArea == self.branchArea.data.lower()).\
        filter(Branch.branchUnitName == self.branchUnitName.data.lower()).first()
        if branchLog is not None:
            return "Area Name or Unit Name already exists"
        return True


class BillForm(FlaskForm):
    customerName = TextField('Customer Name', validators=[DataRequired()])
    itemBarcode = SelectField('Item Barcode ',validators=[DataRequired()])
    itemQuantity = TextField('Item Quantity', validators=[DataRequired()])
    next = SubmitField('Proceed')
    submit = SubmitField('Bill')


class SearchInventoryForm(FlaskForm):
    branchAreaName = SelectField('Area Name')
    branchUnitName = SelectField('Unit Name')
    itemBarcode = SelectField('Item Barcode')
    itemName = SelectField('Item Name')
    expiryDate = SelectField('Expiry Date')
    branchOutletOrNot = SelectField('Branch Type', choices=[('1', 'Shop'), ('0', 'Storage')],\
    validators= [DataRequired()])
    submit = SubmitField('Search Inventory')
