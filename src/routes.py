from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from . models import User, db, ItemBranchRel, Branch, Item, Bill, Customer
from . forms import SignUpForm, SignInForm, FillingForm, BranchForm, BillForm, SearchInventoryForm
from src import app
import datetime
from sqlalchemy import func


@app.route('/')
def i():
    return redirect(url_for("signin"))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    error = ''
    signinform = SignInForm()
    if request.method == 'POST':
        un = signinform.username.data
        userLog = User.query.filter_by(username=un).first()
        if userLog is not None and userLog.password == signinform.password.data:
            branchLog = Branch.query.filter_by(branchId = userLog.userBranchId).first()
            session['branchUnitName'] = branchLog.branchUnitName if userLog.userAccess == 'U' else 'All'
            session['branchAreaName'] = 'All' if userLog.userAccess == 'O' else branchLog.branchArea
            session['branchOutletOrNot'] = branchLog.branchOutletOrNot if userLog.userAccess == 'U' else 'All'
            session['branchId'] = userLog.userBranchId
            session['userAccess'] = userLog.userAccess
            session['current_user'] = userLog.username
            session['user_available'] = True
            return redirect(url_for('billing'))
        else:
            error = 'invalid creds'
    return render_template('signin.html', signinform=signinform, error=error)


@app.route('/signup/<error>', methods=['GET', 'POST'])
def signup(error):
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    signupform = SignUpForm()
    userHead = ['#', 'Username', 'Branch Area', 'User Access', 'Branch Type', 'Branch Unit', 'Modify']
    if session['userAccess'] == 'O':
        signupform.userAccess.choices = [('M', 'Manager'), ('U', 'User')]
        signupform.branchArea.choices = [(bAN[0], bAN[0]) for bAN in db.session.query(Branch.branchArea).group_by\
        (Branch.branchArea).all()]
        userLog = db.session.query(User.userId, User.username, Branch.branchArea, User.userAccess, Branch.\
        branchOutletOrNot, Branch.branchUnitName).filter(User.userBranchId == Branch.branchId).all()
    elif session['userAccess'] == 'M':
        signupform.userAccess.choices = [('U', 'User')]
        signupform.branchArea.choices = [(session['branchAreaName'], session['branchAreaName'])]
        userLog = db.session.query(User.userId, User.username, Branch.branchArea, User.userAccess, Branch.\
        branchOutletOrNot, Branch.branchUnitName).filter(User.userBranchId == Branch.branchId, \
        User.userAccess == 'U', Branch.branchArea == session['branchAreaName']).all()

    if request.method == 'POST':
        error = signupform.validate_on_submit()
        if error[0] is not True:
            return redirect(url_for('signup', error=error[1]))
        db.session.add(User(signupform.username.data, signupform.password.data, signupform.userAccess.data, error[1]))
        db.session.commit()
        return redirect(url_for('signup', error='success'))

    return render_template('signup.html', signupform=signupform, error=error, userHead=userHead, session=session\
    ,userLog=userLog)


@app.route('/updateInventory/<error>', methods=['GET', 'POST'])
def updateInventory(error):
    if session['user_available'] is False:
        return redirect(url_for('signin'))

    fillingform = FillingForm()
    fillingform.branchArea.choices = [(session['branchAreaName'], session['branchAreaName'])]
    if session['userAccess'] == 'O':
        fillingform.branchArea.choices = [(bAN[0], bAN[0]) for bAN in db.session.query(Branch.branchArea).group_by\
        (Branch.branchArea).all()]
    elif session['userAccess'] == 'U':
        fillingform.branchOutletOrNot.choices = [('1', 'Shop')] if session['branchOutletOrNot'] == '1' else [('2', 'Storage')]

    if 'setBranchArea' in session:
        # print(session['setBranchArea'], session['setBranchOutletOrNot'], session['setBranchUnitName'], session['setAddOrRemove'])
        branchLog = Branch.query.filter(Branch.branchArea == session['setBranchArea'], Branch.branchOutletOrNot == \
        session['setBranchOutletOrNot'], Branch.branchUnitName == session['setBranchUnitName']).first()
        # print(branchLog.branchId)
        fillingform.existingItemBarcode.choices = [('0', 'Select')] + [(ibcodes, iNames) for ibcodes, iNames \
        in db.session.query(Item.itemBarcode, Item.itemName).filter(ItemBranchRel.relItemId == Item.itemId, \
        ItemBranchRel.relBranchId == branchLog.branchId).group_by(ItemBranchRel.relItemId).all()]

    if request.method == 'POST':
        if fillingform.locationCheck.data:
            session['setBranchArea'] = request.form['branchArea']
            session['setBranchOutletOrNot'] = request.form['branchOutletOrNot']
            session['setBranchUnitName'] = request.form['branchUnitName']
            session['setAddOrRemove'] = request.form['addOrRemove']
            return redirect(url_for('updateInventory', error='Parameters Fix'))
        elif fillingform.submit.data:
            error = fillingform.validate_on_submit()
            if error is not True:
                return redirect(url_for('updateInventory', error=error))
            else:
                if fillingform.existingItemBarcode.data != '0':
                    if fillingform.expiryDateSel.data == 'null':
                        fillingform.expiryDateSel.data = None
                    item = Item.query.filter(Item.itemBarcode == fillingform.existingItemBarcode.data).first()
                    itemExistInBranchInventory = ItemBranchRel.query.filter(ItemBranchRel.relItemId == item.itemId, ItemBranchRel.\
                    relBranchId == branchLog.branchId, ItemBranchRel.relItemExpiry == fillingform.expiryDateSel.data).first()
                    if fillingform.updatePrice.data != '':
                        itemExistInBranchInventory.relItemPrice = fillingform.updatePrice.data
                    if fillingform.itemName.data != '':
                        item.itemName = fillingform.itemName.data.lower()
                    if fillingform.itemGST.data != '':
                        item.itemGST = fillingform.itemGST.data
                    if fillingform.itemQuantity.data != '':
                        if fillingform.addOrRemove.data == '0':
                            itemExistInBranchInventory.relItemAvailableQuantity = str(int(itemExistInBranchInventory\
                            .relItemAvailableQuantity) + int(fillingform.itemQuantity.data))
                        elif int(itemExistInBranchInventory.relItemAvailableQuantity) > int(fillingform.itemQuantity.data):
                            itemExistInBranchInventory.relItemAvailableQuantity = str(int(itemExistInBranchInventory\
                            .relItemAvailableQuantity) - int(fillingform.itemQuantity.data))
                        else:
                            return redirect(url_for('updateInventory', error='available quantity is less than removing quantity'))
                    itemExistInBranchInventory.relLastfillDateTime = datetime.datetime.now().strftime('%Y-%m-%d')
                else:
                    if fillingform.expiryDate.data == '':
                        fillingform.expiryDate.data = None
                    item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarCode.data).first()
                    #item table itself doesnot have, hence feed to item table first
                    if item is None:
                        db.session.add(Item(fillingform.itemName.data.lower(), fillingform.itemGST.data, fillingform.newItemBarCode.data))
                        db.session.commit()
                        item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarCode.data).first()
                    db.session.add(ItemBranchRel(item.itemId, branchLog.branchId, fillingform.updatePrice.data,\
                    fillingform.itemQuantity.data, fillingform.expiryDate.data, datetime.datetime.now().strftime('%Y-%m-%d')))
                db.session.commit()
                return redirect(url_for('updateInventory', error='success'))

    available_stockHead = ['Item Barcode', 'Item Name', 'Item GST', 'Item price', 'Item Expiry', 'Item Available Quantity']
    available_stock = None
    if 'setBranchArea' in session:
        available_stock = db.session.query(Item.itemBarcode, Item.itemName, Item.itemGST, ItemBranchRel.relItemPrice, ItemBranchRel.relItemExpiry,\
        ItemBranchRel.relItemAvailableQuantity).filter(ItemBranchRel.relItemId == Item.itemId, ItemBranchRel.relBranchId == \
        branchLog.branchId).group_by(ItemBranchRel.relItemId, ItemBranchRel.relItemExpiry).all()
    # print(available_stock)


    return render_template('updateInventory.html', fillingform=fillingform, error=error, session=session, available_stockHead=available_stockHead,\
    available_stock=available_stock)


@app.route('/searchInventory/<error>', methods=['GET', 'POST'])
def searchInventory(error):
    if session['user_available'] is False:
        return redirect(url_for('signin'))

    searchInventoryForm = SearchInventoryForm()
    searchInventoryForm.branchAreaName.choices = [(bl[0], bl[0]) for bl in db.session.query(Branch.branchArea).\
    group_by(Branch.branchArea).all()]
    searchInventoryForm.branchUnitName.choices = [(bl[0], bl[0]) for bl in db.session.query(Branch.branchUnitName).\
    group_by(Branch.branchUnitName).all()]
    searchInventoryForm.branchOutletOrNot.choices = [('1', 'Shop'), ('0', 'Storage')]
    searchInventoryForm.itemBarcode.choices = [(bl[0], bl[0]) for bl in db.session.query(Item.itemBarcode).\
    group_by(Item.itemBarcode).all()]
    searchInventoryForm.itemName.choices = [(bl[0], bl[0]) for bl in db.session.query(Item.itemName).\
    group_by(Item.itemName).all()]
    searchInventoryForm.expiryDate.choices = [(bl[0], bl[0]) for bl in db.session.query(ItemBranchRel.relItemExpiry).\
    group_by(ItemBranchRel.relItemExpiry).all()]
    if request.method == 'POST':
        pass

    # available_stockHead = ['Item Barcode', 'Item Name', 'Branch Address', 'Item price', 'Item Available Quantity']
    # available_stock = [[]]
    # if session['branchAreaName'] == 'All':
    #     available_stock = db.session.query(Item.itemBarcode, Item.itemName, \
    #     Branch.branchAddress, ItemBranchRel.relItemPrice, ItemBranchRel.relItemAvailableQuantity).\
    #     filter(ItemBranchRel.relItemId == Item.itemId).filter(ItemBranchRel.relBranchId == Branch.branchId)\
    #     .group_by(ItemBranchRel.relBranchId, ItemBranchRel.relItemBranchId).all()
    # else:
    #     available_stock = db.session.query(Item.itemBarcode, Item.itemName, Branch.branchAddress\
    #     , ItemBranchRel.relItemPrice, ItemBranchRel.relItemAvailableQuantity).\
    #     filter(ItemBranchRel.relItemId == Item.itemId).filter(ItemBranchRel.relBranchId == Branch.branchId)\
    #     .filter(ItemBranchRel.relBranchId == session['branchId']).\
    #     group_by(ItemBranchRel.relBranchId, ItemBranchRel.relItemBranchId).all()
    #
    #
    # if session['branchAreaName'] == 'All':
    #     return render_template('updateInventory.html', user=session['current_user'], userAccess=session['userAccess'],\
    #      areaName=session['branchAreaName'], error1='For filling, sign in with specific branch', available_stockHead\
    #      =available_stockHead, available_stock=available_stock)

    return render_template('searchInventory.html', searchInventoryForm=searchInventoryForm, session=session, error=error)


@app.route('/billing', methods=['GET', 'POST'])
def billing(listItems = []):
    if session['user_available'] is False:
        return redirect(url_for('signin'))

    query = db.session.query(Item.itemBarcode).filter(ItemBranchRel.relItemId == Item.itemId).\
    filter(ItemBranchRel.relBranchId == session['branchId']).all()
    if query is None:
        return render_template('branch.html', user=session['current_user'], userAccess=session['userAccess'],\
         areaName=session['branchAreaName'], error='No Stock')

    userId = User.query.filter(User.username == session['current_user']).first().userId
    billform = BillForm()
    billform.itemBarcode.choices = [(bcodes[0], bcodes[0]) for bcodes in query]
    if request.method == 'POST':
        if billform.next.data:
            item = Item.query.filter(Item.itemBarcode == billform.itemBarcode.data).first()
            itemrel = db.session.query(ItemBranchRel).filter(ItemBranchRel.relItemId ==\
            item.itemId).filter(ItemBranchRel.relBranchId == session['branchId']).first()
            total=listItems[-1][4] if listItems else 0
            listItems.append([billform.itemBarcode.data, item.itemName, itemrel.relItemPrice\
            , billform.itemQuantity.data, total + int(itemrel.relItemPrice)*int(billform.itemQuantity.data)])
            itemrel.relItemAvailableQuantity = str(int(itemrel.relItemAvailableQuantity) - int(billform.itemQuantity.data))
            db.session.commit()
        if billform.submit.data:
            try:
                customerId = Customer.query.filter(Customer.customerName == billform.customerName.data).first().customerId
            except Exception as e:
                customerId = 0
            row = ''
            for list in listItems:
                row += '('+list[1]+':'+list[2]+':'+list[3]+')'
            print(row)
            db.session.add(Bill(userId, session['branchId'], customerId, row, listItems[-1][4]))
            db.session.commit()
            listItems.clear()
            return redirect(url_for('billing'))
    return render_template('billing.html', session=session, billform=billform, listItems=listItems,\
    total=listItems[-1][4] if listItems else 0)



@app.route('/branch/<error>', methods=['GET', 'POST'])
def branch(error):
    branchform = BranchForm()
    branchHead = ['#', 'Area', 'Type', 'Branch Name', 'Modify']
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    if session['userAccess'] == 'U':
        return render_template('branch.html', user=session['current_user'], userAccess=session['userAccess'],\
         areaName=session['branchAreaName'], error='User cannot modify branch')
    elif session['userAccess'] == 'M':
        branchform.branchArea.data = session['branchAreaName']
        branchLog1 = db.session.query(Branch.branchCode, Branch.branchArea, Branch.branchOutletOrNot,\
        Branch.branchUnitName).filter(Branch.branchArea == session['branchAreaName']).all()
    elif session['userAccess'] == 'O':
        branchLog1 = db.session.query(Branch.branchCode, Branch.branchArea, Branch.branchOutletOrNot,\
        Branch.branchUnitName).all()

    newBranchCode = '1'
    branchLog = Branch.query.first()
    if branchLog is not None:
        newBranchCode = str(int(db.session.query(func.max(Branch.branchCode)).first()[0]) + 1)

    if request.method == 'POST':
        error = branchform.validate_on_submit()
        if error is not True:
            return redirect(url_for('branch', error=error))
        else:
            db.session.add(Branch(newBranchCode, branchform.branchArea.data.lower(), branchform.branchOutletOrNot.data, \
            branchform.branchUnitName.data.lower()))
            db.session.commit()
            return redirect(url_for('branch', error="success"))


    return render_template('branch.html', newBranchCode=newBranchCode, branchform=branchform, error=error, \
     branchLog=branchLog1, branchHead=branchHead, session=session)


@app.route('/sales')
def sales():
    if session['user_available'] is False:
        return redirect(url_for('signin'))

    salesHead = ['#', 'Customer Name', 'List', 'Total', 'DateTime']
    if session['branchAreaName'] == 'All':
        salesDone = db.session.query(Bill.billId, Customer.customerName, \
        Bill.billList, Bill.billAmount, Bill.billDateTime).all()
    else:
        salesDone = db.session.query(Bill.billId, Customer.customerName, \
        Bill.billList, Bill.billAmount, Bill.billDateTime)\
        .filter(Bill.billBranchId == session['branchId']).all()

    return render_template('sales.html', session=session, salesHead=salesHead, salesDone=salesDone)




@app.route('/logout')
def logout():
    session.clear()
    session['user_available'] = False
    return redirect(url_for('signin'))











#functions for dynamic select fields
@app.route('/branchUnitName/<branchArea>/<branchOutletOrNot>')
def branchUnitNameWithOutletFilter(branchArea, branchOutletOrNot):
    if session['userAccess'] == 'U':
        return jsonify({'branchUnitNames': [{'id': session['branchUnitName'], 'name': session['branchUnitName']}]})
    branchUnitNames = Branch.query.filter(Branch.branchArea == branchArea, Branch.branchOutletOrNot == \
    branchOutletOrNot).all()
    branchUnitNameArray = []
    for branchUnitName in branchUnitNames:
        branchUnitNameDict = {}
        branchUnitNameDict['id'] = branchUnitName.branchUnitName
        branchUnitNameDict['name'] = branchUnitName.branchUnitName
        branchUnitNameArray.append(branchUnitNameDict)
    return jsonify({'branchUnitNames': branchUnitNameArray})

#function to get expiryDate of an item dynamically
@app.route('/expiryDate/<itemBarcode>')
def expiryDate(itemBarcode):
    branchLog = Branch.query.filter(Branch.branchArea == session['setBranchArea'], Branch.branchOutletOrNot == \
    session['setBranchOutletOrNot'], Branch.branchUnitName == session['setBranchUnitName']).first()
    expiryDates = db.session.query(ItemBranchRel.relItemExpiry).filter(ItemBranchRel.relBranchId == branchLog.branchId,\
    ItemBranchRel.relItemId == Item.itemId, Item.itemBarcode == itemBarcode).group_by(ItemBranchRel.relItemExpiry).all()
    print(expiryDates)
    expiryDatesArray = []
    for expiryDate in expiryDates:
        expiryDateDict = {}
        expiryDateDict['id'] = expiryDate[0].strftime('%Y-%m-%d') if expiryDate[0] else expiryDate[0]
        expiryDateDict['name'] = expiryDate[0].strftime('%Y-%m-%d') if expiryDate[0] else expiryDate[0]
        expiryDatesArray.append(expiryDateDict)
    return jsonify({'expiryDates': expiryDatesArray})




# if __name__ == '__main__':
#     app.run()
