from flask import Flask, jsonify, request, Response, make_response
from configuration import Configuration
from models import *
from functools import wraps
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt


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


@application.route("/orders_to_deliver", methods=["GET"])
@roleCheck(role="courier")
def ordersToDeliver():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    notDeliveredOrders = Order.query.filter(Order.status == "CREATED")
    returningOrders = []
    for ord in notDeliveredOrders:
        currentOrder = {
            "id": ord.id,
            "email": ord.user
        }
        returningOrders.append(currentOrder)

    return jsonify({"orders": returningOrders}), 200




@application.route("/pick_up_order", methods=["POST"])
@roleCheck(role="courier")
def pickUpOrder():
    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization Header"}), 401
    if request.json==None :
        return jsonify(), 400
    orderIdTemp = request.json.get("id", None)
    if not orderIdTemp:
        return jsonify({"message": "Missing order id."}), 400
    try:
        orderId=int(orderIdTemp)
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400


    if not isinstance(orderId, int) or orderId <=0:
        return jsonify({"message": "Invalid order id."}), 400

    orderToPickUp = Order.query.filter(Order.id == orderId).first()

    if not orderToPickUp:
        return jsonify({"message": "Invalid order id."}), 400
    if orderToPickUp.status != "CREATED":
        return jsonify({"message": "Invalid order id."}), 400


    orderToPickUp.status = "PENDING"
    #database.session.add(orderToPickUp)
    database.session.commit()
    return Response(status=200)




if( __name__ == "__main__" ):
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)