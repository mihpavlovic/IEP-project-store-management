from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import *
from functools import wraps
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime
from sqlalchemy import and_


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


@application.route("/search", methods=["GET"])
@roleCheck(role="customer")
def search():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401
    productName = request.args.get("name")
    categoryName = request.args.get("category")

    #pronadji kategorije koje sadrze categoryName i koje imaju proizvode koji sadrze productName
    allProducts = Product.query
    if productName:
        allProducts = allProducts.filter(Product.name.like(f"%{productName}%"))
    if categoryName:
        allProducts = allProducts.join(ProductAndCategory).join(Category).filter(Category.name.like(f"%{categoryName}%"))

    foundProducts = allProducts.all()
    products = []
    categories = []
    for oneFound in foundProducts:
        productCategories = [category.name for category in oneFound.categories]
        for prodCat in productCategories:
            if prodCat not in categories:
                categories.append(prodCat)
        product = {
            "categories": productCategories,
            "id": oneFound.id,
            "name": oneFound.name,
            "price": oneFound.price
        }
        products.append(product)

    if not productName and not categoryName:
        allCategories = Category.query.all()
        for category in allCategories:
            if category.name not in categories:
                categories.append(category.name)

    return jsonify({
        "categories": categories,
        "products": products
    }),200




@application.route("/order", methods=["POST"])
@roleCheck(role="customer")
def order():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    orderRequests = request.json.get("requests", "") #ne znam da li valja

    if len(orderRequests) == 0: #pitanje da li je dobro, mislim da nije jer ako ima polje request a nema nijedan poslat mislim da ce tu da udje u ovu gresku
        return jsonify({"message":"Field requests is missing."}),400

    counter = 0
    totalPrice = 0
    for orderReq in orderRequests:
        if "id" not in orderReq:
            return jsonify({"message":f"Product id is missing for request number {counter}."}),400
        if "quantity" not in orderReq:
            return jsonify({"message":f"Product quantity is missing for request number {counter}."}), 400
        idCheck= orderReq["id"]
        quantityCheck = orderReq["quantity"]
        if not isinstance(idCheck, int) or idCheck <= 0:
            return jsonify({"message": f"Invalid product id for request number {counter}."}), 400
        if not isinstance(quantityCheck, int) or quantityCheck <=0:
            return jsonify({"message": f"Invalid product quantity for request number {counter}."}), 400

        productInDatabase = Product.query.filter(Product.id == idCheck).first()
        if not productInDatabase:
            return jsonify({"message": f"Invalid product for request number {counter}."}),400

        counter += 1
        #racunanje ukupne cene
        totalPrice += productInDatabase.price * quantityCheck

    #ovde sada treba da se pravi order, prave se veze potrebne za order i vraca se id porudzbine

    #pravljenje ordera
    user = get_jwt_identity()
    newOrder = Order(timestamp=datetime.now(),status="CREATED", user=user, totalPrice=totalPrice)
    database.session.add(newOrder)
    database.session.commit()
    # pravljenje veza
    for orderReq in orderRequests:
        productId = int(orderReq["id"])
        productQuantity = int(orderReq["quantity"])
        newOrderAndProduct = OrderAndProduct(orderId=newOrder.id, productId=productId, quantity=productQuantity)
        database.session.add(newOrderAndProduct)
        database.session.commit()



    return jsonify({"id": newOrder.id}), 200







#izbacuje sve narudzbine jednog kupca, tog koji je pozvao funkciju
#statusi porudzbine su CREATED, PENDING, COMPLETE
@application.route("/status", methods=["GET"])
@roleCheck(role="customer")
def status():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    #uzmi sve ordere od ovog korisnika
    thisUser = get_jwt_identity()

    #pokupi sve ordere od datog korisnika
    #svi order se pakuje na sledeci nacin
        #products : sadrzi kategorije, ime, cenu, kvantitet za svaki
        #ukupna cena ordera
        #status
        #timestamp
    allOrdersForUser = Order.query.filter(Order.user==thisUser).all()
    returningOrders = []
    for ord in allOrdersForUser:
        productsFromCurrentOrder = []
        for product in ord.products:
            categories = [category.name for category in product.categories]
            quantityOfProduct = OrderAndProduct.query.filter(and_(OrderAndProduct.productId==product.id, OrderAndProduct.orderId == ord.id)).first()
            justQuantity = quantityOfProduct.quantity
            productInJson = {
                "categories": categories,
                "name": product.name,
                "price": product.price,
                "quantity": justQuantity
            }
            productsFromCurrentOrder.append(productInJson)
        orderToReturn = {
            "products": productsFromCurrentOrder,
            "price": ord.totalPrice,
            "status": ord.status,
            "timestamp": ord.timestamp
        }
        returningOrders.append(orderToReturn)
    return jsonify({"orders":returningOrders}), 200


@application.route("/delivered", methods=["POST"])
@roleCheck(role="customer")
def delivered():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    if request.json==None :
        return jsonify(), 400

    orderIdTemp = request.json.get("id", None)
    if not orderIdTemp:
        return jsonify({"message":"Missing order id."}), 400

    try:
        orderId=int(orderIdTemp)
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400

    if not isinstance(orderId, int) or orderId<=0:
        return jsonify({"message": "Invalid order id."}), 400

    orderToDeliver = Order.query.filter(Order.id == orderId).first()

    if not orderToDeliver:
        return jsonify({"message": "Invalid order id."}), 400
    if orderToDeliver.status !="PENDING":
        return jsonify({"message": "Invalid order id."}), 400


    orderToDeliver.status = "COMPLETE"
    #database.session.add(orderToDeliver)
    database.session.commit()
    return Response(status=200)





if( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)