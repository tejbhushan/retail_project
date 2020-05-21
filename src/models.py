from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
import datetime
from src import app


db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    userAccess = db.Column(db.String(1), nullable=False)
    userBranchId = db.Column(db.Integer, db.ForeignKey('branch.branchId'), nullable=False)
    userDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, username, password, userAccess, userBranchId):
        self.username = username
        self.password = password
        self.userAccess = userAccess
        self.userBranchId = userBranchId

class Branch(db.Model):
    __tablename__ = 'branch'
    branchId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    branchCode = db.Column(db.Integer, unique=True, nullable=False)
    branchArea = db.Column(db.String(15), nullable=False)
    branchOutletOrNot = db.Column(db.String(1))  #Outlet '1' Not '0'
    branchUnitName = db.Column(db.String(15))
    branchDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    branchItem = relationship('Item', secondary='itemBranchRel')

    def __init__(self, branchCode, branchArea, branchOutletOrNot, branchUnitName):
        self.branchCode = branchCode
        self.branchArea = branchArea
        self.branchOutletOrNot = branchOutletOrNot
        self.branchUnitName = branchUnitName

class Item(db.Model):
    __tablename__ = 'item'
    itemId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemName = db.Column(db.String(20), unique=True, nullable=False)
    itemBarcode = db.Column(db.String(30), unique=True, nullable=False)
    itemDateTime = db.Column(db.DateTime, default=datetime.datetime.now)

    itemBranch = relationship('Branch', secondary='itemBranchRel')

    def __init__(self, itemName, itemBarcode):
        self.itemName = itemName
        self.itemBarcode = itemBarcode

class ItemBranchRel(db.Model):
    __tablename__ = 'itemBranchRel'
    relItemBranchId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    relItemId = db.Column(db.Integer, db.ForeignKey('item.itemId'), nullable=False)
    relBranchId = db.Column(db.Integer, db.ForeignKey('branch.branchId'), nullable=False)
    relItemPrice = db.Column(db.String(10), nullable=False)
    relItemAvailableQuantity = db.Column(db.String(5), nullable=False)
    relItemExpiry = db.Column(db.DateTime, nullable=True)   #ex tissues have no expiry
    relLastfillDateTime = db.Column(db.DateTime, nullable=False)
    relDatetime = db.Column(db.DateTime, default=datetime.datetime.now)
    db.UniqueConstraint('relItemId', 'relBranchId', 'relItemExpiry')

    item = relationship(Item, backref=backref('itemBranchRel', cascade='all, delete-orphan'))
    branch = relationship(Branch, backref=backref('itemBranchRel', cascade='all, delete-orphan'))

    def __init__(self, relItemId, relBranchId, relItemPrice, relItemAvailableQuantity, relItemExpiry, relLastfillDateTime):
        self.relItemId = relItemId
        self.relBranchId = relBranchId
        self.relItemPrice = relItemPrice
        self.relItemPrice = relItemPrice
        self.relItemAvailableQuantity = relItemAvailableQuantity
        self.relItemExpiry = relItemExpiry
        self.relLastfillDateTime = relLastfillDateTime

class Customer(db.Model):
    __tablename__ = 'customer'
    customerId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customerName = db.Column(db.String(20), unique=True, nullable=False)
    customerMobile = db.Column(db.String(15))
    customerDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, customerName, customerMobile):
        self.customerName = customerName
        self.customerMobile = customerMobile

class Bill(db.Model):
    __tablename__ = 'bill'
    billId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    billUserId = db.Column(db.Integer, db.ForeignKey('user.userId'), nullable=False)
    billBranchId = db.Column(db.Integer, db.ForeignKey('branch.branchId'), nullable=False)
    billCustomerId = db.Column(db.Integer, db.ForeignKey('customer.customerId'), nullable=False)
    billQuantity = db.Column(db.String(3), nullable=False)
    billAmount = db.Column(db.String(6), nullable=False)
    billDateTime = db.Column(db.DateTime, default=datetime.datetime.now)

    # user = relationship(User, backref=backref('bill', cascade='all, delete-orphan'))
    # branch = relationship(Branch, backref=backref('bill', cascade='all, delete-orphan'))
    # customer = relationship(Customer, backref=backref('bill', cascade='all, delete-orphan'))

    def __init__(self, billUserId, billBranchId, billCustomerId, billQuantity, billAmount):
        self.billUserId = billUserId
        self.billBranchId = billBranchId
        self.billCustomerId = billCustomerId
        self.billQuantity = billQuantity
        self.billAmount = billAmount

class BillDetails(db.Model):
    __tablename__ = 'billDetails'
    billDetailsId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    billDetailsBillId = db.Column(db.Integer, db.ForeignKey('bill.billId'), nullable=False)
    billItemId = db.Column(db.Integer, db.ForeignKey('item.itemId'), nullable=False)
    billItemQty = db.Column(db.Integer, nullable=False)

    def __init__(self, billDetailsBillId, billItemId, billItemQty):
        self.billDetailsBillId = billDetailsBillId
        self.billItemId = billItemId
        self.billItemQty = billItemQty


# db.drop_all()
# db.create_all()
a = 0;
log = User.query.first()
if a == 0 and log is None:
    db.session.add(Branch('1', 'mumbai', '1', 'wellness'))
    db.session.commit()
    db.session.add(User('tej', 'tej', 'O', 1))
    # db.session.add(Branch('2', 'del'))
    # db.session.add(Branch('3', 'kol'))
    # db.session.add(Branch('4', 'chen'))
    # db.session.add(Item('apple-1kg', '12331112'))
    # db.session.add(Item('cococola-600ml', '123332112'))
    # db.session.add(Item('cococola-2l', '12331112612'))
    # db.session.add(Item('maggi-300g', '1233111212'))
    db.session.add(Customer('expiry', '1111111111'))
    db.session.add(Customer('ram', '9768842000'))
    db.session.commit()
    # barcodes = [12331112, 123332112, 12331112612, 1233111212]
    # price = [200, 50, 80, 35]
    # branch = 1
    # from random import randrange
    # for i in price:
    #     itemId = 1
    #     for c,p in zip(barcodes, price):
    #         k = randrange(42)
    #         db.session.add(ItemBranchRel(itemId, branch, p, k))
    #         # print(itemId, branch, p, k),
    #         itemId += 1
    #     branch += 1

    # db.session.commit()
    a+=1
#
