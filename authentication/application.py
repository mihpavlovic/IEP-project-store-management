from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database
from email.utils import parseaddr
from models import User, UserRole, Role
from sqlalchemy import and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity
import re

application = Flask(__name__)
application.config.from_object( Configuration )

def emailCheck(email):

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.match(regex, email):
        return True
    else:
        return False

@application.route("/", methods=["GET"])
def index():
    return "hello world"

@application.route("/register_customer", methods=["POST"])
def reg_customer():
    email = request.json.get('email', "")
    password = request.json.get('password', "")
    forename = request.json.get('forename', "")
    surname = request.json.get('surname', "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if (forenameEmpty):
        return jsonify({"message": "Field forename is missing."}), 400
    if (surnameEmpty):
        return jsonify({"message": "Field surname is missing."}), 400
    if (emailEmpty):
        return jsonify({"message": "Field email is missing."}), 400
    if (passwordEmpty):
        return jsonify({"message": "Field password is missing."}), 400


    emailValid = emailCheck(email)
    if(not emailValid):
        return jsonify({"message": "Invalid email."}), 400


    if(len(password) < 8):
        return jsonify({"message": "Invalid password."}), 400

    emailExistInDB = User.query.filter(User.email == email).first()
    if(emailExistInDB):
        return jsonify({"message" : "Email already exists."}),400

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    customerRole = Role.query.filter(Role.name == "customer").first()

    userRole = UserRole( userId=user.id, roleId=customerRole.id )
    database.session.add(userRole)
    database.session.commit()

    return Response(status=200)

@application.route("/register_courier", methods=["POST"])
def reg_courier():
    email = request.json.get('email', "")
    password = request.json.get('password', "")
    forename = request.json.get('forename', "")
    surname = request.json.get('surname', "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if (forenameEmpty):
        return jsonify({"message": "Field forename is missing."}), 400
    if (surnameEmpty):
        return jsonify({"message": "Field surname is missing."}), 400
    if (emailEmpty):
        return jsonify({"message": "Field email is missing."}), 400
    if (passwordEmpty):
        return jsonify({"message": "Field password is missing."}), 400

    emailValid = emailCheck(email)
    if (not emailValid):
        return jsonify({"message": "Invalid email."}), 400

    if (len(password) < 8):
        return jsonify({"message": "Invalid password."}), 400

    emailExistInDB = User.query.filter(User.email == email).first()
    if (emailExistInDB):
        return jsonify({"message": "Email already exists."}),400

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    courierRole = Role.query.filter(Role.name=="courier").first()

    userRole = UserRole(userId=user.id, roleId=courierRole.id)
    database.session.add(userRole)
    database.session.commit()

    return Response(status=200)


jwt = JWTManager(application)

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get('email', "")
    password = request.json.get('password', "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if (emailEmpty):
        return jsonify({"message": "Field email is missing."}), 400
    if (passwordEmpty):
        return jsonify({"message": "Field password is missing."}), 400

    # MEJL NE RADI KAKO TREBA
    result = emailCheck(email)
    if (not result):
        return jsonify({"message": "Invalid email."}), 400
    # MEJL NE RADI KAKO TREBA

    user = User.query.filter(and_(User.email == email, User.password == password)).first()
    if(not user):
        return jsonify({"message": "Invalid credentials."}), 400
    additionalClaims = {
        'forename': user.forename,
        'surname': user.surname,
        'roles': [str(role) for role in user.roles]
    }
    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)
    return jsonify(accessToken=accessToken)

@application.route("/delete", methods=["POST"])
@jwt_required()
def delete_user():

    if "Authorization" not in request.headers:
        return jsonify({"msg": "Missing Authorization header"}), 401

    email = get_jwt_identity()
    user = User.query.filter(User.email==email).first()
    if(not user):
        return jsonify({"message": "Unknown user."}),400
    #return Response("pronadjen korisnik", status=200)
    database.session.delete(user)
    database.session.commit()
    return Response(status=200)




@application.route("/loginVezbe", methods=['POST'])
def loginVezbe():
    email = request.json.get('email', "")
    password = request.json.get('password', "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if (emailEmpty or passwordEmpty):
        return Response("All fields required", status=400)

    user = User.query.filter(and_(User.email == email, User.password==password)).first()
    if(not user):
        return Response('Invalid credentials', status=400)

    additionalClaims = {
        'forename': user.forename,
        'surname': user.surname,
        'roles': [str (role) for role in user.roles]
    }
    accessToken = create_access_token(identity=user.email, additional_claims= additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims= additionalClaims)
    return jsonify(accessToken=accessToken, refreshToken=refreshToken)
    #return Response(accessToken, status=200)


@application.route("/check", methods=["POST"])
@jwt_required() #gleda da li je token validan, on se prosledjuje preko Postman->Headers->doda se u key Authorization-> doda se u value Bearer razmak pa token koji treba
def check():
    return "Radi"

@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()
    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }
    return Response( create_access_token(identity=identity, additional_claims=additionalClaims), status=200)



if(__name__ == '__main__'):
    database.init_app(application)
    application.run(debug = True, host="0.0.0.0", port = 5000)