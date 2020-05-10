from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
import datetime
from src import app


db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    useraccess = db.Column(db.String(10))
    userDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, username, password, useraccess):
        self.username = username
        self.password = password
        self.useraccess = useraccess

class Branch(db.Model):
    __tablename__ = 'branch'
    branchId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    branchCode = db.Column(db.String(5), unique=True)
    branchAddress = db.Column(db.String(30), unique=True)
    branchDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    branchItem = relationship('Item', secondary='itemBranchRel')

    def __init__(self, branchCode, branchAddress):
        self.branchCode = branchCode
        self.branchAddress = branchAddress

class Item(db.Model):
    __tablename__ = 'item'
    itemId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itemName = db.Column(db.String(20), unique=True)
    itemBarcode = db.Column(db.String(30), unique=True)
    # itemQuantityUnit = db.Column(db.String(5))
    itemDateTime = db.Column(db.DateTime, default=datetime.datetime.now)

    itemBranch = relationship('Branch', secondary='itemBranchRel')

    def __init__(self, itemName, itemBarcode):#, itemQuantityUnit):
        self.itemName = itemName
        self.itemBarcode = itemBarcode
        # self.itemQuantityUnit = itemQuantityUnit

class ItemBranchRel(db.Model):
    __tablename__ = 'itemBranchRel'
    relItemBranchId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    relItemId = db.Column(db.Integer, db.ForeignKey('item.itemId'))
    relBranchId = db.Column(db.Integer, db.ForeignKey('branch.branchId'))
    relItemPrice = db.Column(db.String(10))
    relItemAvailableQuantity = db.Column(db.String(5))
    # relItemExpiry = db.Column(db.DateTime)
    relDatetime = db.Column(db.DateTime, default=datetime.datetime.now)
    db.UniqueConstraint('relItemId', 'relBranchId', 'relItemExpiry')

    item = relationship(Item, backref=backref('itemBranchRel', cascade='all, delete-orphan'))
    branch = relationship(Branch, backref=backref('itemBranchRel', cascade='all, delete-orphan'))

    def __init__(self, relItemId, relBranchId, relItemPrice, relItemAvailableQuantity):#, relItemExpiry)):
        self.relItemId = relItemId
        self.relBranchId = relBranchId
        self.relItemPrice = relItemPrice
        self.relItemPrice = relItemPrice
        self.relItemAvailableQuantity = relItemAvailableQuantity
        # self.relItemExpiry = relItemExpiry

class Customer(db.Model):
    __tablename__ = 'customer'
    customerId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customerName = db.Column(db.String(20), unique=True)
    customerMobile = db.Column(db.String(15))
    customerDatetime = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, customerName, customerMobile):
        self.customerName = customerName
        self.customerMobile = customerMobile

class Bill(db.Model):
    __tablename__ = 'bill'
    billId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    billUserId = db.Column(db.Integer, db.ForeignKey('user.userId'))
    billBranchId = db.Column(db.Integer, db.ForeignKey('branch.branchId'))
    billCustomerId = db.Column(db.Integer, db.ForeignKey('customer.customerId'))
    billList = db.Column(db.String(100))
    billAmount = db.Column(db.String(5))
    billDateTime = db.Column(db.DateTime, default=datetime.datetime.now)

    # user = relationship(User, backref=backref('bill', cascade='all, delete-orphan'))
    # branch = relationship(Branch, backref=backref('bill', cascade='all, delete-orphan'))
    # customer = relationship(Customer, backref=backref('bill', cascade='all, delete-orphan'))

    def __init__(self, billUserId, billBranchId, billCustomerId, billList, billAmount):
        self.billUserId = billUserId
        self.billBranchId = billBranchId
        self.billCustomerId = billCustomerId
        self.billList = billList
        self.billAmount = billAmount


# db.drop_all()
db.create_all()
a = 0;
log = User.query.filter_by(username='tej').first()
if a == 0 and log is None:
    db.session.add(User('tej', 'tej', '0'))
    # db.session.add(Branch('1', 'mum'))
    # db.session.add(Branch('2', 'del'))
    # db.session.add(Branch('3', 'kol'))
    # db.session.add(Branch('4', 'chen'))
    # db.session.add(Item('apple-1kg', '12331112'))
    # db.session.add(Item('cococola-600ml', '123332112'))
    # db.session.add(Item('cococola-2l', '12331112612'))
    # db.session.add(Item('maggi-300g', '1233111212'))
    db.session.add(Customer('ramchai', '9768842000'))
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
