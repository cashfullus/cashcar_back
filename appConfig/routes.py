# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, render_template
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename

from appConfig import secret_key

from .models import user_model as User, vehicle_model as Vehicle, ad_model as AD
import os
import logging

from flasgger import Swagger, swag_from

logging.basicConfig(filename="log.txt", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = secret_key
app.config['JWT_TOKEN_LOCATION'] = 'headers'
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
CORS(app)
jwt_manager = JWTManager(app)
swagger = Swagger(app)

# 이미지 파일 형식
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
BASE_IMAGE_LOCATION = os.getcwd() + "/appConfig/static/image/"


# 이미지 파일 형식검사
def allowed_files(files):
    result = []
    for file in files:
        filename = file.filename
        result.append('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return result


def allowed_image_for_dict(images):
    result = []
    for image in images.values():
        result.append('.' in image and image.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return result


def allowed_image(image):
    filename = image.filename
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 회원가입 전 이용약관 동의 받기

# 토큰 인증 실패시 return 하는 response 의 중복적인 사용으로 인해 return 변수를 저장해서 쓰는게 낫다고 생각함.
Unauthorized = {"status": False, "data": "Unauthorized"}


# 지도 API (Daum postcode)
@app.route('/kakao/postcode', methods=['GET'])
def kakao_address():
    return render_template('kakao_address.html')


# 이미지 업로드
@app.route("/upload/image/<location>", methods=["POST"])
@jwt_required()
@swag_from('route_yml/upload/image_upload.yml', methods=['POST'])
def upload_image(location):
    files = request.files.getlist('files')
    data = request.form
    identity_ = get_jwt_identity()
    allowed = allowed_files(files)

    if data["user_id"] != identity_:
        return jsonify(Unauthorized), 401

    if False not in allowed:
        try:
            directory = "{0}/{1}/{2}".format(location, data["location_id"], data["user_id"])
            os.makedirs(BASE_IMAGE_LOCATION + directory, exist_ok=True)
            for file in files:
                file.save(BASE_IMAGE_LOCATION + directory + "/" + secure_filename(file.filename))
            return jsonify({"status": True, "data": "Success Upload"}), 200
        except TypeError:
            return jsonify({"status": False, "data": "Bad Request"}), 400
    else:
        return jsonify({"status": False, "data": "Not Allowed File"}), 404


# FCM 토큰
@app.route("/user/fcm", methods=["POST"])
@swag_from('route_yml/user/user_fcm.yml', methods=["POST"])
def fmc_token():
    try:
        data = request.get_json()
        result = User.user_fcm(**data)
        if result:
            return jsonify({"status": True, "data": "Success Save Fcm"}), 200
        else:
            return jsonify({"status": False, "data": "Not Found"}), 404
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 비회원 계정 생성
@app.route("/home", methods=["GET"])
def home():
    result = User.non_user_register()
    return jsonify({"status": True, "data": result}), 200


# 회원가입
@app.route("/register", methods=["POST"])
@swag_from('route_yml/user/user_register.yml', methods=["POST"])
def user_register():
    try:
        data = request.get_json()
        result = User.register(**data)
        if result["email_regex"] is False:
            return jsonify({"status": False, "data": "Not Correct Form Email"}), 404
        elif result["status"] is False:
            return jsonify({"status": False, "data": "Conflict User"}), 409
        elif result["register_type"] is False:
            return jsonify({"status": False, "data": "Not Allowed Type"}), 405
        else:
            return jsonify({"status": True, "data": result["data"]}), 201
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 로그인
@app.route("/login", methods=["POST"])
@swag_from('route_yml/user/user_login.yml', methods=["POST"])
def user_login():
    data = request.get_json()
    result = User.login(**data)
    if result:
        return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": result, "data": "Not Found"}), 404


# 사용자 프로필
@app.route("/user/profile", methods=["GET", "POST"])
@jwt_required()
@swag_from('route_yml/user/user_profile_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_profile_post.yml', methods=['POST'])
def user_profile():
    try:
        user_id = request.args.get('user_id')
        identity_ = get_jwt_identity()
        if int(user_id) != identity_:
            return jsonify(Unauthorized), 401

        if request.method == "GET":
            result = User.get_user_profile(user_id)
            if result:
                return jsonify({"status": True, "data": result}), 200
            else:
                return jsonify({"status": False, "data": "Not Found"}), 404

        elif request.method == "POST":
            data = request.get_json()
            result = User.update_user_profile(user_id, **data)
            if result:
                return jsonify({"status": True, "data": "Success Update"}), 201
            else:
                return jsonify({"status": False, "data": "Not Found"}), 404
        else:
            return jsonify({"status": False, "data": "Not Allowed Request"}), 405
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 차량 등록
@app.route("/vehicle/register", methods=["POST"])
@jwt_required()
@swag_from('route_yml/vehicle/vehicle_register.yml', methods=['POST'])
def register_car():
    try:
        data = request.get_json()
        identity_ = get_jwt_identity()
        result = Vehicle.register_vehicle(**data)
        if data["user_id"] == identity_:
            if result["user"] is False:
                return jsonify({"status": False, "data": "Not Correct User"}), 404
            elif result["register"] is False:
                return jsonify({"status": False, "data": "Register Vehicle Limit 3"}), 405
            elif result["double_check_number"] is False:
                return jsonify({"status": False, "data": "Double Check False"}), 409
            else:
                return jsonify({"status": True, "data": result}), 201
        else:
            return jsonify(Unauthorized), 401
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 본인 차량 리스트
@app.route("/vehicle/list")
@jwt_required()
@swag_from('route_yml/vehicle/vehicle_list.yml')
def vehicle_list():
    try:
        user_id = request.args.get('user_id')
        identity_ = get_jwt_identity()
        if int(user_id) != identity_:
            return jsonify(Unauthorized), 401

        result = Vehicle.vehicle_list_by_user_id(user_id=user_id)
        if result:
            return jsonify({'status': True, 'data': result}), 200
        else:
            return jsonify({'status': True, 'data': []}), 201

    except TypeError:
        return jsonify({'status': False, 'data': 'Data Not Null'}), 400


# 차량 정보 GET UPDATE API
@app.route("/vehicle/information", methods=["GET", "POST", "DELETE"])
@jwt_required()
@swag_from('route_yml/vehicle/vehicle_information_get.yml', methods=['GET'])
@swag_from('route_yml/vehicle/vehicle_information_post.yml', methods=['POST'])
@swag_from('route_yml/vehicle/vehicle_information_delete.yml', methods=['DELETE'])
def vehicle_get():
    try:
        data = request.get_json()
        user_id = request.args.get('user_id')
        vehicle_id = request.args.get('vehicle_id')
        identity_ = get_jwt_identity()
        if int(user_id) == identity_:
            if request.method == "GET":
                result = Vehicle.vehicle_detail_by_id(user_id=user_id, vehicle_id=vehicle_id)
                if result:
                    return jsonify({"status": True, "data": result}), 200
                else:
                    return jsonify({"status": False, "data": "Not Found"}), 404

            elif request.method == "POST":
                result = Vehicle.vehicle_update_by_id(user_id=user_id, vehicle_id=vehicle_id, **data)
                if result["target_vehicle"] is True and result["double_check_number"] is True:
                    return jsonify({"status": True, "data": result}), 200
                elif result["double_check_number"] is False:
                    return jsonify({"status": False, "data": "Double Check Fail"}), 409
                else:
                    return jsonify({"status": False, "data": "Not Found"}), 404

            elif request.method == "DELETE":
                result = Vehicle.vehicle_delete_by_id(vehicle_id=vehicle_id, user_id=user_id)
                if result:
                    return jsonify({"status": True, "data": result}), 200
                else:
                    return jsonify({"status": False, "data": "Not Found"}), 404

            else:
                return jsonify({"status": False, "data": "Not Allowed Method"}), 405

        else:
            return jsonify(Unauthorized), 401

    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 광고 등록 (Admin에서 해야할 일)
# 등록된 광고 리스트 (ad_information_list)
# 광고 신청 (GET, POST) (차량 정보 및 배송지)
@app.route('/admin/ad/register', methods=['POST'])
def ad_register():
    title_image = request.files.get('title_image')
    logo_image = request.files.get('logo_image')
    sticker_design_side = request.files.get('sticker_design_side')
    sticker_design_back = request.files.get('sticker_design_back')
    sticker_attach_side_image = request.files.get('sticker_attach_side')
    sticker_attach_back_image = request.files.get('sticker_attach_back')
    # Allowed 를 위한 리스트
    image_list = {
        "title_image": title_image.filename,
        "logo_image": logo_image.filename,
        "sticker_design_side_image": sticker_design_side.filename,
        "sticker_design_back_image": sticker_design_back.filename,
        "sticker_attach_side_image": sticker_attach_side_image.filename,
        "sticker_attach_back_image": sticker_attach_back_image.filename
    }
    # image_list = [title_image, logo_image, sticker_design_side, sticker_design_back,
    #               sticker_attach_side_image, sticker_attach_back_image]
    # 결과
    allowed_result = allowed_image_for_dict(image_list)
    # 만약 사진 전부 허용된다면
    if False not in allowed_result:
        try:
            data = request.form
            result = AD.register(image_dict=image_list, **data)
            # directory = "{0}/{1}".format("adverting", "1")
            # os.makedirs(BASE_IMAGE_LOCATION + directory, exist_ok=True)
            # title_image.save(BASE_IMAGE_LOCATION + directory + "/" + secure_filename(title_image.filename))
            return jsonify({"status": True, "data": result}), 200
        except TypeError:
            return jsonify({"status": False, "data": "Bad Request"}), 400
    else:
        return jsonify({"status": False, "data": "Bad Request"}), 400



