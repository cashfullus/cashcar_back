import string

import bcrypt
import pymysql
from werkzeug.utils import secure_filename

# Mysql 데이터베이스
from database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token, create_refresh_token
from notification.user_push_nofitication import one_cloud_messaging
# 시간
from datetime import datetime, date, timedelta
import re
import os
# 난수발생 비밀번호 찾기
import random
import math

BASE_IMAGE_LOCATION = os.getcwd() + "/static/image/user"
PROFILE_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/user"


# 이메일 형태 정규식 사용하여 검사
def check_email_regex(email):
    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
    if re.search(regex, email):
        return True
    else:
        return False


# 이메일 인증용 난수 발생기
def email_auth_num():
    LENGTH = 10
    string_pool = string.ascii_letters + string.digits
    auth_num = ""
    for i in range(LENGTH):
        auth_num += random.choice(string_pool)
    return auth_num


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
    db.db_close()
    return result


# 회원가입
def register(**kwargs):
    db = Database()
    result = {"status": True, "email_regex": True, "register_type": True, "data": "", "default": True}
    if 'email' not in kwargs.keys():
        result['default'] = False
        db.db_close()
        return result

    # Email 정규식 검사
    check_email = check_email_regex(kwargs.get("email"))
    # Email 중복확인
    user = db.getUserByEmail(kwargs.get("email"))
    # 확인사항 검사
    if check_email is False:
        result["email_regex"] = False
        db.db_close()
        return result

    elif user:
        result["status"] = False
        db.db_close()
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
            db.db_close()
            return result

        encrypted_password = bcrypt.hashpw(
            kwargs.get("password").encode("utf-8"),
            bcrypt.gensalt()).decode("utf-8")
        value_list = [kwargs['email'], encrypted_password, kwargs['login_type'], kwargs['alarm'], kwargs['marketing']]
    # 정해지지않은 회원가입 시도
    else:
        result["register_type"] = False
        db.db_close()
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
    db.execute(
        query="INSERT INTO user_fcm (user_id, fcm_token) "
              "VALUES (%s, %s)",
        args=[target_user['user_id'], kwargs['fcm_token']]
    )
    db.commit()

    result["data"] = {"user_id": target_user["user_id"], "jwt_token": jwt_token}
    db.db_close()
    return result


# 카카오 로그인
# def kakao_login(**kwargs):
#     db = Database()
#     user = db.getLoginTypeUserByEmail(email=kwargs.get('email'), login_type='kakao')
#     if user:
#         login_user = {"user_id": user["user_id"], "jwt_token": user["jwt_token"]}
#         return login_user
#     else:
#         sql = "INSERT INTO user(email, login_type, alarm, marketing) VALUES (%s, %s, %s, %s)"
#         value_list = [kwargs['email'], kwargs['login_type'], kwargs['alarm'], kwargs['marketing']]
#         db.execute(query=sql, args=value_list)
#         jwt_token = create_access_token(identity=target_user["user_id"], expires_delta=False)


# 로그인
def login(**kwargs):
    db = Database()
    user = db.getLoginTypeUserByEmail(email=kwargs.get("email"), login_type=kwargs.get("login_type"))
    if user:
        db.execute(
            query="UPDATE user SET last_connection_time = NOW() WHERE email = %s",
            args=kwargs.get('email')
        )
        if 'fcm_token' in kwargs.keys():
            db.execute(
                query="UPDATE user_fcm SET fcm_token = %s WHERE user_id = %s",
                args=[kwargs['fcm_token'], user['user_id']]
            )
        db.commit()
        # 제한된 데이터만 response
        if kwargs.get("login_type") == "kakao":
            login_user = {"user_id": user["user_id"], "jwt_token": user["jwt_token"]}
            db.db_close()
            return login_user

        elif kwargs.get("login_type") == "normal":

            encode_password = kwargs.get('password').encode('utf8')
            if bcrypt.checkpw(encode_password, user["hashed_password"].encode('utf8')):
                login_user = {"user_id": user["user_id"], "jwt_token": user["jwt_token"]}
                db.db_close()
                return login_user
            else:
                db.db_close()
                return False
        else:
            db.db_close()
            return False
    else:
        db.db_close()
        return False


class UserProfile:
    def __init__(self, user_id):
        self.user = None
        self.user_id = user_id
        self.db = Database()

    def set_response(self):
        user = self.get_user_information()
        if user:
            return user
        else:
            return False

    def set_user_data(self):
        if self.user is None:
            return False
        else:
            response = {
                'user_id': self.user['user_id'],
                'nick_name': self.user['nickname'],
                'name': self.user['name'],
                'email': self.user['email'],
                'call_number': self.user['call_number'],
                'gender': self.user['resident_registration_number_back'],
                'date_of_birth': self.user['resident_registration_number_front'],
                'alarm': self.user['alarm'],
                'marketing': self.user['marketing'],
                'profile_image': self.user['profile_image']
            }
            return response

    def get_user_information(self):
        return self.db.getUserById(user_id=self.user_id)

    def response(self):
        response_data = self.set_response()
        if response_data:
            self.user = response_data

        response = self.set_user_data()
        self.db.db_close()
        return response


def update_user_profile(user_id, profile_image=None, **kwargs):
    db = Database()
    user = db.getUserById(user_id=int(user_id))
    if user:
        if profile_image:
            directory = f"{BASE_IMAGE_LOCATION}/{user_id}"
            os.makedirs(directory, exist_ok=True)
            profile_image.save(directory + "/" + secure_filename(profile_image.filename))
            save_image = f"{PROFILE_IMAGE_HOST}/{user_id}/{secure_filename(profile_image.filename)}"
            if kwargs.get('nickname') == "":
                kwargs['nickname'] = kwargs['name']
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
            if kwargs.get('nickname') == "":
                kwargs['nickname'] = kwargs['name']
            value_list = [kwargs['nickname'], kwargs['email'], kwargs['name'],
                          kwargs['call_number'], kwargs['gender'], kwargs['date_of_birth'],
                          kwargs['alarm'], kwargs['marketing'], int(user_id)
                          ]
            db.execute(query=sql, args=value_list)
            db.commit()
            db.db_close()
            return True
    else:
        db.db_close()
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
            query="SELECT total_point, title, thumbnail_image, activity_period, day_point,"
                  "DATE_FORMAT(activity_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_start_date, "
                  "DATE_FORMAT(activity_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_end_date "
                  "FROM ad_user_apply as aua "
                  "JOIN ad_information ai on aua.ad_id = ai.ad_id "
                  "WHERE user_id = %s AND status NOT IN ('success', 'fail', 'reject', 'cancel')",
            args=user_id
        )
        additional_point = db.executeOne(
            query="SELECT SUM(additional_point) as sum_point FROM ad_mission_card amc "
                  "JOIN ad_mission_card_user amcu on amc.ad_mission_card_id = amcu.ad_mission_card_id "
                  "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
                  "WHERE user_id = %s "
                  "AND amcu.status = 'success' AND amcu.mission_type = 1 AND aua.status = 'accept'",
            args=user_id
        )['sum_point']
        day_diff = 0
        if ad_user_information['activity_start_date'] == '0000-00-00 00:00:00':
            ad_user_information['day_diff'] = 0
            ad_user_information['activity_start_date'] = ""
            ad_user_information['activity_end_date'] = ""
            ad_user_information['cumulative_point'] = 0
        else:
            start_date = datetime.strptime(ad_user_information['activity_start_date'], '%Y-%m-%d %H:%M:%S').date()
            time_diff = ((date.today() + timedelta(days=1)) - start_date).days
            day_diff = ((time_diff / ad_user_information['activity_period']) * 100)
            if day_diff >= 100:
                day_diff = 100
            ad_user_information['cumulative_point'] = int(time_diff * ad_user_information['day_point'])
            ad_user_information['day_diff'] = time_diff

        if additional_point:
            ad_user_information['cumulative_point'] += additional_point
        result["mission_information"] = mission_information
        result['ad_user_information'] = ad_user_information
        result["images"] = images
        result['day_diffs'] = int(day_diff)
    db.db_close()
    return result


# 광고ID에 신청한 사람 조회
def user_apply_id_by_ad_id(page, count, ad_id):
    per_page = (page - 1) * 10
    db = Database()
    user_information = db.executeAll(
        query="SELECT "
              "u.user_id, nickname, name, call_number, email, "
              "cast('resident_registration_number_back' as unsigned) as gender, "
              "resident_registration_number_front as birth_of_date, "
              "car_number, vehicle_model_name, brand,recruit_number, max_recruiting_count,"
              "DATE_FORMAT(accept_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as accept_status_time "
              "FROM ad_user_apply as aua "
              "JOIN user u on aua.user_id = u.user_id "
              "JOIN vehicle v on u.user_id = v.user_id "
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "WHERE aua.ad_id = %s AND v.supporters = 1 AND v.removed = 0 "
              "ORDER BY ad_user_apply_id LIMIT %s OFFSET %s",
        args=[ad_id, count, per_page]
    )
    item_count = db.executeOne(
        query="SELECT count(u.user_id) as item_count FROM ad_user_apply aua "
              "JOIN user u on aua.user_id = u.user_id "
              "JOIN vehicle v on u.user_id = v.user_id "
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "WHERE aua.ad_id = %s AND v.supporters = 1 AND v.removed = 0",
        args=ad_id
    )
    return user_information, item_count['item_count']


# 사용자 포인트 기록 조회
def get_point_all_by_user(user_id):
    db = Database()
    user_point_history = db.executeAll(
        query="SELECT point, contents, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM point_history WHERE user_id = %s ORDER BY register_time DESC",
        args=user_id
    )
    db.db_close()
    return user_point_history


# fcm token 가져오기
def get_fcm_token_by_user_id(user_id):
    db = Database()
    user_fcm_token = db.executeOne(
        query="SELECT fcm_token FROM user_fcm WHERE user_id = %s",
        args=user_id
    )
    db.db_close()
    return user_fcm_token


# 사용자 출금신청 데이터 GET
def get_user_withdrawal_data(user_id):
    db = Database()
    user_information = db.executeOne(
        query="SELECT user_id, name, deposit, account_bank, account_number FROM user WHERE user_id = %s",
        args=user_id
    )
    user_information['status'] = True
    user_information['ongoing'] = ""
    already_ongoing_withdrawal = db.executeOne(
        query="SELECT withdrawal_self_id, status FROM withdrawal_self "
              "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )
    if already_ongoing_withdrawal:
        user_information['status'] = False
        user_information['ongoing'] = already_ongoing_withdrawal['status']
    db.db_close()
    return user_information


# 사용자 기부 데이터 GET
def get_user_withdrawal_donate_data(user_id, donation_id):
    db = Database()
    user_information = db.executeOne(
        query="SELECT user_id, name, deposit FROM user WHERE user_id = %s",
        args=user_id
    )
    donation_information = db.executeOne(
        query="SELECT donation_organization_id, donation_organization_name FROM donation_organization "
              "WHERE donation_organization_id = %s",
        args=donation_id
    )
    user_information['donation_organization_id'] = donation_information['donation_organization_id']
    user_information['donation_organization_name'] = donation_information['donation_organization_name']
    user_information['status'] = True
    user_information['ongoing'] = ""
    already_ongoing_withdrawal = db.executeOne(
        query="SELECT withdrawal_donate_id, status FROM withdrawal_donate "
              "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )
    if already_ongoing_withdrawal:
        user_information['status'] = False
        user_information['ongoing'] = already_ongoing_withdrawal['status']
    db.db_close()
    return user_information


# 사용자 출금신청    withdrawal_point(음수), bank_name, bank_owner, bank_number, is_main
# status stand_by(대기), confirm(진행중), done(완료), cancel(취소)
def update_user_withdrawal_data(user_id, **kwargs):
    db = Database()
    status = {"deposit": True, "ongoing": True}
    user_deposit = db.getUserById(user_id=user_id)

    if user_deposit['deposit'] < int(kwargs['withdrawal_point']) or kwargs['withdrawal_point'] <= 9999:
        status["deposit"] = False
        db.db_close()
        return status

    already_ongoing_withdrawal = db.executeOne(
        query="SELECT withdrawal_self_id FROM withdrawal_self WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )

    if already_ongoing_withdrawal:
        status["ongoing"] = False
        db.db_close()
        return status

    db.execute(
        query="INSERT INTO withdrawal_self (user_id, amount, account_bank, account_name, account_number) "
              "VALUES (%s, %s, %s, %s, %s)",
        args=[user_id, -int(kwargs['withdrawal_point']), kwargs['account_bank'],
              kwargs['name'], kwargs['account_number']]
    )
    # commit 은 데이터 완전 저장 이기떄문에 안전하게 셀렉후 바로 저장
    db.execute(
        query="INSERT INTO point_history (user_id, point, contents) "
              "VALUES (%s, %s, %s)",
        args=[user_id, -int(kwargs['withdrawal_point']), "통장으로 출금"]
    )
    if int(kwargs['is_main']) == 1:
        db.execute(
            query="UPDATE user "
                  "SET account_bank = %s, account_name = %s, account_number = %s, deposit = deposit - %s "
                  "WHERE user_id = %s",
            args=[kwargs['account_bank'], kwargs['name'],
                  kwargs['account_number'], int(kwargs['withdrawal_point']), user_id]
        )
    else:
        db.execute(
            query="UPDATE user "
                  "SET deposit = deposit - %s "
                  "WHERE user_id = %s",
            args=[int(kwargs['withdrawal_point']), user_id]
        )
    fcm_token = db.executeOne(query="SELECT fcm_token, alarm FROM user_fcm uf JOIN user u on uf.user_id = u.user_id "
                                    "WHERE u.user_id = %s AND alarm = 1",
                              args=user_id)
    if fcm_token:
        one_cloud_messaging(token=fcm_token['fcm_token'],
                            body="[출금] 신청이 등록되었습니다. 영업일 기준 2-3일 정도 후에 통장으로 입금될 예정입니다.")
    db.commit()
    db.db_close()
    return status


# 사용자 기부 신청
def update_user_withdrawal_donate(user_id, donation_id, **kwargs):
    db = Database()
    status = {"deposit": True, "ongoing": True}
    user_deposit = db.getUserById(user_id=user_id)

    if user_deposit['deposit'] < int(kwargs['withdrawal_point']) or kwargs['withdrawal_point'] <= 9999:
        status["deposit"] = False
        db.db_close()
        return status

    already_ongoing_withdrawal = db.executeOne(
        query="SELECT withdrawal_donate_id FROM withdrawal_donate "
              "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )

    if already_ongoing_withdrawal:
        status["ongoing"] = False
        db.db_close()
        return status

    donation_information = db.getOneDonationById(donation_organization_id=donation_id)

    db.execute(
        query="INSERT INTO withdrawal_donate (user_id, amount, receipt, donation_organization_id, name_of_donor) VALUE "
              "(%s, %s, %s, %s, %s)",
        args=[user_id, -int(kwargs['withdrawal_point']), kwargs['is_receipt'], donation_id,
              kwargs['name_of_donor']]
    )
    history_content_name = f"{donation_information['donation_organization_name']} 기부"
    db.execute(
        query="INSERT INTO point_history (user_id, point, contents) "
              "VALUES (%s, %s, %s)",
        args=[user_id, -int(kwargs['withdrawal_point']), history_content_name]
    )
    db.execute(
        query="UPDATE user SET deposit = deposit - %s WHERE user_id = %s",
        args=[int(kwargs['withdrawal_point']), user_id]
    )
    fcm_token = db.executeOne(query="SELECT fcm_token, alarm FROM user_fcm uf JOIN user u on uf.user_id = u.user_id "
                                    "WHERE u.user_id = %s AND alarm = 1",
                              args=user_id)
    if fcm_token:
        one_cloud_messaging(token=fcm_token['fcm_token'],
                            body="[기부]에 함께 동참해주셔서 감사합니다. 영수증의 경우, 영업일 기준 2-3일 내에 기부 단체에서 별도의 연락을 드립니다.")
    db.commit()
    db.db_close()
    return status


# 토스트메시지 읽음 처리
def update_reason_by_user(reason_id):
    db = Database()
    db.execute(
        query="UPDATE ad_mission_reason SET is_read = 1 WHERE ad_mission_reason_id = %s",
        args=reason_id
    )
    db.commit()
    db.db_close()
    return


# 사용자 마이페이지
def get_user_my_page(user_id):
    db = Database()
    user_information = db.executeOne(
        query="SELECT user_id, profile_image, nickname, name, email, deposit, login_type FROM user WHERE user_id = %s",
        args=user_id
    )
    db.db_close()
    return {"user_information": user_information}


# 사용자 벳지 리스트
def get_all_my_badge_list(user_id):
    db = Database()
    badge_information = db.executeAll(
        query="SELECT status, title FROM ad_user_apply aua "
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "WHERE user_id = %s AND status IN ('success', 'fail') ORDER BY ad_user_apply_id",
        args=user_id
    )
    db.db_close()
    return badge_information


# negative positive, donate
def user_point_history_query(user_id, q, per_page, count):
    if q == "":
        sql = "SELECT " \
              "point, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "contents " \
              f"FROM point_history WHERE user_id = {user_id} " \
              f"ORDER BY register_time DESC LIMIT {count} OFFSET {per_page}"
        return sql
    elif q == "negative":
        sql = "SELECT " \
              "point, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "contents " \
              f"FROM point_history WHERE user_id = {user_id} AND SIGN(point) = -1 " \
              f"ORDER BY register_time DESC LIMIT {count} OFFSET {per_page}"
        return sql

    elif q == "positive":
        sql = "SELECT " \
              "point, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "contents " \
              f"FROM point_history WHERE user_id = {user_id} AND (SIGN(point) = 0 OR SIGN(point) = 1) " \
              f"ORDER BY register_time DESC LIMIT {count} OFFSET {per_page}"
        return sql
    elif q == "donate":
        sql = "SELECT " \
              "point, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "contents " \
              f"FROM point_history WHERE user_id = {user_id} AND contents LIKE '%%기부%%' " \
              f"ORDER BY register_time DESC LIMIT {count} OFFSET {per_page}"
        return sql


# 사용자 포인트 와 적립예정 포인트 및 포인트 이력
def get_user_point_and_history(user_id, page, count, q):
    db = Database()
    per_page = (page - 1) * count
    point_query = user_point_history_query(user_id=user_id, q=q, per_page=per_page, count=count)
    user_scheduled_point = 0
    user_point = db.executeOne(
        query="SELECT deposit FROM user WHERE user_id = %s",
        args=user_id
    )
    scheduled_point = db.executeOne(
        query="SELECT "
              "SUM(amc.additional_point) as scheduled_point, aua.ad_user_apply_id "
              "FROM ad_mission_card_user amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "WHERE aua.user_id = %s "
              "AND aua.status ='accept' "
              "AND amcu.status = 'success' "
              "AND amc.mission_type = 1 "
              "GROUP BY aua.ad_user_apply_id",
        args=user_id
    )
    ad_point = db.executeOne(
        query="SELECT total_point FROM ad_information ai "
              "JOIN ad_user_apply aua on ai.ad_id = aua.ad_id "
              "WHERE aua.user_id = %s AND aua.status IN ('stand_by', 'accept')",
        args=user_id
    )
    withdrawal_point = db.executeOne(
        query="SELECT status FROM withdrawal_self "
              "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )
    withdrawal_donate = db.executeOne(
        query="SELECT status FROM withdrawal_donate "
              "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
        args=user_id
    )
    user_point_history = db.executeAll(
        query=point_query
    )
    point_history_page_count = db.executeOne(
        query="SELECT count(user_id) as item_count FROM point_history WHERE user_id = %s",
        args=user_id
    )
    page_count = point_history_page_count['item_count'] / count
    if page_count > point_history_page_count['item_count'] // count:
        page_count += 1

    if scheduled_point:
        user_scheduled_point += int(scheduled_point['scheduled_point'])

    if ad_point:
        user_scheduled_point += ad_point['total_point']

    # False 진행중X True 일시 이미 진행중인 데이터 존재
    ongoing_point = ""
    ongoing_donate = ""
    if withdrawal_point:
        ongoing_point = withdrawal_point['status']

    if withdrawal_donate:
        ongoing_donate = withdrawal_donate['status']

    result = {"user_point": user_point['deposit'],
              "scheduled_point": user_scheduled_point,
              "point_history": user_point_history,
              "is_ongoing_point": ongoing_point,
              "is_ongoing_donate": ongoing_donate,
              "page_count": int(page_count)}
    db.db_close()
    return result


# 사용자 알람 히스토리
def saveAlarmHistory(user_id, alarm_type, required, description):
    db = Database()
    db.execute(
        query="INSERT INTO alarm_history (user_id, alarm_type, required, description) VALUE (%s, %s, %s, %s)",
        args=[user_id, alarm_type, required, description]
    )
    db.commit()


def get_user_alarm_history(user_id, page):
    db = Database()
    per_page = (int(page) - 1) * 10
    start_at = per_page + 10
    result = db.executeAll(
        query="SELECT user_id, alarm_type, required, description, is_read_alarm "
              "FROM alarm_history WHERE user_id = %s ORDER BY register_time DESC LIMIT %s OFFSET %s",
        args=[user_id, start_at, per_page]
    )
    db.execute(
        query="UPDATE alarm_history SET is_read_alarm = 1 WHERE user_id = %s AND is_read_alarm = 0",
        args=user_id
    )
    db.commit()
    db.db_close()
    return result


def getAllFaQ():
    db = Database()
    result = db.executeAll(
        query="SELECT title, description FROM faq"
    )
    db.db_close()
    return result


# 사용자 password 변경
def login_user_change_password(user_id, **kwargs):
    db = Database()
    status = {"new_password_check": True, "old_password_check": True}
    new_password_first = kwargs['new_password_1']
    new_password_second = kwargs['new_password_2']

    if new_password_first != new_password_second:
        status["new_password_check"] = False
        db.db_close()
        return status

    user = db.getUserById(user_id=user_id)

    if kwargs['login_type'] == "normal":
        encode_password = kwargs.get('old_password').encode('utf8')
        if bcrypt.checkpw(encode_password, user["hashed_password"].encode('utf8')):
            encrypted_password = bcrypt.hashpw(
                kwargs.get("new_password_1").encode("utf-8"),
                bcrypt.gensalt()).decode("utf-8")
            db.execute(
                query="UPDATE user SET hashed_password = %s WHERE user_id = %s",
                args=[encrypted_password, user_id]
            )
            db.commit()
            db.db_close()
            return status
        else:
            status['old_password_check'] = False
            db.db_close()
            return status

    else:
        status["new_password_check"] = False
        status["old_password_check"] = False
        db.db_close()
        return status


def user_email_check_for_password(**kwargs):
    db = Database()
    user = db.getAuthEmailByEmail(email=kwargs.get('email'))
    if user:
        auth_number = email_auth_num()
        authenticated = db.executeOne(
            query="SELECT * FROM user_find_password WHERE user_id = %s",
            args=user['user_id']
        )
        if authenticated:
            db.execute(
                query="UPDATE user_find_password SET authentication_number = %s, last_change_time = NOW() "
                      "WHERE user_id = %s",
                args=[auth_number, user['user_id']]
            )
        else:
            db.execute(
                query="INSERT INTO user_find_password (user_id, authentication_number) "
                      "VALUES (%s, %s)",
                args=[user['user_id'], auth_number]
            )
        db.commit()
        db.db_close()
        return True, auth_number
    else:
        db.db_close()
        return False, ""


def user_email_auth_number_check(**kwargs):
    db = Database()
    status = {"authentication": True, "user_information": True}
    user = db.getAuthEmailByEmail(email=kwargs.get('email'))
    if user:
        check_auth = db.executeOne(
            query="SELECT * FROM user_find_password WHERE user_id = %s",
            args=user['user_id']
        )
        if check_auth['authentication_number'] == kwargs.get('authentication_number'):
            db.db_close()
            return status
        else:
            status["authentication"] = False
            db.db_close()
            return status
    else:
        status["user_information"] = False
        db.db_close()
        return status


# 기부 리스트 페이지
class UserDonationList:
    def __init__(self, user_id, count, page):
        self.user_id = user_id
        self.per_page = (page - 1) * count
        self.count = count
        self.db = Database()

    def get_ongoing_donation_status(self):
        status = self.db.getOneUserDonateStatus(user_id=self.user_id)
        if status:
            return status['status']
        else:
            return ""

    def get_image_data(self):
        response_data = self.get_response_data()
        for i in range(len(response_data)):
            image_data = self.db.executeAll(
                query="SELECT image, description FROM donation_organization_images WHERE donation_organization_id = %s",
                args=response_data[i]['donation_organization_id']
            )
            response_data[i]['image_information'] = image_data
        return response_data

    def get_response_data(self):
        return self.db.executeAll(
            query="SELECT donation_organization_id, donation_organization_name, logo_image, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM donation_organization ORDER BY register_time DESC "
                  "LIMIT %s OFFSET %s",
            args=[self.count, self.per_page]
        )

    def response(self):
        response_data = self.get_image_data()
        donation_status = self.get_ongoing_donation_status()
        self.db.db_close()
        return response_data, donation_status


# 기부 디테일 페이지
class UserDonationDetail:
    def __init__(self, donation_id):
        self.donation_id = donation_id
        self.db = Database()

    def get_response_data(self):
        return self.db.executeOne(
            query="SELECT donation_organization_id, donation_organization_name, logo_image, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM donation_organization WHERE donation_organization_id = %s",
            args=self.donation_id
        )

    def get_image_data(self):
        return self.db.executeAll(
            query="SELECT image, description FROM donation_organization_images WHERE donation_organization_id = %s",
            args=self.donation_id
        )

    def response(self):
        response_data = self.get_response_data()
        response_data['image_information'] = self.get_image_data()
        self.db.db_close()
        return response_data


class UserAlarm:
    def __init__(self, user_id, is_on):
        self.user_id = user_id
        self.is_on = is_on
        self.db = Database()

    def update_alarm(self):
        self.db.execute(
            query="UPDATE user SET alarm = %s WHERE user_id = %s",
            args=[self.is_on, self.user_id]
        )
        self.db.commit()
        self.db.db_close()
        return True

    def update_marketing(self):
        self.db.execute(
            query="UPDATE user SET marketing = %s WHERE user_id = %s",
            args=[self.is_on, self.user_id]
        )
        self.db.commit()
        self.db.db_close()
        return True
