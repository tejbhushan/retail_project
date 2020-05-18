from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, SubmitField, PasswordField, BooleanField, SelectField, TextField\
, DateField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email
from . models import Branch, User


class SignUpForm(FlaskForm):
    username = TextField('User Name', validators= [ DataRequired(), Length(min=5)])
    password = PasswordField('Password',validators=[ DataRequired(), Length(min=5)])
    # user_active = BooleanField('User Active', validators=[ DataRequired()])
    userAccess = SelectField('User Access', validators= [DataRequired()])
    selBranchType = SelectField('Branch Type', choices=[('0', 'Shop'), ('1', 'Stock House')],\
     validators= [DataRequired()])
    branchArea = SelectField('Branch Area', validators=[DataRequired()])
    branchUnitName = SelectField('Branch Unit')
    # user_mobile = TextField('User Mobile', validators= [ DataRequired()])
    submit = SubmitField('Sign Up')

    def validate(self):
        userLog = User.query.filter(User.username == self.username.data).first()
        if userLog:
            return [False, "Username duplicate"]
        elif self.userAccess.data == 'U':
            branchLog = Branch.query.filter(Branch.branchArea == self.branchArea.data.lower(), \
            Branch.branchUnitName == self.branchUnitName.data.lower(), Branch.branchShopOrStockHouse\
            == self.selBranchType.data).first()
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
    selBranchType = SelectField('Branch Type', choices=[('0', 'Shop'), ('1', 'Stock House')],\
    validators= [DataRequired()])
    branchUnitName = SelectField('Branch Name', validators=[DataRequired()])
    addOrRemove = SelectField('Add or Remove', choices=[('0', 'Add/Update'), ('1', 'Remove')],\
    validators= [DataRequired()])

    existingItemBarCode = SelectField('Existing Item Barcode')
    newItemBarCode = TextField('New Item Barcode')
    itemName = TextField('New Item Name')
    #add expiry date validation when adding element
    expiryDate = DateField('Expiry Date', format='%d-%m-%Y')
    updatePrice = TextField('Updated Price')
    itemQuantity = TextField('Add/Remove Quantity')
    submit = SubmitField('Submit')

    def validate(self):
        if self.existingItemBarCode.data != '0' and self.newItemBarCode.data != '':
            return "Either do Select or fill new item barcode"
        elif self.existingItemBarCode.data == '0' and self.newItemBarCode.data == '':
            return " Select and fill new item barcode cannot be filled at same time"
        elif self.newItemBarCode.data != '' and self.itemName.data == '':
            return "New Item bar code requires its item name to be filled"
        elif self.updatePrice.data == '' and self.itemQuantity.data == '':# and self.itemName.data == '':
            return "atleast one should be filled between updated Price or Item Quantity"
        return True

class BranchForm(FlaskForm):
    branchArea = TextField('Branch Area', validators=[DataRequired()])
    selBranchType = SelectField('Branch Type', choices=[('0', 'Shop'), ('1', 'Stock House')],\
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
    shopOrStock = SelectField('ShopOrStock')
    submit = SubmitField('Search Inventory')
