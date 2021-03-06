import bcrypt

# Mysql 데이터베이스
from database.dbConnection import Database
# JwtToken
from flask_jwt_extended import create_access_token

# 시간
from datetime import datetime, date, timedelta
import os
from notification.user_push_nofitication import one_cloud_messaging, multiple_cloud_messaging
from .filter_model import Filter

from werkzeug.utils import secure_filename

CASH_CAR_TIP_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/cash_car_tip"
DONATION_ORGANIZATION_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/donation"
BASE_IMAGE_LOCATION_DONATION = os.getcwd() + "/static/image/donation"


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def allowed_in_role_user(user_id):
    db = Database()
    user_role = db.executeOne(
        query="SELECT role FROM admin_user WHERE admin_user_id = %s AND role IN ('staff', 'superuser')",
        args=user_id
    )
    if user_role:
        return True
    else:
        return False


def check_area_filter(area):
    where_area = []
    if type(area) == str:
        if area == "":
            where_area = "area LIKE '%%'"
        else:
            where_area = f"area LIKE '%%{area}%%'"
    else:
        for i in range(len(area)):
            if i + 1 != len(area):
                where_area.append(f"area LIKE '%%{area[i]}%%' OR ")
            else:
                where_area.append(f"area LIKE '%%{area[i]}%%'")
        where_area = "({0})".format(''.join(where_area))
    return where_area


# 사용자 공지사항 리스트
def user_get_notice_list():
    db = Database()
    result = db.getUserAllNotice()
    return result


# 어드민 공지사항 등록
def admin_register_notice(**kwargs):
    db = Database()
    db.execute(
        query="INSERT INTO notice_information (title, description) VALUES (%s, %s)",
        args=[kwargs['title'], kwargs['description']]
    )
    result = db.executeOne(
        query="SELECT notice_id, title, description, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM notice_information ORDER BY register_time DESC LIMIT 1"
    )
    db.commit()
    return result


# router /admin/notice
class Notice:
    def __init__(self):
        self.page = None
        self.count = None
        self.per_page = None
        self.kwargs = None
        self.notice_id = None
        self.db = Database()

    def set_page_count(self, page, count):
        self.page = page
        self.count = count
        self.per_page = (page - 1) * count

    def set_notice_id(self, notice_id):
        self.notice_id = notice_id

    def set_kwargs(self, **kwargs):
        self.kwargs = kwargs

    def get_item_count(self):
        return self.db.executeOne(
            query="SELECT count(notice_id) as item_count FROM notice_information "
                  "WHERE is_removed = 0 ORDER BY register_time DESC"
        )

    def get_admin_all_notice(self):
        return self.db.getAdminAllNotice(count=self.count, per_page=self.per_page), self.get_item_count()

    # 어드민 공지사항 리스트
    def get_notice_list(self):
        response, item_count = self.get_admin_all_notice()
        self.db.db_close()
        return response, item_count

    # 어드민 공지사항 업데이트
    def update_notice(self):
        self.db.updateNotice(notice_id=self.notice_id, title=self.kwargs.get('title'),
                             description=self.kwargs.get('description')
                             )
        self.kwargs['notice_id'] = self.notice_id
        self.db.db_close()
        return self.kwargs

    def delete_notice(self):
        self.db.deleteNotice(notice_id=self.notice_id)
        self.db.db_close()


def register(**kwargs):
    db = Database()
    result = {"exist_id": True, "data": {}}
    exist_user = db.executeOne(
        query="SELECT admin_user_id FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    if exist_user:
        result["exist_id"] = False
        return result

    sql = "INSERT INTO admin_user (login_id, hashed_password) VALUES (%s, %s)"
    encrypted_password = bcrypt.hashpw(kwargs.get("password").encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    value_list = [kwargs['login_id'], encrypted_password]
    db.execute(query=sql, args=value_list)
    db.commit()

    # JwtToken 을 업데이트 하기위해 User 정보 가져오기
    target_user = db.executeOne(query="SELECT admin_user_id FROM admin_user WHERE login_id = %s",
                                args=kwargs['login_id'])
    # JwtToken
    jwt_token = create_access_token(identity=target_user["admin_user_id"], expires_delta=False)
    update_user = "UPDATE admin_user SET jwt_token = %s WHERE admin_user_id = %s"
    db.execute(query=update_user, args=[jwt_token, target_user["admin_user_id"]])
    db.commit()
    result["data"] = db.executeOne(
        query="SELECT admin_user_id, jwt_token, role FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    return result


# 로그인
def login(**kwargs):
    db = Database()
    status = {"login_id": True, "password": True, "data": {}}
    admin_user = db.executeOne(
        query="SELECT admin_user_id, hashed_password, jwt_token, role FROM admin_user WHERE login_id = %s",
        args=kwargs['login_id']
    )
    if not admin_user:
        status["login_id"] = False
        return status

    encode_password = kwargs['password'].encode('utf8')
    if bcrypt.checkpw(encode_password, admin_user['hashed_password'].encode('utf8')):
        status["data"] = {"user_id": admin_user["admin_user_id"], "jwt_token": admin_user["jwt_token"]}
        return status
    else:
        status["password"] = False
        return status


# 어드민 광고 리스트 (query string)
def get_all_by_admin_ad_list(category, avg_point, area, gender, avg_age, distance, recruit_time, order_by,
                             sort, page, count):
    db = Database()
    per_page = (page - 1) * int(count)
    status = {"correct_category": True}
    recruit_start = recruit_time.split('~')[0]
    recruit_end = recruit_time.split('~')[1]
    category_value = ""
    if category == "ongoing":
        category_value = "ad_status = 'ongoing'"
    elif category == "scheduled":
        category_value = "ad_status = 'scheduled'"
    elif category == "done":
        category_value = "ad_status = 'done'"
    elif category == 'none':
        category_value = "ad_status IN ('scheduled', 'ongoing', 'done')"
    else:
        status["correct_category"] = False

    # 포인트가 최솟값보다 크고 최대값보다 작은 데이터
    where_point = f"(total_point >= {avg_point[0]} AND total_point <= {avg_point[1]})"
    where_area = check_area_filter(area)
    if int(gender) == 0:
        where_gender = f"gender IN (0, 1, 2)"
    else:
        where_gender = f"gender IN ({gender})"
    where_distance = f"min_distance >= {distance}"
    where_age = f"(min_age_group >= {avg_age[0]} AND max_age_group <= {avg_age[1]})"
    where_recruit_date = f"(recruit_start_date >= '{recruit_start}' AND recruit_end_date <= '{recruit_end}')"

    sql = "SELECT ad_id, owner_name, title, thumbnail_image, activity_period, ad_status, " \
          "max_recruiting_count, recruiting_count, total_point, " \
          "day_point, area, description, gender, min_distance, min_age_group, " \
          "max_age_group, side_image, back_image, side_length, side_width, " \
          "back_length, back_width, logo_image, " \
          "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
          "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date " \
          "FROM ad_information " \
          f"WHERE {category_value} AND {where_point} " \
          f"AND {where_area} AND {where_gender} " \
          f"AND {where_distance} AND {where_age} AND {where_recruit_date} ORDER BY {order_by} {sort} LIMIT %s OFFSET %s"
    result = db.executeAll(query=sql, args=[int(count), per_page])
    item_count = db.executeOne(
        query="SELECT count(ad_id) as item_count FROM ad_information "
              f"WHERE {category_value} AND {where_point} "
              f"AND {where_area} AND {where_gender} "
              f"AND {where_distance} AND {where_age} AND {where_recruit_date}"
    )
    if result:
        for i in range(len(result)):
            result[i]['ad_images'] = db.executeAll(
                query='SELECT image FROM ad_images WHERE ad_id = %s',
                args=result[i]['ad_id']
            )
            result[i]['default_mission_items'] = db.executeAll(
                query='SELECT '
                      'mission_type, due_date, `order`, based_on_activity_period '
                      'FROM ad_mission_card WHERE ad_id = %s AND mission_type = 0',
                args=result[i]['ad_id']
            )
            result[i]['additional_mission_items'] = db.executeAll(
                query='SELECT '
                      'mission_type, due_date, `order`, based_on_activity_period, '
                      'mission_name, additional_point '
                      'FROM ad_mission_card WHERE ad_id = %s AND mission_type = 1',
                args=result[i]['ad_id']
            )
    return result, item_count['item_count']


# # 어드민이 미션 성공여부 체크
def admin_accept_mission(ad_apply_id, mission_card_id, **kwargs):
    db = Database()
    status = kwargs['status']
    result = {"accept": True, "reason": "Update Success", "status": ""}
    mission_information = db.getOneMissionUserInfoByIdx(ad_user_apply_id=ad_apply_id,
                                                        ad_mission_card_id=mission_card_id)
    if mission_information:
        # 이미 바껴있는 값으로 바꿀경우 fail = fail, success = success, reject = reject
        if status == mission_information['status']:
            result["reason"] = "Already Change Status"
            result["accept"] = False
            return result

        elif (status == "fail" or status == "reject") and mission_information['status'] == "success":
            result["reason"] = "Already Success Mission"
            result["accept"] = False
            return result

        else:
            pass

        today_datetime = datetime.now()

        # 미션 성공일 경우
        if status == 'success':
            # 미션 타입에 따라(필수, 선택) 성공 횟수 추가
            other_sql = "SELECT " \
                        "amcu.ad_mission_card_user_id, amcu.status, mission_fail_count, " \
                        "amc.mission_name, amc.mission_type, amc.additional_point, " \
                        "based_on_activity_period, amc.`order`, amc.mission_type, activity_period, " \
                        "mission_fail_count, title, u.user_id as user_id, fcm_token, alarm, due_date " \
                        "FROM ad_mission_card_user as amcu " \
                        "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id " \
                        "JOIN ad_information ai on amc.ad_id = ai.ad_id " \
                        "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id " \
                        "JOIN user u on aua.user_id = u.user_id " \
                        "JOIN user_fcm uf on aua.user_id = uf.user_id " \
                        "WHERE amcu.ad_user_apply_id = %s AND amcu.ad_mission_card_id NOT IN (%s) AND removed = 0 " \
                        "AND mission_start_date = '0000-00-00 00:00:00'"
            other_mission_list = db.executeAll(
                query=other_sql,
                args=[ad_apply_id, mission_card_id]
            )
            if mission_information['mission_type'] == 0:
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET default_mission_success_count = default_mission_success_count + 1 "
                          "WHERE ad_user_apply_id = %s",
                    args=ad_apply_id
                )
            else:
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET additional_mission_success_count = additional_mission_success_count + 1 "
                          "WHERE ad_user_apply_id = %s",
                    args=ad_apply_id
                )
            # 미션 성공으로 업데이트
            db.execute(
                query="UPDATE ad_mission_card_user "
                      "SET status = 'ongoing' WHERE ad_user_apply_id = %s "
                      "AND mission_start_date <= NOW() AND ad_mission_card_user_id NOT IN (%s) "
                      "AND status NOT IN ('success', 'fail')",
                args=[ad_apply_id, mission_information['ad_mission_card_user_id']]
            )
            db.execute(
                query="UPDATE ad_mission_card_user "
                      "SET status = 'success', mission_success_datetime = NOW() WHERE ad_mission_card_user_id = %s",
                args=mission_information['ad_mission_card_user_id']
            )
            if mission_information['order'] == 1 and mission_information['mission_type'] == 0:
                start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                end_date = (date.today() + timedelta(days=(int(mission_information['activity_period']) - 1))) \
                    .strftime('%Y-%m-%d 23:59:59')
                db.execute(
                    query="UPDATE ad_user_apply "
                          "SET activity_start_date = %s, activity_end_date = %s WHERE ad_user_apply_id = %s",
                    args=[start_date, end_date, ad_apply_id]
                )
                if other_mission_list:
                    for idx, value in enumerate(other_mission_list):
                        if value.get('based_on_activity_period') == 0:
                            other_mission_status = 'ongoing'
                        else:
                            other_mission_status = 'stand_by'
                        start_date = date.today() + timedelta(days=value.get('based_on_activity_period'))
                        end_date = (start_date + timedelta(days=value.get('due_date'))).strftime('%Y-%m-%d 23:59:59')
                        db.execute(
                            query="UPDATE ad_mission_card_user "
                                  "SET mission_start_date = %s, mission_end_date = %s, status = %s "
                                  "WHERE ad_mission_card_user_id = %s",
                            args=[start_date.strftime('%Y-%m-%d 00:00:00'), end_date,
                                  other_mission_status, value.get('ad_mission_card_user_id')
                                  ]
                        )
            history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 승인"
            body_name = f"[{mission_information['mission_name']}]에 성공하였습니다. 축하드립니다 :)"
            db.execute(
                query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                args=[mission_information['user_id'], history_name]
            )
            if mission_information['alarm'] == 1:
                # 현재시간이 21시 이전일 경우 앱푸쉬 전송
                if today_datetime.hour < 21:
                    one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                    db.execute(
                        query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                              "VALUES (%s, %s, %s, %s)",
                        args=[mission_information['user_id'], "mission", 1, body_name]
                    )
                # 현재시간이 21시 이후일 경우 앱푸쉬 예약 전송
                else:
                    db.execute(
                        query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                        args=[mission_information['user_id'], body_name]
                    )
            save_message_name = f"{mission_information['mission_name']} 성공"
            db.saveStatusMessage(
                ad_user_apply_id=ad_apply_id, reason=save_message_name, message_type="mission_success"
            )
            db.commit()
            db.db_close()
            result['status'] = "success"
            return result

        elif status == 'reject':
            # 이미 한번 실패했을 경우
            if mission_information['mission_fail_count'] == 1:
                # 필수미션이 한번 이미 실패했을 경우 광고집행 실패
                if mission_information['mission_type'] == 0:
                    title = "신청한 서포터즈 활동에 실패했습니다:("
                    reason = """서포터즈 활동 미션 인증에 실패하였습니다. 활동 미행으로 리워드는 지급해드리지 않으며 다른 서포터즈 활동에 지원해주세요."""
                    db.execute(
                        query="UPDATE ad_mission_card_user "
                              "SET status = 'fail', mission_fail_count = mission_fail_count + 1 "
                              "WHERE ad_user_apply_id = %s",
                        args=ad_apply_id
                    )
                    db.execute(
                        query="UPDATE ad_user_apply SET status = 'fail' WHERE ad_user_apply_id = %s",
                        args=ad_apply_id
                    )
                    db.saveStatusMessage(
                        ad_user_apply_id=ad_apply_id, title=title, reason=reason, message_type="apply_fail"
                    )
                    body_name = f"[{mission_information['mission_name']}] 인증에 실패하였습니다. 다음 기회에 다시 도전해주세요 :("
                    if mission_information['alarm'] == 1:
                        if today_datetime.hour < 21:
                            one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                            db.execute(
                                query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                                      "VALUES (%s, %s, %s, %s)",
                                args=[mission_information['user_id'], "mission", 1, body_name]
                            )
                        else:
                            db.execute(
                                query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                                args=[mission_information['user_id'], body_name]
                            )
                    db.commit()
                    db.db_close()
                    result['status'] = "fail"
                    return result
                # 추가 미션의 경우 실패해도 상관없음(point 미지급)
                else:
                    title = "미션 인증에 실패하였습니다:("
                    reason = "또 다른 미션을 통해 리워드를 지급받으세요!"
                    db.execute(
                        query="UPDATE ad_mission_card_user "
                              "SET status = 'fail', mission_fail_count =  mission_fail_count + 1 "
                              "WHERE ad_mission_card_id = %s AND ad_user_apply_id = %s",
                        args=[mission_card_id, ad_apply_id]
                    )
                    db.execute(
                        query="INSERT INTO ad_mission_reason "
                              "(ad_user_apply_id, title, reason, message_type, is_additional_fail) "
                              "VALUE (%s, %s, %s, %s, %s)",
                        args=[ad_apply_id, title, reason, "mission_fail", 1]
                    )
                history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 실패"
                db.execute(
                    query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                    args=[mission_information['user_id'], history_name]
                )
                body_name = f"[{mission_information['mission_name']}] 인증에 실패하였습니다. 다음 기회에 다시 도전해주세요ㅠㅜ"
                if mission_information['alarm'] == 1:
                    if today_datetime.hour < 21:
                        one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                        db.execute(
                            query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                                  "VALUES (%s, %s, %s, %s)",
                            args=[mission_information['user_id'], "mission", 1, body_name]
                        )
                    else:
                        db.execute(
                            query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                            args=[mission_information['user_id'], body_name]
                        )
                db.commit()
                db.db_close()
                result['status'] = "fail"
                return result

            else:
                body_name = f"[{mission_information['mission_name']}]의 재인증에 도전해주세요!"
                title = "미션 인증에 실패하였습니다:("
                reason = f"""{kwargs['reason']} 재인증에도 실패할 경우, 리워드가 지급되지 않으니 기한 내 재인증 부탁드립니다!"""
                history_name = f"{mission_information['title']} 광고 {mission_information['mission_name']} 실패"
                db.execute(
                    query="UPDATE ad_mission_card_user "
                          "SET status = 'reject', mission_fail_count = mission_fail_count + 1 "
                          "WHERE ad_mission_card_id = %s AND ad_user_apply_id = %s",
                    args=[mission_card_id, ad_apply_id]
                )
                db.execute(
                    query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                    args=[mission_information['user_id'], history_name]
                )
                db.saveStatusMessage(
                    ad_user_apply_id=ad_apply_id, title=title, reason=reason, message_type="mission_fail"
                )
                if mission_information['alarm'] == 1:
                    if today_datetime.hour < 21:
                        one_cloud_messaging(token=mission_information['fcm_token'], body=body_name)
                        db.execute(
                            query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                                  "VALUES (%s, %s, %s, %s)",
                            args=[mission_information['user_id'], "mission", 1, body_name]
                        )
                    else:
                        db.execute(
                            query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                            args=[mission_information['user_id'], body_name]
                        )
                db.commit()
                db.db_close()
                result['status'] = "reject"
                return result


class AdminUserList(Filter):
    def __init__(self):
        super().__init__()
        self.page = None
        self.count = None
        self.per_page = None
        self.user_list = None
        self.item_count = None
        self.each_user_id = None
        self.kwargs = None
        self.area_filter = None
        self.gender_filter = None
        self.age_filter = None
        self.register_time_filter = None
        self.db = Database()

    def set_pages(self, page, count):
        self.page = page
        self.count = count
        self.per_page = (page - 1) * count

    def set_filter(self, area, gender, age, register_time):
        self.area = area
        self.gender = gender
        self.age = age
        self.start_datetime = register_time.split('~')[0]
        self.end_datetime = register_time.split('~')[1]
        self.area_filter = self.get_area()
        self.gender_filter = self.get_gender()
        self.age_filter = self.get_age()
        self.register_time_filter = self.get_user_register_datetime()

    def set_kwargs(self, **kwargs):
        self.kwargs = kwargs

    def set_item_count(self):
        self.item_count = self.get_item_count()

    def set_user_list(self):
        self.user_list = self.get_user_list()
        if self.user_list:
            for i in range(len(self.user_list)):
                self.each_user_id = self.user_list[i]['user_id']
                self.user_list[i]['vehicle_information'] = self.get_vehicle_information()
                self.user_list[i]['activity_history'] = self.get_activity_history()

    def get_user_list(self):
        return self.db.executeAll(
            query="SELECT user_id, nickname, name, call_number, email, "
                  "resident_registration_number_back as gender, "
                  "resident_registration_number_front as date_of_birth, "
                  "marketing, main_address, detail_address, deposit, "
                  "DATE_FORMAT(u.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM user u "
                  f"WHERE {self.area_filter} AND {self.gender_filter} "
                  f"AND {self.age_filter} AND {self.register_time_filter} "
                  "ORDER BY register_time DESC LIMIT %s OFFSET %s",
            args=[self.count, self.per_page]
        )

    def get_item_count(self):
        return self.db.executeOne(
            query="SELECT count(user_id) as item_count FROM user u "
                  f"WHERE {self.area_filter} AND {self.gender_filter} "
                  f"AND {self.age_filter} AND {self.register_time_filter} "
        )

    def get_vehicle_information(self):
        return self.db.executeAll(
            query="SELECT vehicle_id, vehicle_model_name, car_number, brand, owner_relationship, supporters "
                  "FROM vehicle WHERE user_id = %s AND removed = 0",
            args=self.each_user_id
        )

    def get_activity_history(self):
        return self.db.executeAll(
            query="SELECT history_name, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM user_activity_history WHERE user_id = %s ORDER BY register_time DESC",
            args=self.each_user_id
        )

    # 어드민 회원 정보 수정
    def user_profile_modify(self):
        self.db.execute(
            query="UPDATE user SET nickname = %s, email = %s, main_address = %s, detail_address = %s WHERE user_id = %s",
            args=[self.kwargs.get('nickname'), self.kwargs.get('email'), self.kwargs.get('main_address'),
                  self.kwargs.get('detail_address'), self.kwargs.get('user_id')]
        )
        self.db.commit()
        self.db.db_close()
        return self.kwargs

    # 어드민 회원리스트 및 회원 관리  모집번호 추가
    def response(self):
        self.set_user_list()
        self.set_item_count()
        self.db.db_close()
        return self.user_list, self.item_count['item_count']


class AdminWithdrawal:
    def __init__(self, is_point):
        self.is_point = is_point
        self.page = None
        self.count = None
        self.per_page = None
        self.kwargs = None
        self.status_list = []
        self.db = Database()

    def set_pages(self, page, count):
        self.page = page
        self.count = count
        self.per_page = (page - 1) * count

    def get_item_count(self):
        if self.is_point:
            return self.db.executeOne(
                query="SELECT count(withdrawal_self_id) as item_count FROM withdrawal_self"
            )
        else:
            return self.db.executeOne(
                query="SELECT count(withdrawal_donate_id) as item_count FROM withdrawal_donate"
            )

    def get_all_withdrawal(self):
        if self.is_point:
            return self.db.executeAll(
                query="SELECT "
                      "withdrawal_self_id, w.account_bank, name, w.account_number, user.user_id, amount, `status`, "
                      "DATE_FORMAT(w.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, call_number,"
                      "CASE WHEN w.change_done = '0000-00-00 00:00:00' THEN '' "
                      "WHEN w.change_done IS NOT NULL "
                      "THEN DATE_FORMAT(w.change_done, '%%Y-%%m-%%d %%H:%%i:%%s') END as change_done "
                      "FROM user JOIN withdrawal_self w on user.user_id = w.user_id "
                      "ORDER BY FIELD(`status`, 'waiting', 'checking', 'reject', 'cancel', 'done') LIMIT %s OFFSET %s",
                args=[self.count, self.per_page]
            )
        else:
            return self.db.executeAll(
                query="SELECT "
                      "name, user.user_id, amount, `status`, donation_organization_name as donation_organization, "
                      "receipt, name_of_donor, withdrawal_donate_id, call_number, "
                      "DATE_FORMAT(wd.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, "
                      "CASE WHEN wd.change_done = '0000-00-00 00:00:00' THEN '' "
                      "WHEN wd.change_done IS NOT NULL "
                      "THEN DATE_FORMAT(wd.change_done, '%%Y-%%m-%%d %%H:%%i:%%s') END as change_done "
                      "FROM user JOIN withdrawal_donate wd on user.user_id = wd.user_id "
                      "JOIN donation_organization d on wd.donation_organization_id = d.donation_organization_id "
                      "ORDER BY FIELD(`status`, 'waiting', 'checking', 'reject', 'cancel', 'done') "
                      "LIMIT %s OFFSET %s",
                args=[self.count, self.per_page]
            )

    def response(self):
        response = self.get_all_withdrawal()
        item_count = self.get_item_count()
        return response, item_count['item_count']


# 어드민 포인트 출금 상태 변경  (waiting(대기중), confirm(확인), done(승인), reject(반려))
def update_withdrawal_point(**kwargs):
    result = withdrawal_total_result(withdrawal_type="point", **kwargs)
    return result


# 어드민 기부 출금 상태 변경 (waiting(대기중), checking(확인중), done(승인), reject(반려))
def update_withdrawal_donate(**kwargs):
    result = withdrawal_total_result(withdrawal_type="donate", **kwargs)
    return result


def withdrawal_total_result(withdrawal_type, **kwargs):
    db = Database()
    status_list = []
    if withdrawal_type == "point":
        user_list = kwargs['withdrawal_list']
        if user_list:
            if kwargs['status'] == "done":
                fcm_list = []
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_self "
                              "JOIN user u on withdrawal_self.user_id = u.user_id WHERE withdrawal_self_id = %s",
                        args=user_list[i]
                    )
                    if int(user_information['deposit']) - int(user_information["amount"]) >= 0:
                        db.execute(
                            query="UPDATE withdrawal_self "
                                  "SET status = 'done', change_done = NOW() "
                                  "WHERE withdrawal_self_id = %s",
                            args=user_list[i]
                        )
                        fcm_token = db.executeOne(
                            query="SELECT fcm_token, alarm FROM user_fcm uf JOIN user u on uf.user_id = u.user_id "
                                  "WHERE u.user_id = %s AND alarm = 1",
                            args=user_information['user_id'])
                        if fcm_token:
                            fcm_list.append(fcm_token['fcm_token'])
                    else:
                        status_list.append({i: False})
                multiple_cloud_messaging(tokens=fcm_list, body="[출금]이 완료되었습니다. 통장 내역을 확인해보세요 :)")
                db.commit()
                db.db_close()
                return kwargs['status']
            elif kwargs['status'] == "reject":
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_donate "
                              "JOIN user u on withdrawal_donate.user_id = u.user_id WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                    db.execute(
                        query="UPDATE withdrawal_self "
                              "SET status = 'reject', change_reject = NOW() "
                              "WHERE withdrawal_self_id = %s",
                        args=user_list[i]
                    )
                    db.execute(
                        query="UPDATE user SET deposit = deposit - %s WHERE user_id = %s",
                        args=[user_information['amount'], user_information['user_id']]
                    )
                    db.execute(
                        query="INSERT INTO point_history (user_id, point, contents) VALUES (%s, %s, %s)",
                        args=[user_information['user_id'], -user_information['amount'], "[출금] 이 거부되었습니다."]
                    )
                db.commit()
                db.db_close()
                return kwargs['status']
            elif kwargs['status'] == "confirm":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_self "
                              "SET status = %s, change_confirm = NOW() "
                              "WHERE withdrawal_self_id = %s",
                        args=[kwargs['status'], user_list[i]]
                    )
                db.commit()
                db.db_close()
                return kwargs['status']

    elif withdrawal_type == "donate":
        user_list = kwargs['withdrawal_donate_list']
        if user_list:
            # 기부 완료
            if kwargs['status'] == "done":
                fcm_list = []
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_donate "
                              "JOIN user u on withdrawal_donate.user_id = u.user_id WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                    if int(user_information['deposit']) - int(user_information["amount"]) >= 0:
                        db.execute(
                            query="UPDATE withdrawal_donate SET status = 'done', change_done = NOW() "
                                  "WHERE withdrawal_donate_id = %s",
                            args=user_list[i]
                        )
                        fcm_token = db.executeOne(
                            query="SELECT fcm_token, alarm FROM user_fcm uf JOIN user u on uf.user_id = u.user_id "
                                  "WHERE u.user_id = %s AND alarm = 1",
                            args=user_information['user_id'])
                        if fcm_token:
                            fcm_list.append(fcm_token['fcm_token'])
                    else:
                        status_list.append({i: False})
                multiple_cloud_messaging(tokens=fcm_list, body="[기부]가 완료되었습니다. 당신의 나눔으로 세상이 더욱 따듯해졌습니다 :)")
                db.commit()
                db.db_close()
                return kwargs['status']
            # 기부 reject
            elif kwargs['status'] == "reject":
                for i in range(len(user_list)):
                    user_information = db.executeOne(
                        query="SELECT u.user_id, deposit, amount FROM withdrawal_donate "
                              "JOIN user u on withdrawal_donate.user_id = u.user_id WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                    db.execute(
                        query="UPDATE withdrawal_donate "
                              "SET status = 'reject', change_reject = NOW() "
                              "WHERE withdrawal_donate_id = %s",
                        args=user_list[i]
                    )
                    db.execute(
                        query="UPDATE user SET deposit = deposit - %s WHERE user_id = %s",
                        args=[user_information['amount'], user_information['user_id']]
                    )
                db.commit()
                db.db_close()
                return kwargs['status']
            # 기부 진행중
            elif kwargs['status'] == "confirm":
                for i in range(len(user_list)):
                    db.execute(
                        query="UPDATE withdrawal_donate "
                              "SET status = %s, change_confirm = NOW() "
                              "WHERE withdrawal_donate_id = %s",
                        args=[kwargs['status'], user_list[i]]
                    )
                db.commit()
                db.db_close()
                return kwargs['status']


# 기부 단체 등록
def donation_organization_register(logo_image, images, **kwargs):
    db = Database()
    db.execute(
        query="INSERT INTO donation_organization (donation_organization_name) "
              "VALUES (%s)",
        args=kwargs.get('donation_organization_name')
    )
    last_insert_id = db.executeOne(
        query="SELECT donation_organization_id FROM donation_organization ORDER BY register_time DESC LIMIT 1",
    )['donation_organization_id']
    directory = f"{BASE_IMAGE_LOCATION_DONATION}/{last_insert_id}"
    logo_url = f"{DONATION_ORGANIZATION_IMAGE_HOST}/{last_insert_id}/{secure_filename(logo_image.filename)}"
    os.makedirs(directory, exist_ok=True)
    db.execute(
        query="UPDATE donation_organization SET logo_image = %s WHERE donation_organization_id = %s",
        args=[logo_url, last_insert_id]
    )
    logo_image.save(directory + "/" + secure_filename(logo_image.filename))
    for i in range(len(images)):
        description = kwargs["descriptions"][i]
        image = images[i]
        image_url = f"{DONATION_ORGANIZATION_IMAGE_HOST}/{last_insert_id}/{secure_filename(image.filename)}"
        db.execute(
            query="INSERT INTO donation_organization_images (donation_organization_id, image, description) "
                  "VALUES (%s, %s, %s)",
            args=[last_insert_id, image_url, description]
        )
        image.save(directory + "/" + secure_filename(image.filename))
    db.commit()

    response_data = db.executeOne(
        query="SELECT donation_organization_id, donation_organization_name, logo_image, "
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
              "FROM donation_organization WHERE donation_organization_id = %s",
        args=last_insert_id
    )
    images = db.executeAll(
        query="SELECT image, description FROM donation_organization_images WHERE donation_organization_id = %s",
        args=last_insert_id
    )
    response_data["image_information"] = images
    db.db_close()
    return response_data


class AdminPointGet:
    def __init__(self, page, count, min_point, max_point):
        self.count = count
        self.per_page = (page - 1) * count
        self.min_point = min_point
        self.max_point = max_point
        self.db = Database()

    # item_count
    def get_item_count(self):
        return self.db.executeOne(
            query="SELECT count(user_id) as item_count FROM user WHERE deposit >= %s AND deposit <= %s",
            args=[self.min_point, self.max_point]
        )['item_count']

    # Database 의 클래스를 상속받아 부모클래스의 method 사용
    def get_user_information(self):
        return self.db.executeAll(
            query="SELECT user_id, nickname, name, call_number, email, deposit FROM user "
                  "WHERE deposit >= %s AND deposit <= %s "
                  "ORDER BY register_time DESC LIMIT %s OFFSET %s",
            args=[self.min_point, self.max_point, self.count, self.per_page]
        )

    def get_user_point_history(self, user_id):
        return self.db.executeAll(
            query="SELECT point, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, contents "
                  "FROM point_history WHERE user_id = %s ORDER BY register_time DESC",
            args=user_id
        )

    def response_user_point_history(self):
        user_information = self.get_user_information()
        if user_information:
            for i in range(len(user_information)):
                point_history = self.get_user_point_history(user_id=user_information[i]['user_id'])
                user_information[i]['point_history'] = point_history

            return user_information, self.get_item_count()
        else:
            return False, self.get_item_count()


class AdminPointPost:
    # 생성자
    def __init__(self, user_id, point, contents):
        self.user_id = user_id
        self.point = point
        self.contents = contents
        self.db = Database()

    def get_last_point_history(self):
        point_history = self.db.executeOne(
            query="SELECT point, contents, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM point_history "
                  "WHERE user_id = %s ORDER BY register_time DESC LIMIT 1",
            args=self.user_id
        )
        return point_history

    def set_insert_point_history_query(self):
        return f"INSERT INTO point_history (user_id, point, contents) VALUES " \
               f"({self.user_id}, {self.point}, '{self.contents}')"

    def set_update_user_deposit_query(self):
        return f"UPDATE user SET deposit = deposit + {self.point} WHERE user_id = {self.user_id}"

    def update_user_point(self):
        self.db.execute(query=self.set_update_user_deposit_query(), args=None)
        self.db.execute(query=self.set_insert_point_history_query(), args=None)
        self.db.commit()
        point_history = self.get_last_point_history()
        self.db.db_close()
        return point_history


class AdminPointAll:
    # 생성자
    def __init__(self, user_list, point, contents):
        self.point = point
        self.contents = contents
        self.user_list = user_list
        self.db = Database()

    # executemany 의 value 설정
    def set_history_many_value(self):
        history_value_list = [[self.point, self.contents, user] for user in self.user_list]
        return history_value_list

    # executemany 의 value 설정
    def set_user_point_many_value(self):
        point_value_list = [[self.point, user] for user in self.user_list]
        return point_value_list

    # 포인트 이력 넣기
    def insert_point_history(self):
        self.db.executemany(
            query="INSERT INTO point_history SET point = %s, contents = %s, user_id = %s",
            args=self.set_history_many_value()
        )
        self.db.commit()

    # 포인트 업데이트
    def update_point_user(self):
        self.db.executemany(
            query="UPDATE user SET deposit = deposit + %s WHERE user_id = %s",
            args=self.set_user_point_many_value()
        )
        self.db.commit()

    def get_point_history(self):
        return self.db.executeOne(
            query="SELECT point, contents, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM point_history ORDER BY register_time DESC LIMIT 1"
        )

    # 결과
    def response(self):
        self.insert_point_history()
        self.update_point_user()
        response = self.get_point_history()
        self.db.db_close()
        return response
