# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, render_template, send_file
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import (
    user_model as User,
    vehicle_model as Vehicle,
    ad_model as AD,
    mission_model as Mission,
    admin_model as Admin
)
import os
import logging

from flasgger import Swagger, swag_from
from notification.user_push_nofitication import one_cloud_messaging, multiple_cloud_messaging


logging.basicConfig(filename="log.txt", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__, static_folder='/static/')
app.config["JWT_SECRET_KEY"] = "databasesuperuserset"
app.config['JWT_TOKEN_LOCATION'] = 'headers'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app, resources={r"*": {"origins": "*"}})
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
Forbidden = {"status": False, "data": "Forbidden"}


# 개인정보처리방침
@app.route('/agree/privacy_policy')
@swag_from('route_yml/agree/privacy_policy.yml')
def privacy():
    return render_template('privacy_policy.html')


# 위치기서비스 이용약관
@app.route('/agree/location-based-service')
@swag_from('route_yml/agree/location_based_service.yml')
def location_based_service():
    return render_template('location_based_service.html')


# 이용약관
@app.route('/agree/clause-service')
@swag_from('route_yml/agree/clause_service.yml')
def clause_service():
    return render_template('clause_service.html')


# 마케팅 수신동의
@app.route('/agree/marketing-information')
@swag_from('route_yml/agree/marketing_information.yml')
def marketing_information():
    return render_template('marketing_information.html')


@app.route('/image/<location>/<idx>/<image_file>')
@swag_from('route_yml/image/get_image.yml')
def get_image(location, idx, image_file):
    try:
        image_file = f"/home/cashcaruser21/CashCar/appConfig/static/image/{location}/{idx}/{image_file}"
        return send_file(image_file, mimetype='image/' + image_file.split('.')[-1])
    except FileNotFoundError:
        return jsonify({"status": False, "data": "Not Found Image"}), 404


# 지도 API (Daum postcode)
@app.route('/kakao/postcode', methods=['GET'])
@swag_from('route_yml/address/kakao_address.yml')
def kakao_address():
    return render_template('kakao_address.html')


# 안드로이드 지도
@app.route('/kakao/postcode/and', methods=['GET'])
@swag_from('route_yml/address/kakao_address.yml')
def kakao_address_and():
    return render_template('kakao_address_and.html')


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
        elif result['default'] is False:
            return jsonify({"status": False, "data": "Default Data"}), 406
        else:
            if data['alarm'] == 1:
                push_result = one_cloud_messaging(token=data['fcm_token'],
                                                  body="캐시카플러스에 가입하신 것을 환영합니다! 다양한 서포터즈 활동을 통해 "
                                                       "리워드가 쌓이는 즐거움을 느껴보세요 :D "
                                                  )
                if push_result['success'] >= 1:
                    User.saveAlarmHistory(user_id=result['data']['user_id'],
                                          alarm_type="register", required=0,
                                          description="캐시카플러스에 가입하신 것을 환영합니다! 다양한 서포터즈 활동을 통해 리워드가 쌓이는 즐거움을 느껴보세요 :D"
                                          )
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
            data = {
                "nickname": request.form['nickname'],
                "email": request.form["email"],
                "name": request.form["name"],
                "call_number": request.form["call_number"],
                "gender": request.form["gender"],
                "date_of_birth": request.form["date_of_birth"],
                "alarm": request.form["alarm"],
                "marketing": request.form["marketing"]
            }
            profile_image = request.files.get('profile_image', None)
            if profile_image:
                if allowed_image(profile_image):
                    result = User.update_user_profile(user_id, profile_image, **data)
                else:
                    return jsonify({"status": False, "data": "Not Allowed Image"}), 405
            else:
                result = User.update_user_profile(user_id, **data)

            if result:
                return jsonify({"status": True, "data": "Success Update", "image": result}), 201
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
        result, fcm_token_result = Vehicle.register_vehicle(**data)
        if data["user_id"] == identity_:
            if result["user"] is False:
                return jsonify({"status": False, "data": "Not Correct User"}), 404
            elif result["register"] is False:
                return jsonify({"status": False, "data": "Register Vehicle Limit 3"}), 405
            elif result["double_check_number"] is False:
                return jsonify({"status": False, "data": "Double Check False"}), 409
            else:
                if fcm_token_result:
                    if fcm_token_result['alarm'] == 1:
                        push_result = one_cloud_messaging(token=fcm_token_result['fcm_token'],
                                                          body="차량 등록이 완료되었습니다! 관심이 가는 브랜드의 서포터즈가 되어보세요 :)"
                                                          )
                        if push_result['success'] >= 1:
                            User.saveAlarmHistory(user_id=result['vehicle_information']['user_id'],
                                                  alarm_type="vehicle_register", required=0,
                                                  description="차량 등록이 완료되었습니다! 관심이 가는 브랜드의 서포터즈가 되어보세요 :)"
                                                  )
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


@app.route('/user/alarm/history')
@jwt_required()
@swag_from('route_yml/notification/user_notification_list.yml')
def user_alarm_history():
    user_id = request.args.get('user_id', 0)
    page = request.args.get('page', 1)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    result = User.get_user_alarm_history(user_id=user_id, page=int(page))
    return jsonify({"data": result})


@app.route('/faq/list')
@swag_from('route_yml/user/faq_list.yml')
def user_faq_list():
    result = User.getAllFaQ()
    return jsonify({"data": result})


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
@app.route("/ad/apply", methods=["GET", "POST"])
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
            vehicle_id = request.args.get('vehicle_id', 0)
            status = AD.ad_apply(user_id=user_id, ad_id=ad_id, vehicle_id=vehicle_id, **data)
            if status["user_information"] is False or status["ad_information"] is False or \
                    status["already_apply"] is False or status["area"] is False:
                return jsonify({"status": False, "data": status}), 404
            else:
                return jsonify({"status": True, "data": status}), 200

        else:
            return jsonify({"status": False, "data": "Not Allowed Method"}), 405
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 미션 인증 신청 ongoing -> success -> success_count +1
#             ongoing -> reject -> 미션 실패 (필수미션일 경우)
@app.route("/ad/mission", methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/user/user_mission_apply_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_mission_apply_post.yml', methods=['POST'])
def ad_mission_apply_with_list():
    user_id = request.args.get('user_id')
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    if request.method == 'GET':
        result = User.user_mission_list(user_id=user_id)
        return jsonify({"status": True, "data": result}), 200

    elif request.method == 'POST':
        result_status = {"image_data": True, "mission_data": True,
                         "mission_type": True, "image_allowed": True, "data_not_null": True
                         }
        ad_mission_card_user_id = request.args.get('ad_mission_card_user_id')
        # ad_mission_card_user 테이블의 id와 해당 미션 Id에 맞는 미션타입 조회
        amcu_id_and_mission_type = Mission.get_mission_type_idx_by_stand_by(
            ad_mission_card_user_id=ad_mission_card_user_id)
        if not amcu_id_and_mission_type:
            result_status["mission_data"] = False
            return jsonify({"status": False, "data": result_status})
        # 주행거리 데이터
        travelled_distance = None
        # 미션이 필수 미션인경우
        if int(amcu_id_and_mission_type["mission_type"]) == 0:
            side_image = request.files.get('side_image')
            back_image = request.files.get('back_image')
            instrument_panel_image = request.files.get('instrument_panel_image')
            # Allowed 를 위한 리스트
            image_list = {
                "side_image": side_image,
                "back_image": back_image,
                "instrument_panel_image": instrument_panel_image
            }
            travelled_distance = request.form["travelled_distance"]
        # 미션이 선택미션인 경우
        elif int(amcu_id_and_mission_type["mission_type"]) == 1:
            side_image = request.files.get('side_image')
            back_image = request.files.get('back_image')
            # Allowed 를 위한 리스트
            image_list = {
                "side_image": side_image,
                "back_image": back_image
            }
        else:
            result_status["mission_type"] = False
            return jsonify({"status": False, "data": result_status})

        # 이미지 결과
        try:
            allowed_result = allowed_image_for_dict(image_list)
            if False not in allowed_result:
                result = Mission.user_apply_mission(
                    ad_mission_card_user_id=amcu_id_and_mission_type["ad_mission_card_user_id"],
                    ad_mission_card_id=amcu_id_and_mission_type["ad_mission_card_id"],
                    mission_type=int(amcu_id_and_mission_type["mission_type"]),
                    image_dict=image_list,
                    travelled_distance=travelled_distance
                )
                if result:
                    return jsonify({"status": True, "data": result_status})
            else:
                result_status["image_allowed"] = False
                return jsonify({"status": False, "data": result_status})
        except AttributeError:
            result_status["image_data"] = False
            return jsonify({"status": False, "data": result_status})
        except TypeError:
            result_status["data_not_null"] = False
            return jsonify({"status": False, "data": result_status})


# /ad/mission
# 사용자의 진행중인 광고 정보 카드(광고 취소 기능 포함)
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
        return jsonify({"status": True, "data": result}), 200

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


# 사용자 배송지 설정
@app.route('/user/set/address', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/user/user_set_address_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_set_address_post.yml', methods=['POST'])
def user_set_address():
    try:
        user_id = request.args.get('user_id')
        identity_ = get_jwt_identity()
        if int(user_id) != identity_:
            return jsonify(Unauthorized), 401
        if request.method == 'GET':
            result = User.get_user_address(user_id=user_id)
            return jsonify(result)

        elif request.method == 'POST':
            data = request.get_json()
            result = User.user_address_update(user_id=user_id, **data)
            return jsonify(result)
    except TypeError:
        return jsonify({"data": "Data Not Null"}), 400


# 사용자 포인트 히스토리
@app.route('/user/point/history')
def user_point_history():
    user_id = request.args.get('user_id')
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401


# 사용자 포인트 출금
@app.route('/user/withdrawal/point', methods=['GET'])
def user_withdrawal():
    user_id = request.args.get('user_id')
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401


# 메세지 읽음표시
@app.route('/user/is-read', methods=['POST'])
@swag_from('route_yml/user/user_message_is_read.yml')
def user_is_read_message():
    ad_mission_reason_id = request.args.get('reason_id')
    User.update_reason_by_user(reason_id=ad_mission_reason_id)
    return jsonify(True)


# 마이페이지 (마이캐시카)
@app.route('/user/my-page')
@jwt_required()
@swag_from('route_yml/user/user_my_page.yml')
def user_my_page():
    try:
        user_id = request.args.get('user_id', 0)
        identity_ = get_jwt_identity()
        if int(user_id) != identity_:
            return jsonify(Unauthorized), 401

        result = User.get_user_my_page(user_id)
        return jsonify({"data": result})

    except KeyError:
        return jsonify({"data": "Data Not Null"}), 400


# 공지사항 리트스
@app.route('/notice/list')
@jwt_required()
@swag_from('route_yml/user/notice_list.yml')
def notice_list():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    result = Admin.user_get_notice_list()
    return jsonify({"data": result})


# 사용자 포인트
@app.route('/user/point')
@jwt_required()
def user_point():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    # result =


# 사용자 출금 신청
@app.route('/user/point/withdrawal/point', methods=['GET', 'POST'])
@jwt_required()
def user_point_withdrawal():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    if request.method == 'GET':
        result = User.get_user_withdrawal_data(user_id=user_id)
        return jsonify({"data": result})

    elif request.method == 'POST':
        data = request.get_json()
        result = User.update_user_withdrawal_data(user_id=user_id, **data)


########### ADMIN ############
# 어드민 권한 확인
def admin_allowed_user_check(admin_user_id, identity_):
    if int(admin_user_id) == identity_:
        allowed_user = Admin.allowed_in_role_user(admin_user_id)
        if allowed_user:
            return True, True
        else:
            return Forbidden, 403
    else:
        return Unauthorized, 401


# 공지사항 등록
@app.route('/admin/notice/register', methods=['POST'])
@jwt_required()
@swag_from('route_yml/admin/notice_register.yml')
def register_notice_by_admin():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    if int(admin_user_id) != identity_:
        return jsonify(Unauthorized), 401

    try:
        data = request.get_json()
        result = Admin.admin_register_notice(**data)
        return jsonify({"data": result})
    except KeyError:
        return jsonify({"status": False})
    except TypeError:
        return jsonify({"status": False})


# 공지사항 수정 및 삭제 및 데이터 가져오기
@app.route('/admin/notice', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
@swag_from('route_yml/admin/notice_list.yml', methods=['GET'])
@swag_from('route_yml/admin/notice_modify.yml', methods=['POST'])
@swag_from('route_yml/admin/notice_delete.yml', methods=['DELETE'])
def modify_notice_by_admin():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    if int(admin_user_id) != identity_:
        return jsonify(Unauthorized), 401
    try:
        if request.method == 'GET':
            page = request.args.get('page', 1)
            count = request.args.get('count', 10)
            result, item_count = Admin.admin_get_notice_list(page=int(page), count=int(count))
            return jsonify({"data": result, "item_count": item_count})

        elif request.method == 'POST':
            notice_id = request.args.get('notice_id', 0)
            data = request.get_json()
            result = Admin.update_notice(notice_id=notice_id, **data)
            return jsonify({"data": result})

        elif request.method == 'DELETE':
            notice_id = request.args.get('notice_id', 0)
            Admin.delete_notice(notice_id=notice_id)
            return jsonify({"status": True})
    except KeyError:
        return jsonify({"status": False})


# 아이디 등록
@app.route('/admin/user/register', methods=['POST'])
def admin_user_register():
    data = request.get_json()
    result = Admin.register(**data)
    return jsonify(result)


@app.route('/admin/user/login', methods=['POST'])
@swag_from('route_yml/admin/login.yml')
def admin_user_login():
    data = request.get_json()
    result = Admin.login(**data)
    return jsonify(result)


# 이미지 (썸네일, 스티커 이미지, 광고 이미지)
@app.route('/admin/adverting/register', methods=['POST', 'DELETE'])
@jwt_required()
@swag_from('route_yml/admin/advertisement_register.yml', methods=['POST'])
def admin_adverting_register():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    if int(admin_user_id) != identity_:
        return jsonify(Unauthorized), 401
    # 권한 확인
    allowed_user = Admin.allowed_in_role_user(admin_user_id)
    if not allowed_user:
        return jsonify(Forbidden), 403

    side_image = request.files.get('side_image')
    back_image = request.files.get('back_image')
    thumbnail_image = request.files.get('thumbnail_image')
    # 기타 사진들
    images = request.files.getlist('ad_images')
    # 썸네일, 좌측, 후면 사진
    image_dict = {
        "side_image": side_image,
        "back_image": back_image,
        "thumbnail_image": thumbnail_image
    }

    allowed_ad_images = allowed_files(images)
    allowed_other_images = allowed_image_for_dict(image_dict)
    if False not in allowed_ad_images and allowed_other_images is not False:
        # eval 의 사용이유는 getlist 로 데이터를 가져올 경우 ['{}'] 인 스트링 형태로 데이터가 들어오기 때문에 강제로 여러개의 프로퍼티 값으로 변환
        # 클라이언트와 데이터의 형식을 맞춰 사용할 경우 위험성은 없어보임.
        data = {
            'ad_id': request.args.get('ad_id', 0),
            'title': request.form.get('title'),
            'owner_name': request.form.get('owner_name'),
            'description': request.form.get('description'),
            'total_point': request.form.get('total_point'),
            'activity_period': request.form.get('activity_period'),
            'recruit_start_date': request.form.get('recruit_start_date'),
            'recruit_end_date': request.form.get('recruit_end_date'),
            'max_recruiting_count': request.form.get('max_recruiting_count'),
            'area': request.form.get('area'),
            'gender': request.form.get('gender'),
            'min_age_group': request.form.get('min_age_group', 0),
            'max_age_group': request.form.get('max_age_group', 0),
            'min_distance': request.form.get('min_distance', 0),
            'side_length': request.form.get('side_length'),
            'side_width': request.form.get('side_width'),
            'back_length': request.form.get('back_length'),
            'back_width': request.form.get('back_width'),
            'default_mission_items': [eval(item) for item in request.form.getlist('default_mission_items')],
            'additional_mission_items': [eval(item) for item in request.form.getlist('additional_mission_items')]
        }
        result = AD.admin_ad_register(other_images=image_dict, ad_images=images, req_method=request.method, **data)
        if result:
            return jsonify({"data": {"allowed_image": True, "success": True, "registered": result}})
        else:
            return jsonify({"data": {"allowed_image": True, "success": False, "registered": {}}})
    else:
        return jsonify({"data": {"allowed_image": False, "success": False}})


# 광고 미션 수정 or 삭제
# @app.route('/admin/ad/mission/update', methods=['POST', 'DELETE'])
# ad_mission_card_id = request.args.get('ad_mission_card_Id')

# 어드민 광고 리스트
@app.route('/admin/ad/list')
@jwt_required()
@swag_from('route_yml/admin/advertisement_ad_list.yml')
def admin_ad_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    if int(admin_user_id) != identity_:
        return jsonify(Unauthorized), 401
    # 권한 확인
    allowed_user = Admin.allowed_in_role_user(admin_user_id)
    if not allowed_user:
        return jsonify(Forbidden), 403
    page = request.args.get('page', 1)
    category = request.args.get('category', 'none')
    point = request.args.get('point', '0~900000')
    area = request.args.get('area', '')
    gender = request.args.get('gender', '0')
    age = request.args.get('age', '0~200')
    distance = request.args.get('distance', '0')
    recruit_start_date = request.args.get('recruit_start', '0000-00-00')
    recruit_end_date = request.args.get('recruit_end', '9999-12-30')
    order_by = request.args.get('order_by', 'ad_id')
    sort = request.args.get('sort', 'ASC')
    count = request.args.get('count', 10)
    if area == '':
        area_list = area
    else:
        if len(area.split(',')) <= 1:
            area_list = area
        else:
            area_list = area.split(',')
    avg_point = point.split('~')
    avg_age = age.split('~')
    result, item_count = Admin.get_all_by_admin_ad_list(category=category, avg_point=avg_point, area=area_list,
                                                        gender=gender, avg_age=avg_age, distance=distance,
                                                        recruit_start=recruit_start_date, recruit_end=recruit_end_date,
                                                        order_by=order_by, sort=sort,
                                                        page=int(page), count=int(count)
                                                        )
    return jsonify({"data": result, "item_count": item_count})


# 광고 신청한 사용자 리스트 모집번호 추가
@app.route('/admin/ad/list/user-list')
@jwt_required()
@swag_from('route_yml/admin/advertisement_user_list.yml')
def admin_ad_list_user_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    if int(admin_user_id) != identity_:
        return jsonify(Unauthorized), 401
    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    ad_id = request.args.get('ad_id', 0)
    result, item_count = User.user_apply_id_by_ad_id(page=int(page), count=int(count), ad_id=ad_id)
    return jsonify({"data": result, "item_count": item_count})


# 광고신청 리스트
@app.route("/admin/ad/apply/list")
@jwt_required()
@swag_from('route_yml/admin/advertisement_user_apply_list.yml')
def admin_user_apply_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    result, item_count = AD.ad_apply_list(page=page, count=count)
    if result:
        return jsonify({"status": True, "data": result, "item_count": item_count}), 200
    else:
        return jsonify({"status": True, "data": []}), 201


# 광고신청 승인 or 거절
@app.route("/admin/ad/apply", methods=["GET", "POST"])
@jwt_required()
@swag_from('route_yml/admin/advertisement_apply_post.yml', methods=['POST'])
def admin_ad_apply():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code
    try:
        if request.method == "POST":
            data = request.get_json()
            result, user_fcm_list = AD.update_ad_apply_status(**data)
            if user_fcm_list:
                if data['status'] == "accept":
                    push_result = multiple_cloud_messaging(tokens=user_fcm_list,
                                                           body="서포터즈 신청이 승인되었습니다. 스티커를 받은 후 1차 미션을 인증해주세요!"
                                                           )

                elif data["status"] == "reject":
                    push_result = multiple_cloud_messaging(tokens=user_fcm_list,
                                                           body="서포터즈 신청 조건에 만족하지 못하여 신청이 거절되었습니다, 다음 기회에 다시 도전해주세요ㅠㅜ"
                                                           )
            return jsonify({"data": result})
        else:
            return jsonify({"status": False, "data": "Not Allowed Method"}), 405
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 사용자 미션 인증 에서 상태 변경
@app.route('/admin/mission/apply', methods=['POST'])
@jwt_required()
@swag_from('route_yml/admin/mission_apply_post.yml')
def admin_mission_apply():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code
    try:
        mission_card_id = request.args.get('mission_id')
        ad_apply_id = request.args.get('ad_apply_id')
        data = request.get_json()
        result = Admin.admin_accept_mission(ad_apply_id=ad_apply_id, mission_card_id=mission_card_id, **data)
        if result['accept'] is True:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except TypeError:
        return jsonify({"accept": False, "reason": "Data Not Null"}), 400


# 사용자 미션 인증 요청 리스트
@app.route('/admin/mission/list')
@jwt_required()
@swag_from('route_yml/admin/mission_list.yml')
def admin_mission_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code
    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    result, item_count = Mission.admin_review_mission_list(page=int(page), count=int(count))
    return jsonify({"data": result, "item_count": item_count})


# 사용자 미션 인증 요청 리스트에서 해당 사용자의 모든 미션 리스트를 볼수있는 데이터
@app.route('/admin/mission/all/list')
@jwt_required()
@swag_from('route_yml/admin/mission_list_all.yml')
def admin_mission_list_by_user():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code
    ad_user_apply_id = request.args.get('ad_user_apply_id')
    mission_card_id = request.args.get('mission_card_id')
    result = Mission.admin_review_detail_mission_list(
        ad_user_apply_id=ad_user_apply_id,
        ad_mission_card_id=mission_card_id
    )
    return jsonify({"data": result})


# 어드민 회원관리
@app.route('/admin/user/list')
@jwt_required()
@swag_from('route_yml/admin/admin_get_all_user_list.yml')
def admin_get_all_user_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    # area = request.args.get('area', '')
    # gender = request.args.get('gender', 0)
    # age = request.args.get('age', '0~200')
    # register_time = request.args.get('register_time', '0000-00-00 00:00:00 ~ 9999-12-30 00:00:00')
    # avg_register_time = register_time.split('~')
    # avg_age = age.split('~')
    result, item_count = Admin.get_all_user_list(page=page, count=count)
    return jsonify({"data": result, "item_count": item_count})


# 회원 정보에서 보유 포인트 이력
@app.route('/user/point')
@jwt_required()
@swag_from('route_yml/user/user_get_point_history.yml')
def get_point_all_by_user_id():
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    result, item_count = User.get_point_all_by_user(user_id=user_id, page=page, count=count)
    return jsonify({"data": result, "item_count": item_count})


# 어드민 출금 신청 리스트  ## status 의 값들 swagger 추가
@app.route('/admin/user/withdrawal/point', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/admin/admin_withdrawal_self_point_get.yml', methods=['GET'])
@swag_from('route_yml/admin/admin_withdrawal_self_point_post.yml', methods=['POST'])
def get_withdrawal_self_point_all():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code
    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    if request.method == 'GET':
        result, item_count = Admin.get_all_withdrawal_point(page=page, count=count)
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        data = request.get_json()
        result = Admin.update_withdrawal_point(**data)
        return jsonify({"data": result})


# 어드민 기부 신청 리스트
@app.route('/admin/user/withdrawal/donate', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/admin/admin_withdrawal_donate_point_get.yml', methods=['GET'])
@swag_from('route_yml/admin/admin_withdrawal_donate_point_post.yml', methods=['POST'])
def get_withdrawal_donate_point_all():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1)
    count = request.args.get('count', 10)
    if request.method == 'GET':
        result, item_count = Admin.get_all_withdrawal_donate(page=page, count=count)
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        withdrawal_donate_id = request.args.get('withdrawal_donate_id', 0)
        if withdrawal_donate_id != 0:
            data = request.get_json()
            result = Admin.update_withdrawal_donate(withdrawal_donate_id=withdrawal_donate_id, **data)
            return jsonify({"data": result})
        else:
            return jsonify({"data": False})
