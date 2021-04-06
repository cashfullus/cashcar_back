from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from appConfig import secret_key

from .models import user_model as User, car_model as Car

import os
import logging

from flasgger import Swagger, swag_from

# logging.basicConfig(filename="log.txt", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = secret_key
app.config['JWT_TOKEN_LOCATION'] = 'headers'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
jwt_manager = JWTManager(app)
swagger = Swagger(app)


# 이미지 파일 형식
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
BASE_IMAGE_LOCATION = os.getcwd()+"/appConfig/static/image/"


# 이미지 파일 형식검사
def allowed_file(files):
    result = []
    for file in files:
        filename = file.filename
        result.append('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return result


# 토큰 인증 실패시 return 하는 response 의 중복적인 사용으로 인해 return 변수를 저장해서 쓰는게 낫다고 생각함.
Unauthorized = {"status": False, "data": "Unauthorized"}


# 이미지 업로드
@app.route("/upload/image/<location>", methods=["POST"])
@jwt_required()
@swag_from('route_yml/upload/image_upload.yml', methods=['POST'])
def upload_image(location):
    files = request.files.getlist('files')
    data = request.form
    identity_ = get_jwt_identity()
    allowed = allowed_file(files)

    if data["user_id"] != identity_:
        return jsonify(Unauthorized), 401

    if False not in allowed:
        try:
            os.makedirs(BASE_IMAGE_LOCATION + f"{location}/{data['location_id']}/{data['user_id']}", exist_ok=True)
            for file in files:
                file.save(BASE_IMAGE_LOCATION + f"{location}/{data['location_id']}/{data['user_id']}/"+secure_filename(file.filename))
            return jsonify({"status": True, "data": "Success Upload"}), 200
        except TypeError:
            return jsonify({"status": False, "data": "Bad Request"}), 400
    else:
        return jsonify({"status": False, "data": "Not Allowed File"}), 404


# 회원가입
@app.route("/register", methods=["POST"])
@swag_from('route_yml/user/user_register.yml', methods=["POST"])
def user_register():
    data = request.get_json()
    result = User.register(**data)
    if result:
        return jsonify({"status": result}), 201
    else:
        return jsonify({"status": result}), 409


# 로그인
@app.route("/login", methods=["POST"])
@swag_from('route_yml/user/user_login.yml', methods=["POST"])
def user_login():
    data = request.get_json()

    result = User.login(**data)
    if result:
        return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": result, "data": "Not Found"}), 405


# 제조사 별 차량 업체 리스트
@app.route("/manufacturer/list", methods=["GET"])
@jwt_required()
@swag_from('route_yml/car/manufacturer_list.yml', methods=['GET'])
def get_manufacturer_list():
    """
    """
    data = request.get_json()
    identity_ = get_jwt_identity()
    result = Car.manufacturer(data["manufacturer_type"])
    if result:
        if data["user_id"] == identity_:
            return jsonify({"status": True, "data": result}), 200
        else:
            return jsonify(Unauthorized), 401
    else:
        return jsonify({"status": False, "data": "Not Found"}), 405


# 차량 등록
@app.route("/car/register", methods=["POST"])
@jwt_required()
@swag_from('route_yml/car/car_register.yml', methods=['POST'])
def register_car():
    data = request.get_json()
    identity_ = get_jwt_identity()
    result = Car.register_car(**data)
    if result:
        if data["user_id"] == identity_:
            return jsonify({"status": True, "data": result}), 200
        else:
            return jsonify(Unauthorized), 401
    else:
        return jsonify({"status": False, "data": "Not Found"}), 405


# 미션등록


