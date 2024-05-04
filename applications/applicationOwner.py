import io
import csv
from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from functools import wraps
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt
from sqlalchemy import func, desc, asc, case
from sqlalchemy import and_, or_


application = Flask (__name__)
application.config.from_object(Configuration)
jwt= JWTManager(application)


def roleCheck(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*arguments, **keywordArguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if (("roles" in claims) and (role in claims["roles"])):
                return function(*arguments, **keywordArguments)
            else:
                return jsonify({"msg": "Missing Authorization Header"}), 401
        return decorator
    return innerRole


@application.route("/update", methods=["POST"])
@roleCheck(role="owner")
def update():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401
    if "file" not in request.files:
        return jsonify({"message":"Field file is missing."}), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)
    cnt = 0
    productsToAdd = []
    for row in reader:
        if(len(row) !=3):
            return jsonify({"message": f"Incorrect number of values on line {cnt}."}), 400
        categoryNames = []
        categoryNames.extend(row[0].split("|"))
        try:
            price = float(row[2])
            if price <=0:
                raise ValueError
        except ValueError:
            return jsonify({"message": f"Incorrect price on line {cnt}."}), 400

        productName = row[1]
        foundProduct = Product.query.filter(Product.name==productName).first()
        if foundProduct:
            return jsonify({"message": f"Product {productName} already exists."}), 400

        cnt += 1
        productsToAdd.append({"categories": categoryNames, "name":productName, "price": price})


    for productInfo in productsToAdd:
        product = Product(name=productInfo.get("name"), price=float(productInfo.get("price")))
        database.session.add(product)
        database.session.commit()

        categories = productInfo.get("categories")

        for currentName in categories:
            currentCategory = Category.query.filter(Category.name==currentName).first()
            if not currentCategory:
                currentCategory = Category(name=currentName)
                database.session.add(currentCategory)
                database.session.commit()

            prodCat = ProductAndCategory(productId=product.id, categoryId=currentCategory.id)
            database.session.add(prodCat)
            database.session.commit()

    return Response(status=200)



@application.route("/product_statistics", methods=["GET"])
@roleCheck(role="owner")
def productStatistics():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    #za svaki proizvod, koliko je prodatih(nalaze se u complete porudzbinama), koliko ceka(nije complete)

    #koristim join umesto outerjoin jer ne treba da se prikazu proizvodi koji imaju 0 prodatih
    productStatistics = database.session.query(
        Product.name,
        func.sum( case([(Order.status == "COMPLETE", OrderAndProduct.quantity)], else_=0)).label("productSold"),
        func.sum(case([(Order.status != "COMPLETE", OrderAndProduct.quantity)], else_=0)).label("productWaiting")
    )
    productStatistics = productStatistics.join(OrderAndProduct, Product.id == OrderAndProduct.productId).join(Order, OrderAndProduct.orderId == Order.id)
    productStatistics = productStatistics.group_by(Product.name).all()

    statsToReturn=[{"name": productStat.name,
                    "sold": int(productStat.productSold),
                    "waiting": int(productStat.productWaiting)
                    } for productStat in productStatistics]

    return jsonify({"statistics": statsToReturn}),200



@application.route("/category_statistics", methods=["GET"])
@roleCheck(role="owner")
def categoryStatistics():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    categoriesToReturn = database.session.query(Category.name,
                func.sum(case([(Order.status=="COMPLETE", OrderAndProduct.quantity)], else_=0)).label("sold"))\
        .outerjoin(ProductAndCategory, Category.id == ProductAndCategory.categoryId)\
        .outerjoin(Product, ProductAndCategory.productId == Product.id)\
        .outerjoin(OrderAndProduct, Product.id == OrderAndProduct.productId)\
        .outerjoin(Order, OrderAndProduct.orderId == Order.id)\
        .group_by(Category.name)\
        .order_by(desc("sold"), Category.name).all()


    toReturn = [category.name for category in categoriesToReturn]
    return jsonify({"statistics": toReturn}), 200


if( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)