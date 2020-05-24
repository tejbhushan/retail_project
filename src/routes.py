from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from . models import User, db, ItemBranchRel, Branch, Item, Bill, BillDetails
from . forms import SignUpForm, SignInForm, FillingForm, BranchForm, BillForm, SearchInventoryForm, BillDetailsForm, SalesForm
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
            return redirect(url_for('billing', error='success'))
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
        fillingform.branchOutletOrNot.choices = [('B', 'Shop')] if session['branchOutletOrNot'] == 'B' else [('N', 'Storage')]

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
            return redirect(url_for('updateInventory', error='Parameters Fixed'))
        elif fillingform.submit.data:
            error = fillingform.validate(branchLog.branchId)
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
                        elif int(itemExistInBranchInventory.relItemAvailableQuantity) >= int(fillingform.itemQuantity.data):
                            itemExistInBranchInventory.relItemAvailableQuantity = str(int(itemExistInBranchInventory\
                            .relItemAvailableQuantity) - int(fillingform.itemQuantity.data))
                        else:
                            return redirect(url_for('updateInventory', error='available quantity is less than removing quantity'))
                    itemExistInBranchInventory.relLastfillDateTime = datetime.datetime.now().strftime('%Y-%m-%d')
                    if itemExistInBranchInventory.relItemAvailableQuantity == '0':
                        db.session.delete(itemExistInBranchInventory)
                else:
                    if fillingform.expiryDate.data == '':
                        fillingform.expiryDate.data = None
                    item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarcode.data).first()
                    #item table itself doesnot have, hence feed to item table first
                    if item is None:
                        db.session.add(Item(fillingform.itemName.data.lower(), fillingform.itemGST.data, fillingform.newItemBarcode.data))
                        db.session.commit()
                        item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarcode.data).first()
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

    available_stockHead = ['Branch Area', 'Branch Type', 'Branch Unit Name', 'Item Barcode', 'Item Name', 'Item GST', 'Item price', 'Item Expiry'\
    , 'Item Available Quantity']
    available_stock = db.session.query(Branch.branchArea, Branch.branchOutletOrNot, Branch.branchUnitName, Item.itemBarcode, Item.itemName,\
     Item.itemGST, ItemBranchRel.relItemPrice, ItemBranchRel.relItemExpiry, ItemBranchRel.relItemAvailableQuantity).filter(ItemBranchRel.relBranchId \
     == Branch.branchId, ItemBranchRel.relItemId == Item.itemId).group_by(ItemBranchRel.relItemBranchId).all()

    searchInventoryForm = SearchInventoryForm()
    searchInventoryForm.branchArea.choices = [(None, 'All')] + [(branchArea[0], branchArea[0]) for branchArea in \
    db.session.query(Branch.branchArea).group_by(Branch.branchArea).all()]
    searchInventoryForm.branchUnitName.choices = [(None, 'All')] + [(branchUnitName[0], branchUnitName[0]) for branchUnitName in \
    db.session.query(Branch.branchUnitName).group_by(Branch.branchUnitName).all()]
    searchInventoryForm.itemBarcode.choices = [(None, 'All')] + [(ibcodes[0], ibcodes[0]) for ibcodes in db.session.query(Item.itemBarcode).all()]
    searchInventoryForm.itemName.choices = [(None, 'All')] + [(iNames[0], iNames[0]) for iNames in db.session.query(Item.itemName).all()]

    if request.method == 'POST':
        # print(searchInventoryForm.branchArea.data, searchInventoryForm.branchOutletOrNot.data, searchInventoryForm.branchUnitName.data,\
        # searchInventoryForm.itemBarcode.data, searchInventoryForm.itemName.data)
        error = searchInventoryForm.validate()
        if error is not True:
            return redirect(url_for('searchInventory', error=error))
        else:
            available_stock = db.session.query(Branch.branchArea, Branch.branchOutletOrNot, Branch.branchUnitName, Item.itemBarcode, Item.itemName,\
             Item.itemGST, ItemBranchRel.relItemPrice, ItemBranchRel.relItemExpiry, ItemBranchRel.relItemAvailableQuantity).filter(ItemBranchRel.\
             relBranchId == Branch.branchId, ItemBranchRel.relItemId == Item.itemId)
            if searchInventoryForm.branchArea.data != 'None':
                available_stock = available_stock.filter(Branch.branchArea == searchInventoryForm.branchArea.data)
                # print(available_stock.all())
            if searchInventoryForm.branchOutletOrNot.data != 'None':
                available_stock = available_stock.filter(Branch.branchOutletOrNot == searchInventoryForm.branchOutletOrNot.data)
            if searchInventoryForm.branchUnitName.data != 'None':
                available_stock = available_stock.filter(Branch.branchUnitName == searchInventoryForm.branchUnitName.data)
            if searchInventoryForm.itemBarcode.data != 'None':
                available_stock = available_stock.filter(Item.itemBarcode == searchInventoryForm.itemBarcode.data)
            if searchInventoryForm.itemName.data != 'None':
                available_stock = available_stock.filter(Item.itemName == searchInventoryForm.itemName.data)
            if searchInventoryForm.expiryAfterOrBefore.data != 'None':
                if searchInventoryForm.expiryAfterOrBefore.data == '0':#before
                    available_stock = available_stock.filter(ItemBranchRel.relItemExpiry <= searchInventoryForm.expiryDate.data)
                else:
                    available_stock = available_stock.filter(ItemBranchRel.relItemExpiry > searchInventoryForm.expiryDate.data)
            available_stock = available_stock.all()
            # print(available_stock)
            error = 'success'

    return render_template('searchInventory.html', searchInventoryForm=searchInventoryForm, session=session, error=error, available_stockHead=\
    available_stockHead, available_stock=available_stock)

#TODO remove this if multiple clients and check for session alternatives
billDetailList = []
index = [0]
@app.route('/billing/<error>', methods=['GET', 'POST'])
def billing(error='success'):
    global billDetailList, index
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    elif session['userAccess'] != 'U':
        return redirect(url_for('sales', error='user only can bill'))
    branchId = session['branchId']
    billform = BillForm()
    billform.itemBarcode.choices = [('None', 'None')] + [(ibcodes[0], ibcodes[0]) for ibcodes in db.session.query(Item.itemBarcode).all()]
    billform.itemName.choices = [('None', 'None')] + [(iNames[0], iNames[0]) for iNames in db.session.query(Item.itemName).all()]
    totalPriceAndQuantity = [0, 0]
    #donot remove
    # for i, blist in enumerate(billDetailList):
    #     if blist[1].itemQuantity.data == '0':
    #         billDetailList.pop(i)
    #         break

    if request.method == 'POST':
        if billform.next.data:
            error = billform.validate()
            if error != 'success':
                return redirect(url_for('billing', error=error))
            if billform.itemBarcode.data != 'None':
                item = Item.query.filter(Item.itemBarcode == billform.itemBarcode.data).first()
            elif billform.itemName.data != 'None':
                item = Item.query.filter(Item.itemName == billform.itemName.data).first()
            itemDetails = ItemBranchRel.query.filter(ItemBranchRel.relItemId == item.itemId, ItemBranchRel.\
            relBranchId == branchId)#.first()
            itemAvailableQuantity = '0'
            for details in itemDetails:
                itemAvailableQuantity = str(int(itemAvailableQuantity) + int(details.relItemAvailableQuantity))
            itemDetails = itemDetails.first()
            if int(billform.itemQuantity.data) > int(itemAvailableQuantity):
                return redirect(url_for('billing', error="Ordered Item Quantity not available in store, available quantity is "+itemAvailableQuantity))
            billDetailsForm = BillDetailsForm()
            billDetailsForm.itemBarcode.data = item.itemBarcode
            billDetailsForm.itemName.data = item.itemName
            billDetailsForm.itemGST.data = item.itemGST
            # billDetailsForm.itemName.data = billform.itemName.data
            billDetailsForm.itemPrice.data = itemDetails.relItemPrice
            billDetailsForm.itemQuantity.data = billform.itemQuantity.data
            billDetailsForm.itemTotalPrice.data = str(int(billform.itemQuantity.data) * int(itemDetails.relItemPrice))
            #already existing item in cart
            flag = 0
            for i, blist in enumerate(billDetailList):
                # print(billDetailsForm.itemBarcode.data, blist[1].itemBarcode.data,billDetailsForm.itemName.data,blist[1].itemName.data)
                if billDetailsForm.itemBarcode.data == blist[1].itemBarcode.data or billDetailsForm.itemName.data == blist[1].itemName.data:
                    billDetailList[i][1].itemQuantity.data = str(int(blist[1].itemQuantity.data) + int(billDetailsForm.itemQuantity.data))
                    billDetailList[i][1].itemTotalPrice.data = str(int(blist[1].itemTotalPrice.data) + int(billDetailsForm.itemTotalPrice.data))
                    flag = 1
                    break
            if flag == 0:
                index[0] += 1
                billDetailList.append([index[0], billDetailsForm])
            # print(billDetailList)
        for blist in billDetailList:
            totalPriceAndQuantity[0] += int(blist[1].itemTotalPrice.data)
            totalPriceAndQuantity[1] += int(blist[1].itemQuantity.data)
        print(totalPriceAndQuantity)
        if billform.submit.data:
            if totalPriceAndQuantity[1] != 0:
                userLog = User.query.filter_by(username=session['current_user']).first()
                db.session.add(Bill(userLog.userId, session['branchId'], billform.customerName.data, str(totalPriceAndQuantity[1]), str(totalPriceAndQuantity[0])))
                db.session.commit()
                billId = db.session.query(func.max(Bill.billId)).first()[0]
                for i, blist in enumerate(billDetailList):
                    item = Item.query.filter(Item.itemBarcode == blist[1].itemBarcode.data).first()
                    itemDetails = ItemBranchRel.query.filter(ItemBranchRel.relBranchId == branchId, ItemBranchRel.relItemId == item.itemId).first()
                    db.session.add(BillDetails(billId, item.itemId, itemDetails.relItemPrice, blist[1].itemQuantity.data))
                db.session.commit()
            index[0] = 0
            billDetailList.clear()


    return render_template('billing.html', session=session, billform=billform, billDetailList=billDetailList, totalPriceAndQuantity=totalPriceAndQuantity\
    , error=error)



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


@app.route('/sales/<error>', methods=['GET', 'POST'])
def sales(error):
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    if session['userAccess'] == 'U':
        return redirect(url_for('billing', error='user cannot view sales page'))

    salesHead = ['Bill Number', 'Customer Name', 'User Name', 'Branch Area', 'Branch Type', 'Branch Unit', 'Total Quantity', 'Total Price', 'Date Time']
    salesDone = db.session.query(Bill.billId, Bill.billCustomerName, User.username, Branch.branchArea, Branch.branchOutletOrNot, Branch.branchUnitName\
    , Bill.billQuantity, Bill.billAmount, Bill.billDateTime).filter(Bill.billUserId == User.userId, Bill.billBranchId == Branch.branchId)

    salesForm = SalesForm()
    salesForm.branchArea.choices = [(None, 'All')] + [(branchArea[0], branchArea[0]) for branchArea in \
    db.session.query(Branch.branchArea).group_by(Branch.branchArea).all()]
    salesForm.branchUnitName.choices = [(None, 'All')] + [(branchUnitName[0], branchUnitName[0]) for branchUnitName in \
    db.session.query(Branch.branchUnitName).group_by(Branch.branchUnitName).all()]
    salesForm.userSearch.choices = [(None, 'All')] + [(un.username, un.username) for un in User.query.all()]

    if request.method == 'POST':
        # print(salesForm.branchArea.data, salesForm.branchOutletOrNot.data, salesForm.branchUnitName.data,\
        # salesForm.userSearch.data, salesForm.customerSearch.data, salesForm.fromDate.data, salesForm.tillDate.data)
        error = salesForm.validate()
        if error is not True:
            return redirect(url_for('sales', error=error))
        else:
            if salesForm.branchArea.data != 'None':
                salesDone = salesDone.filter(Branch.branchArea == salesForm.branchArea.data)
            if salesForm.branchOutletOrNot.data != 'None':
                salesDone = salesDone.filter(Branch.branchOutletOrNot == salesForm.branchOutletOrNot.data)
            if salesForm.branchUnitName.data != 'None':
                salesDone = salesDone.filter(Branch.branchUnitName == salesForm.branchUnitName.data)
            if salesForm.userSearch.data != 'None':
                salesDone = salesDone.filter(User.username == salesForm.userSearch.data)
            if salesForm.customerSearch.data != 'None':
                salesDone = salesDone.filter(Bill.billCustomerName == salesForm.customerSearch.data)
            if salesForm.fromDate.data != '':
                year, month, day = salesForm.fromDate.data.split('-')
                fromDate = datetime.datetime(int(year),int(month),int(day))
                salesDone = salesDone.filter(Bill.billDateTime >= fromDate)
            if salesForm.tillDate.data != '':
                year, month, day = salesForm.tillDate.data.split('-')
                tillDate = datetime.datetime(int(year),int(month),int(day))
                salesDone = salesDone.filter(Bill.billDateTime <= tillDate)
            # print(salesDone)
            error = 'success'
    salesDone1 = salesDone.all()
    salesDone = []
    for sales in salesDone1:
        salesDone.append([sales[0], [sales[1], sales[2], sales[3], sales[4], sales[5], sales[6], sales[7], sales[8]]])

    return render_template('sales.html', session=session, salesHead=salesHead, error=error, salesDone=salesDone, salesForm=salesForm)

@app.route('/saleDetail/<billId>')
def saleDetail(billId):
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    saleDetailHead = ['ItemName', 'Item Price', 'Item Quantity']
    saleDetail = db.session.query(Item.itemName, BillDetails.billItemPrice, BillDetails.billItemQty).filter(BillDetails.billItemId == Item.itemId\
    , BillDetails.billDetailsBillId == billId).all()
    print(billId, saleDetail)
    return render_template('saleDetail.html', session=session, saleDetailHead=saleDetailHead, saleDetail=saleDetail, bill=Bill.query.\
    filter(Bill.billId == billId).first())


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
    # print(expiryDates)
    expiryDatesArray = []
    for expiryDate in expiryDates:
        expiryDateDict = {}
        expiryDateDict['id'] = expiryDate[0].strftime('%Y-%m-%d') if expiryDate[0] else expiryDate[0]
        expiryDateDict['name'] = expiryDate[0].strftime('%Y-%m-%d') if expiryDate[0] else expiryDate[0]
        expiryDatesArray.append(expiryDateDict)
    return jsonify({'expiryDates': expiryDatesArray})


@app.route('/qtyChanged/<id>/<val>')
def qtyChanged(id, val):
    global billDetailList
    for i, blist in enumerate(billDetailList):
        if int(id) == blist[0]:
            billDetailList[i][1].itemQuantity.data = val
            billDetailList[i][1].itemTotalPrice.data = str(int(billDetailList[i][1].itemQuantity.data) * int(billDetailList[i][1].itemPrice.data))
    return jsonify({'no':0})




# if __name__ == '__main__':
#     app.run()
