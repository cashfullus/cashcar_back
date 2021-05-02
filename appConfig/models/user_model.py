import bcrypt
from werkzeug.utils import secure_filename

# Mysql 데이터베이스
from ..database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token, create_refresh_token

# 시간
import datetime
import re
import os

BASE_IMAGE_LOCATION = os.getcwd() + "/CashCar/appConfig/static/image/user"
PROFILE_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/user"

# 이메일 형태 정규식 사용하여 검사
def check_email_regex(email):
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    if re.search(regex, email):
        return True
    else:
        return False


# Datetime to String
def datetime_to_str(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')


# Non_User_Register
def non_user_register():
    db = Database()
    sql = "INSERT INTO user (is_non) VALUES (%s)"
    db.execute(query=sql, args=1)
    db.commit()
    result = db.executeOne(query="SELECT user_id, is_non FROM user ORDER BY register_time DESC LIMIT 1")
    return result


# 회원가입
def register(**kwargs):
    db = Database()
    result = {"status": True, "email_regex": True, "register_type": True, "data": ""}
    # Email 정규식 검사
    check_email = check_email_regex(kwargs.get("email"))
    # Email 중복확인
    user = db.getUserByEmail(kwargs.get("email"))
    print(user)
    # 확인사항 검사
    if check_email is False:
        result["email_regex"] = False
        return result

    elif user:
        result["status"] = False
        return result

    # 기본 회원가입 Query
    sql = "INSERT INTO user(email, hashed_password, login_type, alarm, marketing) VALUES (%s, %s, %s, %s, %s)"
    value_list = []
    # 카카오 회원일 경우 Query
    if kwargs.get("login_type") == "kakao":
        sql = "INSERT INTO user(email, login_type, alarm, marketing) VALUES (%s, %s, %s, %s)"
        value_list = [kwargs['email'], kwargs['login_type'], kwargs['alarm'], kwargs['marketing']]
    # 앱 기본 회원가입일 경우 password 복호화
    elif kwargs.get("login_type") == "normal":
        if kwargs.get("password") is None:
            result["status"] = False
            return result

        encrypted_password = bcrypt.hashpw(
            kwargs.get("password").encode("utf-8"),
            bcrypt.gensalt()).decode("utf-8")
        value_list = [kwargs['email'], encrypted_password, kwargs['login_type'], kwargs['alarm'], kwargs['marketing']]
    # 정해지지않은 회원가입 시도
    else:
        result["register_type"] = False
        return result

    db.execute(query=sql, args=value_list)
    db.commit()

    # JwtToken 을 업데이트 하기위해 User 정보 가져오기
    target_user = db.executeOne(query="SELECT user_id FROM user WHERE email = %s", args=kwargs.get("email"))
    # JwtToken
    jwt_token = create_access_token(identity=target_user["user_id"], expires_delta=False)
    update_user = f"UPDATE user SET jwt_token = %s WHERE user_id = {target_user['user_id']}"
    db.execute(query=update_user, args=jwt_token)
    db.execute(
        query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
        args=[target_user['user_id'], "회원가입"]
    )
    db.commit()

    result["data"] = {"user_id": target_user["user_id"], "jwt_token": jwt_token}
    return result


# 로그인
def login(**kwargs):
    db = Database()
    user = db.getLoginTypeUserByEmail(email=kwargs.get("email"), login_type=kwargs.get("login_type"))
    if user:
        # 제한된 데이터만 response
        if kwargs.get("login_type") == "kakao":
            login_user = {"user_id": user["user_id"], "jwt_token": user["jwt_token"]}
            return login_user

        elif kwargs.get("login_type") == "normal":

            encode_password = kwargs.get('password').encode('utf8')
            if bcrypt.checkpw(encode_password, user["hashed_password"].encode('utf8')):
                login_user = {"user_id": user["user_id"], "jwt_token": user["jwt_token"]}
                return login_user
            else:
                return False
        else:
            return False
    else:
        return False


# 사용자 프로필 GET
def get_user_profile(user_id):
    db = Database()
    user = db.getUserById(user_id=user_id)
    if user:
        result = {
            'user_id': user['user_id'],
            'nick_name': user['nickname'],
            'name': user['name'],
            'email': user['email'],
            'call_number': user['call_number'],
            'gender': user['resident_registration_number_back'],
            'date_of_birth': user['resident_registration_number_front'],
            'alarm': user['alarm'],
            'marketing': user['marketing'],
            'profile_image': user['profile_image']
        }
        return result

    else:
        return False


def update_user_profile(user_id, profile_image=None, **kwargs):
    db = Database()
    user = db.getUserById(user_id=int(user_id))
    if user:
        if profile_image:
            directory = f"{BASE_IMAGE_LOCATION}/{user_id}"
            os.makedirs(directory, exist_ok=True)
            profile_image.save(directory + "/" + secure_filename(profile_image.filename))
            save_image = f"{PROFILE_IMAGE_HOST}/{user_id}/{secure_filename(profile_image.filename)}"
            print(save_image)
            sql = "UPDATE user SET " \
                  "nickname = %s, email = %s, name = %s, " \
                  "call_number = %s, " \
                  "resident_registration_number_back = %s, " \
                  "resident_registration_number_front = %s, " \
                  "alarm = %s, " \
                  "marketing = %s, profile_image = %s WHERE user_id = %s"
            value_list = [kwargs['nickname'], kwargs['email'], kwargs['name'],
                          kwargs['call_number'], kwargs['gender'], kwargs['date_of_birth'],
                          kwargs['alarm'], kwargs['marketing'], save_image, user_id
                          ]
            print(value_list)
            db.execute(query=sql, args=value_list)
            db.commit()
            return save_image
        else:
            sql = "UPDATE user SET " \
                  "nickname = %s, email = %s, name = %s, " \
                  "call_number = %s, " \
                  "resident_registration_number_back = %s, " \
                  "resident_registration_number_front = %s, " \
                  "alarm = %s, " \
                  "marketing = %s WHERE user_id = %s"
            value_list = [kwargs['nickname'], kwargs['email'], kwargs['name'],
                          kwargs['call_number'], kwargs['gender'], kwargs['date_of_birth'],
                          kwargs['alarm'], kwargs['marketing'], int(user_id)
                          ]
            db.execute(query=sql, args=value_list)
            db.commit()
            return True
    else:
        return False


# 사용자 배송지 설정
def user_address_update(user_id, **kwargs):
    db = Database()
    status = {"is_update": True}
    user = db.getUserById(user_id=user_id)
    if user:
        db.execute(
            query="UPDATE user SET "
                  "name = %s, call_number = %s, main_address = %s, detail_address = %s WHERE user_id = %s",
            args=[kwargs['name'], kwargs['call_number'], kwargs['main_address'], kwargs['detail_address'], user_id]
        )
        db.commit()
        return status
    else:
        status["is_update"] = False
        return status


# 사용자 배송지 설정에서 Method == GET
def get_user_address(user_id):
    db = Database()
    status = {"is_user": True, "data": {}}
    user = db.executeOne(
        query="SELECT name, call_number, main_address, detail_address FROM user WHERE user_id = %s",
        args=user_id
    )
    if user:
        status['data'] = user
        return status
    else:
        status['is_user'] = False
        return status


# Fcm 토큰 저장
def user_fcm(**kwargs):
    db = Database()
    user = db.getUserById(user_id=kwargs.get("user_id"))
    if user:
        fcm_row = db.executeOne(query="SELECT * FROM user_fcm WHERE user_id = %s", args=kwargs.get("user_id"))
        if fcm_row:
            db.execute(query="UPDATE user_fcm SET fcm_token = %s, "
                             "last_check_time = NOW() WHERE fcm_id = %s",
                       args=[kwargs.get('fcm_token'), fcm_row["fcm_id"]]
                       )
            db.commit()
            return True
        else:
            db.execute(query="INSERT INTO user_fcm (user_id, fcm_token) VALUES (%s, %s)",
                       args=[kwargs.get("user_id"), kwargs.get("fcm_token")]
                       )
            db.commit()
            return True
    else:
        return False


# 진행해야할 미션 리스트
def user_mission_list(user_id):
    db = Database()
    result = {"mission_information": [], "images": [], "ad_user_information": {}}
    mission_information = db.getAllMyMissionByUserId(user_id=user_id)
    if mission_information:
        images = db.executeAll(
            query="SELECT image FROM ad_images "
                  "JOIN ad_user_apply aua on ad_images.ad_id = aua.ad_id WHERE aua.user_id = %s",
            args=user_id
        )
        ad_user_information = db.executeOne(
            query="SELECT total_point, title, thumbnail_image, "
                  "DATE_FORMAT(activity_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_start_date, "
                  "DATE_FORMAT(activity_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_end_date "
                  "FROM ad_user_apply as aua "
                  "JOIN ad_information ai on aua.ad_id = ai.ad_id "
                  "WHERE user_id = %s",
            args=user_id
        )
        result["mission_information"] = mission_information
        result['ad_user_information'] = ad_user_information
        result["images"] = images

    return result


# 광고ID에 신청한 사람 조회
def user_apply_id_by_ad_id(page, ad_id):
    per_page = (page - 1) * 10
    start_at = per_page + 10
    db = Database()
    user_information = db.executeAll(
        query="SELECT "
              "u. user_id, nickname, name, call_number, email, "
              "cast('resident_registration_number_back' as unsigned) as gender, "
              "resident_registration_number_front as birth_of_date, "
              "car_number, vehicle_model_name, "
              "DATE_FORMAT(accept_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as accept_status_time "
              "FROM ad_user_apply as aua "
              "JOIN user u on aua.user_id = u.user_id "
              "JOIN vehicle v on u.user_id = v.user_id "
              "WHERE aua.ad_id = %s AND v.supporters = 1 AND removed = 0 "
              "ORDER BY ad_user_apply_id LIMIT %s OFFSET %s",
        args=[ad_id, start_at, per_page]
    )
    return user_information


# 사용자 포인트 기록 조회
def get_point_all_by_user(user_id, page):
    per_page = (int(page) - 1) * 7
    start_at = per_page + 7
    db = Database()
    user_point_history = db.executeAll(
        query="SELECT point, contents, type, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM point_history WHERE user_id = %s LIMIT %s OFFSET %s",
        args=[user_id, start_at, per_page]
    )
    return user_point_history


#fcm token 가져오기
def get_fcm_token_by_user_id(user_id):
    db = Database()
    user_fcm_token = db.executeOne(
        query="SELECT fcm_token FROM user_fcm WHERE user_id = %s",
        args=user_id
    )
    return user_fcm_token


# 사용자 포인트 창
def get_user_point_history(user_id):
    db = Database()
    point = db.executeOne(
        query="SELECT deposit FROM user WHERE user_id = %s",
        args=user_id
    )
    point_history = db.executeAll(
        query="SELECT point, contents, register_time FROM point_history WHERE user_id = %s",
        args=user_id
    )
    scheduled_point = db.executeAll(

    )

# 사용자 출금신청시 GET
# def get_user_withdrawal_data(user_id):



