from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()

class OrderAndProduct(database.Model):
    __tablename__ = "order_and_product"
    id = database.Column(database.Integer, primary_key=True)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"))
    productId= database.Column(database.Integer, database.ForeignKey("products.id"))
    quantity = database.Column(database.Integer, nullable=False)


class ProductAndCategory(database.Model):
    __tablename__ = "product_and_category"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"))
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id"))

class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    timestamp = database.Column(database.DateTime, nullable=False)
    status = database.Column(database.String(100), nullable=False)
    user = database.Column(database.String(256), nullable=False)
    totalPrice = database.Column(database.Float, nullable=False)

    products = database.relationship("Product", secondary=OrderAndProduct.__table__, back_populates="orders")


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)

    categories = database.relationship('Category', secondary=ProductAndCategory.__table__, back_populates="products")
    orders = database.relationship('Order', secondary=OrderAndProduct.__table__, back_populates="products")

class Category(database.Model):
    __tablename__="categories"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    products = database.relationship('Product', secondary=ProductAndCategory.__table__, back_populates="categories")




