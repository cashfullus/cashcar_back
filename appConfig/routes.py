# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, render_template
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename

from appConfig import secret_key

from .models import (
    user_model as User,
    vehicle_model as Vehicle,
    ad_model as AD,
    mission_model as Mission
)
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
        filename = image.filename
        result.append('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return result


def allowed_image(image):
    filename = image.filename
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 회원가입 전 이용약관 동의 받기

# 토큰 인증 실패시 return 하는 response 의 중복적인 사용으로 인해 return 변수를 저장해서 쓰는게 낫다고 생각함.
Unauthorized = {"status": False, "data": "Unauthorized"}


# 지도 API (Daum postcode)
@app.route('/kakao/postcode', methods=['GET'])
@swag_from('route_yml/address/kakao_address.yml')
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
@swag_from('route_yml/admin/advertisement_register.yml')
def ad_register():
    title_image = request.files.get('title_image')
    logo_image = request.files.get('logo_image')
    # Allowed 를 위한 리스트
    image_list = {
        "title_image": title_image,
        "logo_image": logo_image
    }
    # 결과
    allowed_result = allowed_image_for_dict(image_list)
    # 만약 사진 전부 허용된다면
    if False not in allowed_result:
        data = request.form
        result = AD.register(image_dict=image_list, **data)
        if result:
            return jsonify({"status": True, "data": result}), 200
        else:
            return jsonify({"status": False, "data": "Not Found"}), 404
    else:
        return jsonify({"status": False, "data": "Not Allowed File"}), 405


# 광고 리스트 (진행중="ongoing", 예정="scheduled", 완료="done")
@app.route("/ad/list")
@jwt_required()
@swag_from('route_yml/advertisement/advertisement_list_get.yml', methods=['GET'])
def ongoing_ad_information():
    category = request.args.get('category')
    page = request.args.get('page')
    if int(page) == 0:
        page = 1
    result, status = AD.get_all_by_category_ad_list(page=int(page), category=category)
    if status["correct_category"] is True:
        return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": False, "data": "Not Allowed Category"}), 405


# 메인화면 신청 진행중인 카드 (신청취소는 한시간 전까지만)


# 광고 세부정보
@app.route("/ad")
@jwt_required()
@swag_from('route_yml/advertisement/advertisement_information_get.yml', methods=['GET'])
def ad_information_detail():
    ad_id = request.args.get('ad_id')
    result = AD.get_ad_information_by_id(ad_id=ad_id)
    if result:
        return jsonify({"status": True, "data": result})
    else:
        return jsonify({"status": False, "data": "Not Found"}), 404


# 광고 신청
@app.route("/ad/apply", methods=["GET", "POST", "DELETE"])
@jwt_required()
@swag_from('route_yml/user/user_apply_ad_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_apply_ad_post.yml', methods=['POST'])
def ad_apply():
    try:
        user_id = request.args.get('user_id')
        ad_id = request.args.get('ad_id')
        identity_ = get_jwt_identity()
        if int(user_id) != identity_:
            return jsonify(Unauthorized), 401

        if request.method == "GET":
            result, status = AD.get_information_for_ad_apply(user_id=user_id, ad_id=ad_id)
            if status["ad_information"] is False or status["user_information"] is False:
                return jsonify({"status": False, "data": status}), 404
            else:
                return jsonify({"status": True, "data": result}), 200

        elif request.method == "POST":
            data = request.get_json()
            status = AD.ad_apply(user_id=user_id, ad_id=ad_id, **data)
            if status["user_information"] is False or status["ad_information"] is False or status["already_apply"] is False:
                return jsonify({"status": False, "data": status}), 404
            else:
                return jsonify({"status": True, "data": status}), 200

        else:
            return jsonify({"status": False, "data": "Not Allowed Method"}), 405
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 사용자의 진행중인 광고 정보 카드
@app.route("/main/my-ad", methods=["GET", "DELETE"])
@jwt_required()
@swag_from('route_yml/user/user_my_ad_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_my_ad_delete.yml', methods=['DELETE'])
def home_my_ad():
    user_id = request.args.get('user_id')
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    if request.method == 'GET':
        result = AD.get_ongoing_user_by_id(user_id=user_id)
        if result:
            return jsonify({"status": True, "data": result})
        else:
            return jsonify({"status": False, "data": "Not Found"}), 201

    elif request.method == 'DELETE':
        ad_user_apply_id = request.args.get('ad_user_apply_id')
        result = AD.cancel_apply_user(ad_user_apply_id=ad_user_apply_id)
        if result["apply_information"] is False:
            return jsonify({"status": False, "data": "Not Found Apply"}), 404
        elif result["time_out"] is False:
            return jsonify({"status": False, "data": "Time Out For Cancel"}), 403
        else:
            return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": False, "data": "Not Allowed Method"}), 405


# 광고신청 리스트
@app.route("/admin/ad/apply/list")
@swag_from('route_yml/admin/advertisement_user_apply_list.yml')
def admin_user_apply_list():
    result = AD.ad_apply_list()
    if result:
        return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": True, "data": []}), 201


# 광고신청 승인 or 거절
@app.route("/admin/ad/apply", methods=["GET", "POST"])
@swag_from('route_yml/admin/advertisement_apply_get.yml', methods=['GET'])
def admin_ad_apply():
    try:
        ad_user_apply_id = request.args.get('ad_user_apply_id')
        if request.method == "GET":
            result = AD.get_ad_apply(ad_user_apply_id)
            if result:
                return jsonify({"status": True, "data": result}), 200
            else:
                return jsonify({"status": False, "data": "Not Found"}), 404

        elif request.method == "POST":
            data = request.get_json()
            result = AD.update_ad_apply_status(ad_user_apply_id=ad_user_apply_id, **data)
            if result["rejected"] is True and result["accept"] is True:
                return jsonify({"status": True, "data": result}), 200
            else:
                return jsonify({"status": False, "Data": result}), 404
        else:
            return jsonify({"status": False, "data": "Not Allowed Method"}), 405
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# mission_type  (0 = required, 1 = additional)
@app.route('/admin/mission/card/register', methods=["POST"])
@swag_from('route_yml/admin/mission_card_register.yml')
def mission_card_register():
    try:
        data = request.get_json()
        result = Mission.register(**data)
        return jsonify({"status": True, "data": result}), 200
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 404


# 미션카드 광고에 배정 ex) ad_id=1 mission_id=1, ad_id=1 mission_id=2
@app.route("/admin/mission/advertisement", methods=["POST"])
@swag_from('route_yml/admin/mission_advertisement_assign.yml')
def mission_to_advertisement():
    try:
        data = request.get_json()
        result = Mission.mission_assign_advertisement(**data)
        return jsonify({"status": True, "data": result}), 200
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 404


# stand_by 대기중, review 검토중, success 미션성공, fail 미션실패,  authenticate 인증하기
@app.route("/admin/mission/image", methods=["POST"])
def mission_image():
    side_image = request.files.get('side_image')
    back_image = request.files.get('back_image')

    # Allowed 를 위한 리스트
    image_list = {
        "side_image": side_image,
        "back_image": back_image
    }
    # 결과
    allowed_result = allowed_image_for_dict(image_list)
    if False not in allowed_result:
        result = Mission.mission_save_images(image_list)
        return jsonify({"status": True, "data": result}), 200
    else:
        return jsonify({"status": False, "data": "Not Allowed File"}), 405
