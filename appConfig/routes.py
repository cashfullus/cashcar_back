# -*- coding: utf-8 -*-
import json

from flask import Flask, jsonify, request, render_template, send_file, redirect
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename

from logging.handlers import WatchedFileHandler

from models import (
    user_model as User,
    vehicle_model as Vehicle,
    ad_model as AD,
    mission_model as Mission,
    admin_model as Admin,
    system_model as System,
    cashcar_tip_model as Tip,
    notification_model as Notification
)
import os
import logging
import requests
import subprocess

from flasgger import Swagger, swag_from, LazyString, LazyJSONEncoder
from notification.user_push_nofitication import one_cloud_messaging, multiple_cloud_messaging

# 메일 발송
from flask_mail import Mail, Message

logging.basicConfig(filename="log.txt", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
app = Flask(__name__, template_folder='templates')
app.config["JWT_SECRET_KEY"] = "databasesuperuserset"
app.config['JWT_TOKEN_LOCATION'] = 'headers'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cashfullus@gmail.com'
app.config['MAIL_PASSWORD'] = 'zotlvnfdjtm12'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.json_encoder = LazyJSONEncoder
CORS(app, resources={r"*": {"origins": "*"}})
jwt_manager = JWTManager(app)
mail = Mail()
mail.init_app(app)
template = dict(swaggerUiPrefix=LazyString(lambda: request.environ.get('HTTP_X_SCRIPT_NAME', '')))
swagger = Swagger(app, template=template)
# 이미지 파일 형식
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
BASE_IMAGE_LOCATION = os.getcwd() + "/appConfig/static/image/"
kakao_client_id = '15c625b843651faa96695d0b5001f858'
SERVER_HOST_NAME = "https://app.api.service.cashcarplus.com:50193"
LOCAL_HOST_NAME = "http://localhost:50123"


@app.before_first_request
def setup_logging():
    """
    Setup logging
    """
    directory = os.getcwd()
    handler = WatchedFileHandler(directory + "/flask_app.log")
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


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


@app.route('/github/webhook')
def webhook():
    subprocess.call("git pull", shell=True)
    subprocess.call("service uwsgi reload", shell=True)
    subprocess.call("service nginx reload", shell=True)
    return jsonify({"Data": True})


# 제3자 정보제공 동의
@app.route('/agree/provide-policy')
@swag_from('route_yml/agree/provide_policy.yml')
def provide_policy():
    return render_template('provide_policy.html')


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


# 통합 금융정보 및 전자문서 서비스 약관
@app.route('/agree/terms_of_service')
@swag_from('route_yml/agree/terms_of_service.yml')
def terms_of_service():
    return render_template('terms_of_service.html')


# 이미지 send
@app.route('/image/<location>/<idx>/<image_file>', methods=['GET', 'DELETE'])
@swag_from('route_yml/image/get_image.yml')
def get_image(location, idx, image_file):
    if request.method == 'GET':
        try:
            image_file = f"static/image/{location}/{idx}/{image_file}"
            return send_file(image_file, mimetype='image/' + image_file.split('.')[-1])
        except FileNotFoundError:
            return jsonify({"status": False, "data": "Not Found Image"}), 404
    elif request.method == 'DELETE':
        try:
            result = System.delete_image(location=location, idx=idx, image=image_file)
            if result:
                file_path = f"static/image/{location}/{idx}/{image_file}"
                os.remove(file_path)
                return jsonify({"status": True})
            else:
                return jsonify({"status": False})
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


# 앱 버전 체크 확인
@app.route('/app/version')
@swag_from('route_yml/system/app_version_check.yml')
def app_version_check():
    device = request.args.get('device', "")
    result = System.get_app_version_check(device=device)
    return jsonify(result)


# FCM 토큰
@app.route("/user/fcm", methods=["POST"])
@swag_from('route_yml/user/user_fcm.yml', methods=["POST"])
def fmc_token():
    try:
        data = request.get_json()
        user_agent = request.headers.get('User-Agent', '')
        result = User.user_fcm(user_agent, **data)
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


@app.route('/oauth/kakao')
def kakao_login():
    client_id = kakao_client_id
    # redirect_uri = SERVER_HOST_NAME + "/oauth/kakao/callback"
    redirect_uri = LOCAL_HOST_NAME + "/oauth/kakao/callback"
    kakao_oauthurl = f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    return redirect(kakao_oauthurl)


@app.route('/oauth/kakao/callback')
def kakao_callback():
    try:
        # 위 oauth/kakao에서 redirect로 요청을 보낸후 callback으로 돌아온 uri 에서 code쿼리스트링 받기
        code = request.args.get('code')
        client_id = kakao_client_id
        # 다시 재요청 들어올 redirect_uri callback 지정
        # redirect_uri = SERVER_HOST_NAME + "/oauth/kakao/callback"
        redirect_uri = LOCAL_HOST_NAME + "/oauth/kakao/callback"
        token_request = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={client_id}&redirect_uri={redirect_uri}&code={code}"
        )
        # 최종적으로 사용자 정보를 받기위한 토큰 발급
        token_response = token_request.json()
        # 내용에 error 가 존재한다면.
        error = token_response.get('error', None)
        if error is not None:
            return jsonify({"message": "INVALID_CODE"}), 400

        # access_token 받아오기
        access_token = token_response.get('access_token')
        # access_token으로 유저 정보 받아오기
        profile_request = requests.get(
            "https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {access_token}"},
        )
        # 최종적으로 받은 data
        data = profile_request.json()
    except KeyError:
        return jsonify({"message": "INVALID_TOKEN"}), 400

    return jsonify({"data": data})


# 애플 로그인
@app.route('/oauth/apple')
def apple_auth():
    return render_template("apple_login.html")


# 애플 로그인 callback
# @app.route('/oauth/apple/callback')
# def apple_auth_callback():


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
            User.saveAlarmHistory(user_id=result['data']['user_id'],
                                  alarm_type="register", required=1,
                                  description="캐시카플러스에 가입하신 것을 환영합니다! 다양한 서포터즈 활동을 통해 리워드가 쌓이는 즐거움을 느껴보세요 :D"
                                  )
            return jsonify({"status": True, "data": result["data"]}), 201
    except TypeError:
        return jsonify({"status": False, "data": "Data Not Null"}), 400


# 사용자 로그인 후 비밀번호 변경
@app.route('/user/new-password', methods=['POST'])
@jwt_required()
@swag_from('route_yml/user/change_password_after_login.yml')
def user_new_password():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    data = request.get_json()
    result = User.login_user_change_password(user_id=user_id, **data)
    return jsonify(result)


# 사용자 비밀번호 재설정(이메일 인증)
@app.route('/send/email/password', methods=['POST'])
@swag_from('route_yml/user/user_auth_email_for_password.yml')
def send_to_client_for_password():
    data = request.get_json()
    result, auth_number = User.user_email_check_for_password(**data)
    if result:
        msg = Message("캐시카 플러스 비밀번호 재설정", sender="cashfullus@gmail.com", recipients=[data['email']])
        msg.body = auth_number
        mail.send(msg)
        return jsonify({"status": True})
    else:
        return jsonify({"status": False})


# 사용자 이메일 전송된 인증번호 인증
@app.route('/sent/email/auth', methods=['POST'])
@swag_from('route_yml/user/user_email_auth_number_check.yml')
def email_auth_number_check():
    data = request.get_json()
    result = User.user_email_auth_number_check(**data)
    return jsonify(result)


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
        user_id = request.args.get('user_id', 0, int)
        identity_ = get_jwt_identity()
        if user_id != identity_:
            return jsonify(Unauthorized), 401

        if request.method == "GET":
            set_result = User.UserProfile(user_id=user_id)
            result = set_result.response()
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
        result = Vehicle.register_vehicle(**data)
        if data["user_id"] == identity_:
            if result["user"] is False:
                return jsonify({"status": False, "data": "Not Correct User"}), 404
            elif result["register"] is False:
                return jsonify({"status": False, "data": "Register Vehicle Limit 3"}), 405
            elif result["double_check_number"] is False:
                return jsonify({"status": False, "data": "Double Check False"}), 409
            else:
                User.saveAlarmHistory(user_id=result['vehicle_information']['user_id'],
                                      alarm_type="vehicle_register", required=1,
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

        set_response = Vehicle.VehicleList()
        result = set_response.response(user_id=user_id)
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
                set_response = Vehicle.VehicleDetail()
                result = set_response.response(user_id=user_id, vehicle_id=vehicle_id)
                if result:
                    return jsonify({"status": True, "data": result}), 200
                else:
                    return jsonify({"status": False, "data": "Not Found"}), 404

            elif request.method == "POST":
                set_response = Vehicle.VehicleUpdate(**data)
                result = set_response.response(user_id=user_id, vehicle_id=vehicle_id)
                if result["target_vehicle"] is True and result["double_check_number"] is True:
                    return jsonify({"status": True, "data": result}), 200
                elif result["double_check_number"] is False:
                    return jsonify({"status": False, "data": "Double Check Fail"}), 409
                else:
                    return jsonify({"status": False, "data": "Not Found"}), 404

            elif request.method == "DELETE":
                set_response = Vehicle.VehicleDelete()
                result = set_response.response(user_id=user_id, vehicle_id=vehicle_id)
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
    page = request.args.get('page', 1, int)
    advertisement = AD.AdvertisementList()
    result, status = advertisement.get_all_by_category_ad_list(page=page, category=category)
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
            set_status = AD.UserAdApply(user_id=user_id, ad_id=ad_id, vehicle_id=vehicle_id, **data)
            status = set_status.response()
            if status["user_information"] is False or status["ad_information"] is False or \
                    status["already_apply"] is False or status["area"] is False or status['reject_apply'] is False:
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
            latitude = request.form.get('latitude', "", str)
            longitude = request.form.get('longitude', "", str)
            allowed_result = allowed_image_for_dict(image_list)
            if False not in allowed_result:
                result = Mission.user_apply_mission(
                    ad_mission_card_user_id=amcu_id_and_mission_type["ad_mission_card_user_id"],
                    mission_type=int(amcu_id_and_mission_type["mission_type"]),
                    image_dict=image_list,
                    travelled_distance=travelled_distance,
                    latitude=latitude,
                    longitude=longitude
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
        set_response = AD.UserMyAd(user_id=user_id)
        response = set_response.response()
        return jsonify({"status": True, "data": response}), 200

    elif request.method == 'DELETE':
        ad_user_apply_id = request.args.get('ad_user_apply_id')
        set_response = AD.UserApplyCancel(ad_user_apply_id=ad_user_apply_id)
        result = set_response.response()
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


@app.route('/user/badge-list')
@jwt_required()
@swag_from('route_yml/user/user_badge_list.yml')
def user_badge_list():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    result = User.get_all_my_badge_list(user_id=user_id)
    return jsonify(result)


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


# 사용자 포인트 페이지 q = "", "donate", "positive", "negative"
@app.route('/user/information/point')
@jwt_required()
@swag_from('route_yml/user/user_point_information.yml')
def user_point_information():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    page: int = request.args.get('page', 1, int)
    count: int = request.args.get('count', 8, int)
    q: str = request.args.get('q', '', str)
    result = User.get_user_point_and_history(user_id=user_id, page=page, count=count, q=q)
    return jsonify({"data": result})


# 사용자 포인트 출금
@app.route('/user/withdrawal/point', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/user/user_withdrawal_point_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_withdrawal_point_post.yml', methods=['POST'])
def user_withdrawal_point():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    if request.method == 'GET':
        result = User.get_user_withdrawal_data(user_id=user_id)
        return jsonify(result)

    elif request.method == 'POST':
        data = request.get_json()
        result = User.update_user_withdrawal_data(user_id=user_id, **data)
        return jsonify(result)


# 사용자 기부 신청
@app.route('/user/withdrawal/donate', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/user/user_withdrawal_donate_get.yml', methods=['GET'])
@swag_from('route_yml/user/user_withdrawal_donate_post.yml', methods=['POST'])
def user_withdrawal_donate():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    donation_id = request.args.get('donation_organization_id')
    if request.method == 'GET':
        result = User.get_user_withdrawal_donate_data(user_id=user_id, donation_id=donation_id)
        return jsonify(result)

    elif request.method == 'POST':
        data = request.get_json()
        result = User.update_user_withdrawal_donate(user_id=user_id, donation_id=donation_id, **data)
        return jsonify(result)


# 사용자 기부 페이지
@app.route('/user/donate/list')
@jwt_required()
@swag_from('route_yml/donation/organization_list.yml')
def user_donate_list():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    page = request.args.get('page', 1, type=int)
    count = request.args.get('count', 10, type=int)
    set_result = User.UserDonationList(user_id=user_id, page=page, count=count)
    result, donate_status = set_result.response()
    return jsonify({"data": result, "ongoing": donate_status})


# 기부단체 상세페이지
@app.route('/user/donate')
@jwt_required()
@swag_from('route_yml/donation/organization_detail.yml')
def user_donate():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    donation_id = request.args.get('donation_organization_id')
    set_data = User.UserDonationDetail(donation_id=donation_id)
    response = set_data.response()
    return jsonify(response)


# 사용자 캐시카팁 리스트
@app.route('/user/cash-car-tip/list')
@jwt_required()
@swag_from('route_yml/user/cash_car_tip_list.yml')
def user_cash_car_tip_list():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    page = request.args.get('page', 1, type=int)
    result = Tip.get_cash_car_tip_all(page=page, request_user="user")
    return jsonify(result)


@app.route('/user/cash-car-tip')
@jwt_required()
@swag_from('route_yml/user/cash_car_tip.yml')
def user_cash_car_tip():
    user_id = request.args.get('user_id', 0)
    identity_ = get_jwt_identity()
    if int(user_id) != identity_:
        return jsonify(Unauthorized), 401

    tip_id = request.args.get('tip_id')
    result = Tip.get_cash_car_tip_by_id(cash_car_tip_id=tip_id)
    return jsonify(result)


# 사용자 서포터즈  활동대한 필수 알림
@app.route('/user/alarm', methods=['POST'])
@jwt_required()
@swag_from('route_yml/user/user_alarm.yml')
def user_alarm():
    user_id: int = request.args.get('user_id', 0, int)
    identity_: int = get_jwt_identity()
    if user_id != identity_:
        return jsonify(Unauthorized), 401

    is_on: int = request.args.get('is_on', 0, int)
    set_response = User.UserAlarm(user_id=user_id, is_on=is_on)
    response = set_response.update_alarm()
    return jsonify({"status": response})


@app.route('/user/marketing', methods=['POST'])
@jwt_required()
@swag_from('route_yml/user/user_marketing.yml')
def user_marketing():
    user_id: int = request.args.get('user_id', 0, int)
    identity_: int = get_jwt_identity()
    if user_id != identity_:
        return jsonify(Unauthorized), 401

    is_on: int = request.args.get('is_on', 0, int)
    set_response = User.UserAlarm(user_id=user_id, is_on=is_on)
    response = set_response.update_marketing()
    return jsonify({"status": response})


# 마케팅 정보 수신 알림

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
        set_response = Admin.Notice()
        if request.method == 'GET':
            page = request.args.get('page', 1, int)
            count = request.args.get('count', 10, int)
            set_response.set_page_count(page=page, count=count)
            result, item_count = set_response.get_notice_list()
            return jsonify({"data": result, "item_count": item_count})

        elif request.method == 'POST':
            notice_id = request.args.get('notice_id', 0, int)
            data = request.get_json()
            set_response.set_notice_id(notice_id=notice_id)
            set_response.set_kwargs(**data)
            result = set_response.update_notice()
            return jsonify({"data": result})

        elif request.method == 'DELETE':
            notice_id = request.args.get('notice_id', 0, int)
            set_response.set_notice_id(notice_id=notice_id)
            set_response.delete_notice()
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
    logo_image = request.files.get('logo_image')
    # 썸네일 미지정인 경우 썸네일을 side_image로
    if not thumbnail_image:
        thumbnail_image = side_image
    # 기타 사진들
    images = request.files.getlist('ad_images')
    # 썸네일, 좌측, 후면 사진
    image_dict = {
        "side_image": side_image,
        "back_image": back_image,
        "thumbnail_image": thumbnail_image,
        "logo_image": logo_image
    }
    if images[0].filename == "":
        images = [side_image, back_image]
        allowed_ad_images = allowed_files(images)
    else:
        allowed_ad_images = allowed_files(images)

    allowed_other_images = allowed_image_for_dict(image_dict)
    if False not in allowed_ad_images and False not in allowed_other_images:
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
    recruit_time = request.args.get('recruit_time', '0001-01-01 00:00:00~9999-12-30 00:00:00')
    order_by = request.args.get('order_by', 'ad_id')
    sort = request.args.get('sort', 'DESC')
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
                                                        recruit_time=recruit_time,
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

    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    status = request.args.get('status', "", str)
    area = request.args.get('area', "", str)
    gender = request.args.get('gender', 0, int)
    age = request.args.get('age', '0~200', str)
    register_time = request.args.get('apply_time', '0001-01-01 00:00:00~9999-12-30 00:00:00')
    search = request.args.get('q', "", str)
    search_type = request.args.get('q_type', "all", str)
    advertisement = AD.AdvertisementList()
    result, item_count = advertisement.get_ad_apply_list_filter(
        page=page, count=count, status=status, area=area, gender=gender, age=age, register_time=register_time,
        search=search, search_type=search_type
    )
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
            set_result = AD.AdApplyStatusUpdate(**data)
            result, user_fcm_list = set_result.response()
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
        mission_card_id = request.args.get('mission_card_id')
        ad_apply_id = request.args.get('ad_user_apply_id')
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
    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    status = request.args.get('status', "", str)
    set_response = Mission.ReviewMissionList(page=page, count=count, status=status)
    result, item_count = set_response.response()
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

    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    area = request.args.get('area', '', str)
    gender = request.args.get('gender', 0)
    age = request.args.get('age', '0~200')
    register_time = request.args.get('register_time', '0001-01-01 00:00:00~9999-12-30 00:00:00')
    set_pages = Admin.AdminUserList()
    set_pages.set_pages(page=page, count=count)
    set_pages.set_filter(area=area, gender=gender, age=age, register_time=register_time)
    result, item_count = set_pages.response()
    return jsonify({"data": result, "item_count": item_count})


# 회원 정보에서 보유 포인트 이력
@app.route('/user/point')
@jwt_required()
@swag_from('route_yml/user/user_get_point_history.yml')
def get_point_all_by_user_id():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    user_id = request.args.get('user_id')
    result = User.get_point_all_by_user(user_id=user_id)
    return jsonify({"data": result})


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
    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    set_response = Admin.AdminWithdrawal(is_point=True)
    if request.method == 'GET':
        set_response.set_pages(count=count, page=page)
        result, item_count = set_response.response()
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

    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    set_response = Admin.AdminWithdrawal(is_point=False)
    if request.method == 'GET':
        set_response.set_pages(page=page, count=count)
        result, item_count = set_response.response()
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        data = request.get_json()
        result = Admin.update_withdrawal_donate(**data)
        return jsonify({"data": result})


def get_cash_car_tip_request_data(request):
    tip_images = request.files.getlist("tip_images")
    thumbnail_image = request.files.get('thumbnail_image')
    allowed_tips = allowed_files(tip_images)
    allowed_thumbnail = allowed_image(thumbnail_image)
    if False in allowed_tips or allowed_thumbnail is False:
        return False
    data = {
        "title": request.form.get('title'),
        "main_description": request.form.get('main_description'),
        "tip_images": tip_images,
        "thumbnail_image": thumbnail_image
    }
    return data


@app.route('/admin/cash-car-tip/register', methods=['POST'])
@jwt_required()
@swag_from('route_yml/admin/cash_car_tip_register.yml')
def cash_car_tip_register():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    data = get_cash_car_tip_request_data(request)
    if data:
        result = Tip.register(**data)
        return jsonify({"data": result})
    else:
        return jsonify({"status": "Not Allowed Image"}), 405


# 추가의 경우 이미지 파일
@app.route('/admin/cash-car-tip', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
@swag_from('route_yml/admin/cash_car_tip_list.yml', methods=['GET'])
@swag_from('route_yml/admin/cash_car_tip_post.yml', methods=['POST'])
@swag_from('route_yml/admin/cash_car_tip_delete.yml', methods=['DELETE'])
def cash_car_tip_information():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1, type=int)
    count = request.args.get('count', 10, type=int)
    if request.method == 'GET':
        result, item_count = Tip.get_cash_car_tip_all(page=page, request_user='admin', count=count)
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        tip_id = request.args.get('cash_car_tip_id', 0)
        data = get_cash_car_tip_request_data(request)
        if data:
            result = Tip.modify_cash_car_tip(cash_car_tip_id=tip_id, **data)
            return jsonify({"data": result})
        else:
            return jsonify({"data": "Not Allowed Image"}), 405

    elif request.method == 'DELETE':
        tip_id = request.args.get('cash_car_tip_id', 0)
        result = Tip.delete_cash_car_tip(cash_car_tip_id=tip_id)
        return jsonify({"data": result})


# 유저 프로필 어드민 수정
@app.route('/admin/user/profile', methods=['POST'])
@jwt_required()
def admin_user_profile_update():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    data = request.get_json()
    set_response = Admin.AdminUserList()
    set_response.set_kwargs(**data)
    result = set_response.user_profile_modify()
    return jsonify(result)


@app.route('/admin/donation/register', methods=['POST'])
@jwt_required()
def admin_donation_organization_register():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    logo_image = request.files.get('logo_image')
    donation_images = request.files.getlist('donation_images')
    allowed_logo = allowed_image(logo_image)
    allowed_donation_images = allowed_files(donation_images)

    if allowed_logo is False or False in allowed_donation_images:
        return jsonify({"status": "Not Allowed Image"}), 405
    descriptions = request.form.get('descriptions').split('&&')
    if len(donation_images) != len(descriptions):
        return jsonify({"data": "Not Allowed Data"}), 400

    data = {
        "donation_organization_name": request.form.get('organization_name'),
        "descriptions": descriptions
    }
    result = Admin.donation_organization_register(logo_image=logo_image, images=donation_images, **data)
    return jsonify({"data": result})


@app.route('/admin/app-push/list')
@jwt_required()
@swag_from('route_yml/notification/admin_app_push_list.yml')
def admin_notification_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    result, item_count = Notification.get_notification_list(page=page, count=count)
    return jsonify({"data": result, "item_count": item_count})


@app.route('/admin/app-push/re-transfer', methods=['POST'])
@jwt_required()
@swag_from('route_yml/notification/admin_app_push_re_transfer_post.yml')
def admin_notification_re_transfer():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    user_id = request.args.get('user_id')
    app_push_id = request.args.get('id')

    result = Notification.app_push_re_transfer(user_id=user_id, app_push_id=app_push_id)
    return jsonify({"data": result})


@app.route('/admin/marketing/user-list')
@jwt_required()
@swag_from('route_yml/notification/admin_marketing_user_list.yml', methods=['GET'])
def admin_marketing_user_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    page = request.args.get('page', 1, int)
    count = request.args.get('count', 10, int)
    area = request.args.get('area', '')
    gender = request.args.get('gender', 0)
    register_time_query = request.args.get('register_time', None)

    if area == '':
        area_list = area
    else:
        if len(area.split(',')) <= 1:
            area_list = area
        else:
            area_list = area.split(',')

    if register_time_query:
        register_time = register_time_query.split(',')
    else:
        register_time = ['0001-01-01 00:00:00', '9999-12-01 23:59:59']
    result, item_count = Notification.get_all_marketing_user(page=page, count=count, area=area_list,
                                                             gender=gender, register_time=register_time
                                                             )
    return jsonify({"data": result, "item_count": item_count})


# 앱푸쉬 전송 유저 리스트 (마케팅 수신동의한 사용자만)  app_push_id에 해당하는 사용자 리스트가 존재하지않는다.!
@app.route('/admin/app-push/user-list', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/notification/admin_app_push_user_list.yml', methods=['GET'])
@swag_from('route_yml/notification/admin_app_push_user_list_post.yml', methods=['POST'])
def admin_notification_user_list():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    if request.method == 'GET':
        page = request.args.get('page', 1, int)
        count = request.args.get('count', 10, int)
        app_push_id = request.args.get('id', 0, int)
        result, item_count = Notification.get_user_list_by_app_push_id(app_push_id=app_push_id, page=page, count=count)
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        data = json.loads(request.get_data())
        result = Notification.user_app_push_notification(*data['user_list'], **data)
        return jsonify({"data": result})


# 사용자 전체 포인트 관리
@app.route('/admin/point', methods=['GET', 'POST'])
@jwt_required()
@swag_from('route_yml/admin/admin_point_get.yml', methods=['GET'])
@swag_from('route_yml/admin/admin_point_post.yml', methods=['POST'])
def admin_point():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    if request.method == 'GET':
        page = request.args.get('page', 1, int)
        count = request.args.get('count', 10, int)
        filter_point = request.args.get('point', "0~999999")
        avg_point = filter_point.split('~')
        set_point = Admin.AdminPointGet(page=page, count=count, min_point=int(avg_point[0]),
                                        max_point=int(avg_point[1]))
        result, item_count = set_point.response_user_point_history()
        return jsonify({"data": result, "item_count": item_count})

    elif request.method == 'POST':
        data = json.loads(request.get_data())
        set_point = Admin.AdminPointPost(user_id=data['user_id'], point=int(data['point']), contents=data['contents'])
        result = set_point.update_user_point()
        return jsonify({"data": result})


# 포인트 일괄적용
@app.route('/admin/point/all', methods=['POST'])
@jwt_required()
@swag_from('route_yml/admin/admin_point_all.yml')
def admin_point_all():
    identity_ = get_jwt_identity()
    admin_user_id = request.headers['admin_user_id']
    # 어드민 권한 및 사용자 확인
    status, code = admin_allowed_user_check(admin_user_id=admin_user_id, identity_=identity_)
    if status is not True:
        return jsonify(status), code

    data = request.get_json()
    set_result = Admin.AdminPointAll(user_list=data['user_list'], point=data['point'], contents=data['contents'])
    result = set_result.response()
    return jsonify({"data": result})


@app.route("/admin/adverting/update/test", methods=['POST'])
@jwt_required()
def admin_ad_image_upload():
    img = request.files.get('image')
    ad_id = request.args.get('ad_id', 0)
    result = AD.adverting_image_upload(image=img, ad_id=ad_id)
    return jsonify({"data": result})


@app.route("/multipart/test", methods=['POST'])
def multipart_test_function():
    image = request.files.get('test_image')
    return jsonify({"data": secure_filename(image.filename)})
