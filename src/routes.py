from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
from . models import User, db, ItemBranchRel, Branch, Item, Bill, Customer
from . forms import SignUpForm, SignInForm, FillingForm, BranchForm, BillForm
from src import app
import datetime
from sqlalchemy import func


@app.route('/')
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    #handle if branch has no entries
    error = ''
    signinform = SignInForm()
    signinform.selBranchCode.choices = [('0', 'All')] + [(i+1, bCodes[0]) for i, bCodes in\
     enumerate(db.session.query(Branch.branchAddress).order_by(Branch.branchId).all())]
    if request.method == 'POST':
        un = signinform.username.data
        log = User.query.filter_by(username=un).first()
        if log is not None and log.password == signinform.password.data:
            if log.useraccess == '2' and signinform.selBranchCode.data == '0':
                error = 'User please select a specific branch. '
            else:
                if signinform.selBranchCode.data == '0':
                    session['branchId'], session['branch'] = '0', 'All'
                else:
                    branch = Branch.query.filter(Branch.branchId == signinform.selBranchCode.data).first()
                    session['branchId'], session['branch'] = branch.branchId, branch.branchAddress
                session['current_user'] = log.username
                session['user_available'] = True
                session['user_access'] = log.useraccess
                return redirect(url_for('billing'))
        else:
            error = 'invalid creds'
    return render_template('signin.html', signinform=signinform, error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    signupform = SignUpForm()
    if session['user_access'] == '0':
        signupform.user_access.choices = [('1', 'Manager'), ('2', 'Employee')]
    elif session['user_access'] == '1':
        signupform.user_access.choices = [('2', 'Employee')]
    if request.method == 'POST':
        reg = User(signupform.username.data, signupform.password.data, signupform.user_access.data)
        usernameDuplicate = User.query.filter(User.username == signupform.username.data).first()
        if usernameDuplicate is None:
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for('signup'))
        else:
            return render_template('signup.html', signupform=signupform, error="username duplicate",\
            user=session['current_user'], user_access=session['user_access'], selBranchCode=session['branch'])
    return render_template('signup.html', signupform=signupform, user=session['current_user'], \
    user_access=session['user_access'], selBranchCode=session['branch'])



@app.route('/filling/<error>', methods=['GET', 'POST'])
def filling(error):
    if session['user_available'] is False:
        return redirect(url_for('signin'))

    available_stockHead = ['Item Barcode', 'Item Name', 'Branch Address', 'Item price', 'Item Available Qunatity']
    if session['branch'] == 'All':
        available_stock = db.session.query(Item.itemBarcode, Item.itemName, \
        Branch.branchAddress, ItemBranchRel.relItemPrice, ItemBranchRel.relItemAvailableQuantity).\
        filter(ItemBranchRel.relItemId == Item.itemId).filter(ItemBranchRel.relBranchId == Branch.branchId)\
        .group_by(ItemBranchRel.relBranchId, ItemBranchRel.relItemBranchId).all()
    else:
        available_stock = db.session.query(Item.itemBarcode, Item.itemName, Branch.branchAddress\
        , ItemBranchRel.relItemPrice, ItemBranchRel.relItemAvailableQuantity).\
        filter(ItemBranchRel.relItemId == Item.itemId).filter(ItemBranchRel.relBranchId == Branch.branchId)\
        .filter(ItemBranchRel.relBranchId == session['branchId']).\
        group_by(ItemBranchRel.relBranchId, ItemBranchRel.relItemBranchId).all()


    if session['branch'] == 'All':
        return render_template('filling.html', user=session['current_user'], user_access=session['user_access'],\
         selBranchCode=session['branch'], error1='For filling, sign in with specific branch', available_stockHead\
         =available_stockHead, available_stock=available_stock)

    fillingform = FillingForm()
    fillingform.existingItemBarCode.choices = [('0', 'Select')] + [(ibcodes, iNames) for ibcodes, iNames \
    in db.session.query(Item.itemBarcode, Item.itemName).filter(ItemBranchRel.relItemId == Item.itemId).\
    filter(ItemBranchRel.relBranchId == session['branchId']).all()]
    if request.method == 'POST':
        error = fillingform.validate_on_submit()
        if error is not True:
            return redirect(url_for('filling', error=error))
        else:
            # print(fillingform.existingItemBarCode.data, " as ", fillingform.newItemBarCode.data, " as ", fillingform.\
            # itemName.data, " as ",fillingform.updatePrice.data, " as ", fillingform.itemQuantity.data)
            if fillingform.existingItemBarCode.data != '0':
                item = Item.query.filter(Item.itemBarcode == fillingform.existingItemBarCode.data).first()
                itemExistInBranchInventory = ItemBranchRel.query.filter(ItemBranchRel.relItemId == item.itemId).filter\
                (ItemBranchRel.relBranchId == session['branchId']).first()
                if fillingform.updatePrice.data != '':
                    itemExistInBranchInventory.relItemPrice = fillingform.updatePrice.data
                if fillingform.itemQuantity.data != '':
                    itemExistInBranchInventory.relItemAvailableQuantity = str(int(itemExistInBranchInventory\
                    .relItemAvailableQuantity) + int(fillingform.itemQuantity.data))
            else:
                item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarCode.data).first()
                #item table itself doesnot have, hence feed to item table first
                if item is None:
                    db.session.add(Item(fillingform.itemName.data, fillingform.newItemBarCode.data))
                    db.session.commit()
                item = Item.query.filter(Item.itemBarcode == fillingform.newItemBarCode.data).first()
                db.session.add(ItemBranchRel(item.itemId, session['branchId'], fillingform.updatePrice.data,\
                fillingform.itemQuantity.data))

            db.session.commit()
            return redirect(url_for('filling', error='success'))

    return render_template('filling.html', user=session['current_user'], user_access=session['user_access'],\
     selBranchCode=session['branch'], fillingform=fillingform, available_stockHead=available_stockHead,\
     available_stock=available_stock, error=error)



@app.route('/billing', methods=['GET', 'POST'])
def billing(listItems = [], total = [0]):
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    if session['branch'] == 'All':
        return render_template('billing.html', user=session['current_user'], user_access=session['user_access'],\
         selBranchCode=session['branch'], error='sign in with a specific branch for billing')

    query = db.session.query(Item.itemBarcode).filter(ItemBranchRel.relItemId == Item.itemId).\
    filter(ItemBranchRel.relBranchId == session['branchId']).all()
    if query is None:
        return render_template('branch.html', user=session['current_user'], user_access=session['user_access'],\
         selBranchCode=session['branch'], error='No Stock')

    userId = User.query.filter(User.username == session['current_user']).first().userId
    billform = BillForm()
    billform.itemBarcode.choices = [(bcodes[0], bcodes[0]) for bcodes in query]
    if request.method == 'POST':
        if billform.next.data:
            item = Item.query.filter(Item.itemBarcode == billform.itemBarcode.data).first()
            itemrel = db.session.query(ItemBranchRel).filter(ItemBranchRel.relItemId ==\
            item.itemId).filter(ItemBranchRel.relBranchId == session['branchId']).first()
            total[0] += int(itemrel.relItemPrice)*int(billform.itemQuantity.data)
            listItems.append([billform.itemBarcode.data, item.itemName, itemrel.relItemPrice\
            , billform.itemQuantity.data])
            itemrel.relItemAvailableQuantity = str(int(itemrel.relItemAvailableQuantity) - int(billform.itemQuantity.data))
            db.session.commit()
        if billform.submit.data:
            customerId = Customer.query.filter(Customer.customerName == billform.customerName.data).first().customerId
            s = ''
            for list in listItems:
                s += '('+list[1]+':'+list[2]+':'+list[3]+')'
            print(s)
            db.session.add(Bill(userId, session['branchId'], customerId, s, total[0]))
            db.session.commit()
            listItems.clear()
            total.clear()
            return redirect(url_for('billing'))
    return render_template('billing.html', user=session['current_user'], user_access=session['user_access'],\
     selBranchCode=session['branch'], billform=billform, listItems=listItems, total=total)



@app.route('/branch', methods=['GET', 'POST'])
def branch():
    if session['user_available'] is False:
        return redirect(url_for('signin'))
    if session['user_access'] != '0':
        return render_template('branch.html', user=session['current_user'], user_access=session['user_access'],\
         selBranchCode=session['branch'], error='only owner can modify branch')
    branchform = BranchForm()
    newBranchCode = '1'
    branch = Branch.query.first()
    if branch is not None:
        newBranchCode = str(int(db.session.query(func.max(Branch.branchCode)).first()[0]) + 1)
    branchform.branchCode.choices = [(1, newBranchCode)]
    if request.method == 'POST':
        db.session.add(Branch(newBranchCode, branchform.branchAddress.data))
        db.session.commit()
        return render_template('branch.html', user=session['current_user'], user_access=session['user_access'],\
         selBranchCode=session['branch'], branchform=branchform, error='success')
    return render_template('branch.html', user=session['current_user'], user_access=session['user_access'],\
     selBranchCode=session['branch'], branchform=branchform)


@app.route('/logout')
def logout():
    session.clear()
    session['user_available'] = False
    return redirect(url_for('signin'))






# if __name__ == '__main__':
#     app.run()
