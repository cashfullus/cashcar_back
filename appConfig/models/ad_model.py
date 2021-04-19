from ..database.dbConnection import Database
from werkzeug.utils import secure_filename

from datetime import date, timedelta, datetime

import os

BASE_IMAGE_LOCATION = os.getcwd() + "/CashCar/appConfig/static/image/adverting"
BASE_IMAGE_LOCATION_BACK = "/appConfig/static/image/adverting"


# 광고 등록 / (현재 이미지는 미정 2021-04-13 ) title_image 의 첫번째는 무조건 썸네일 이미지가 된다.
def register(image_dict, **kwargs):
    db = Database()
    sql = "INSERT INTO ad_information " \
          "(title, recruit_start_date, recruit_end_date, activity_period, " \
          "max_recruiting_count, total_point, day_point, area, description) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    kwargs['recruit_start_date'] = kwargs['recruit_start_date'] + " 00:00:00"
    kwargs['recruit_end_date'] = kwargs['recruit_end_date'] + " 23:59:59"

    value_list = [kwargs['title'], kwargs['recruit_start_date'],
                  kwargs['recruit_end_date'], kwargs['activity_period'],
                  kwargs['max_recruiting_count'], kwargs['total_point'],
                  int(kwargs['total_point']) // int(kwargs['activity_period']),
                  kwargs['area'], kwargs['description']
                  ]

    db.execute(query=sql, args=value_list)
    db.commit()

    register_id = db.executeOne(query="SELECT ad_id FROM ad_information ORDER BY register_time DESC LIMIT 1")
    if register_id:
        save_to_db_dict = {}
        directory = f"{BASE_IMAGE_LOCATION}/{register_id['ad_id']}"
        os.makedirs(directory, exist_ok=True)
        # 서버에서는 Cashcar라는 directory 안에 있기때문에 추가
        for key, val in image_dict.items():
            # save_db = BASE_IMAGE_LOCATION_BACK + "/" + secure_filename(val.filename)
            val.save(directory + "/" + secure_filename(val.filename))
            save_to_db_dict.setdefault(key, directory + "/" + secure_filename(val.filename))

        db.execute(
            query="UPDATE ad_information SET title_image = %s, logo_image = %s WHERE ad_id = %s",
            args=[save_to_db_dict.get('title_image'), save_to_db_dict.get('logo_image'), register_id['ad_id']]
        )
        db.commit()
        return True
    else:
        return False


# 광고 리스트 (parameter query_string)
def get_all_by_category_ad_list(page, category):
    db = Database()
    per_page = (page - 1) * 20
    start_at = per_page + 20
    status = {"correct_category": True}
    sql_parameter_val = ""
    # 모집중인 광고
    if category == "ongoing":
        sql_parameter_val = "recruit_start_date <= NOW() AND recruit_end_date >= NOW()"
    elif category == "scheduled":
        sql_parameter_val = "recruit_start_date > NOW()"
    elif category == "done":
        sql_parameter_val = "recruit_end_date < NOW() OR recruiting_count = max_recruiting_count"
    else:
        status["correct_category"] = False

    sql = "SELECT ad_id, title, title_image, " \
          "max_recruiting_count, recruiting_count, total_point, area," \
          "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
          "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date " \
          f"FROM ad_information WHERE {sql_parameter_val} " \
          "LIMIT %s OFFSET %s"

    result = db.executeAll(query=sql, args=[start_at, per_page])
    return result, status


# 광고 디테일
def get_ad_information_by_id(ad_id):
    db = Database()
    result = db.getOneAdByAdId(ad_id)
    return result


# 광고신청 창 GET
def get_information_for_ad_apply(user_id, ad_id):
    db = Database()
    status = {"ad_information": True, "user_information": True}
    ad_information = db.executeOne(
        query="SELECT ad_id, logo_image, title, total_point "
              "FROM ad_information WHERE ad_id = %s",
        args=ad_id
    )
    vehicle_information = db.getAllVehicleByUserId(user_id=user_id)
    user_information = db.executeOne(
        query="SELECT "
              "name, call_number, main_address, detail_address "
              "FROM user WHERE user_id = %s",
        args=user_id
    )
    if not ad_information:
        status["ad_information"] = False
    elif not user_information:
        status["user_information"] = False
    else:
        pass

    result = {
        "ad_information": ad_information,
        "vehicle_information": vehicle_information,
        "user_information": user_information
    }

    return result, status


# 광고 신청 POST
def ad_apply(user_id, ad_id, **kwargs):
    db = Database()
    status = {"user_information": True, "ad_information": True, "already_apply": True}
    target_user = db.getUserById(user_id)
    target_ad = db.getOneAdApplyByAdId(ad_id)
    already_apply_ad = db.executeOne(
        query="SELECT ad_user_apply_id FROM ad_user_apply WHERE status in (0, 1) and user_id = %s",
        args=user_id
    )

    if not target_ad:
        status["ad"] = False
        return status

    elif not target_user:
        status["user"] = False
        return status

    elif already_apply_ad:
        status["already_apply"] = False
        return status

    else:
        db.execute(
            query="UPDATE user SET main_address = %s, "
                  "detail_address = %s, call_number = %s, name = %s "
                  "WHERE user_id = %s",
            args=[kwargs['main_address'], kwargs['detail_address'], kwargs['call_number'], kwargs['name'], user_id]
        )
        db.execute(
            query="INSERT INTO ad_user_apply (user_id, ad_id, register_time) VALUES (%s, %s, NOW())",
            args=[user_id, ad_id]
        )
        db.execute(
            query="UPDATE ad_information SET recruiting_count = recruiting_count + 1 WHERE ad_id = %s",
            args=ad_id
        )
        db.commit()

        return status


# 진행중인 광고 By User
def get_ongoing_ad(user_id):
    db = Database()
    result = db.executeOne(
        query="SELECT "
              "* "
              "FROM ad_mission_card_user as amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id AND aua.user_id = %s",
        args=user_id
    )
    return result


# 광고 신청 목록
def ad_apply_list():
    db = Database()
    result = db.getAllAdUserApply()
    return result


# 광고신청 목록 -> Detail
def get_ad_apply(ad_user_apply_id):
    db = Database()
    result = db.getOneAdUserApplyById(ad_user_apply_id=ad_user_apply_id)
    if result:
        return result
    else:
        return False


# 메인화면 본인이 진행중인 광고 카드의 정보
def get_ongoing_user_by_id(user_id):
    db = Database()
    result = db.getMainMyAd(user_id=user_id)
    if result:
        return result
    else:
        return False


# 신청한 광고 status 업데이트
# 먼저 광고와 연결된 미션 을 전부 return
# 그 해당 미션에 대해 미션하기를 누를시 데이터 생성
#
# 승인시 flow (default = stand_by(승인 대기중) -> accept(승인) -> during_delivery(배송중) -> delivery_completed(배송완료)
# 거절시 flow (default = stand_by(승인 대기중) -> reject(거절)
def update_ad_apply_status(ad_user_apply_id, **kwargs):
    db = Database()
    apply_information = {"rejected": True, "accept": True}
    apply_status = db.getOneApplyStatus(ad_user_apply_id=ad_user_apply_id)
    if apply_status["status"] == "reject" and kwargs["status"] == "reject":
        apply_information["rejected"] = False
        return apply_information

    elif apply_status["status"] == "accept" and kwargs["status"] == "accept":
        apply_information["accept"] = False
        return apply_information

    else:
        if kwargs["status"] == "reject":
            # ad_user_apply 테이블에서 ad_id 가 같은 ad_information 테이블에서 모집인원 -1 (ad_user_apply_id)에 맞는 데이터
            db.execute(
                query="UPDATE ad_information as ad_info "
                      "JOIN ad_user_apply aua on ad_info.ad_id = aua.ad_id "
                      "SET ad_info.recruiting_count = ad_info.recruiting_count - 1 "
                      "WHERE aua.ad_user_apply_id = %s",
                args=ad_user_apply_id
            )

        elif kwargs["status"] == "accept":
            ad_mission_card_info = db.getAdMissionCardIdsByAcceptApply(ad_user_apply_id=ad_user_apply_id)
            # 수락후 미션 생성
            for i in range(len(ad_mission_card_info)):
                if ad_mission_card_info[i]["mission_card_id"] == 1:
                    first_start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    first_end_date = date.today() + timedelta(days=ad_mission_card_info[i]["due_date"])
                    db.execute(
                        query="INSERT INTO "
                              "ad_mission_card_user "
                              "(ad_user_apply_id, ad_mission_card_id, status, "
                              "mission_start_date, mission_end_date, register_time) "
                              "VALUES (%s, %s, %s, %s, %s, NOW())",
                        args=[ad_user_apply_id, ad_mission_card_info[i]["ad_mission_card_id"], "ongoing",
                              first_start_date, first_end_date.strftime('%Y-%m-%d 23:59:59')]
                    )
                else:
                    db.execute(
                        query="INSERT INTO "
                              "ad_mission_card_user "
                              "(ad_user_apply_id, ad_mission_card_id, register_time) "
                              "VALUES (%s, %s, NOW())",
                        args=[ad_user_apply_id, ad_mission_card_info[i]["ad_mission_card_id"]]
                    )
        db.execute(
            query="UPDATE ad_user_apply SET status = %s WHERE ad_user_apply_id = %s",
            args=[kwargs['status'], ad_user_apply_id]
        )
        db.commit()
        return apply_information
