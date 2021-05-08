from database.dbConnection import Database
from werkzeug.utils import secure_filename
import os

BASE_IMAGE_LOCATION = os.getcwd() + "/static/image/mission"
MISSION_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/mission"


# 페이지 적용
def page_nation(page, count):
    per_page = (int(page) - 1) * int(count)
    return per_page


# 미션 데이터 정보
def get_mission_type_idx_by_stand_by(ad_mission_card_user_id):
    db = Database()
    amcu_id_and_mission_type = db.executeOne(
        query="SELECT mission_type, ad_mission_card_user_id, ad_mission_card_id "
              "FROM ad_mission_card_user WHERE ad_mission_card_user_id = %s AND status != 'stand_by'",
        args=ad_mission_card_user_id
    )
    return amcu_id_and_mission_type


# 사용자 미션 하기
def user_apply_mission(ad_mission_card_user_id, ad_mission_card_id, mission_type, image_dict, travelled_distance):
    db = Database()
    save_to_db_dict = {}
    directory = f"{BASE_IMAGE_LOCATION}/{ad_mission_card_id}"
    os.makedirs(directory, exist_ok=True)
    # 필수미션 인증하기
    for key, val in image_dict.items():
        val.save(directory + "/" + secure_filename(val.filename))
        save_to_db_dict.setdefault(key, f"{MISSION_IMAGE_HOST}/{ad_mission_card_id}/" + secure_filename(val.filename))
    # mission_fail_count 조회
    fail_count = db.executeOne(
        query="SELECT mission_fail_count FROM ad_mission_card_user WHERE ad_mission_card_user_id = %s",
        args=ad_mission_card_user_id
    )
    if fail_count['mission_fail_count'] >= 1:
        review_status = "re_review"
    else:
        review_status = "review"
    # 미션 타입에 따른 db저장
    if mission_type == 0:
        db.execute(
            query="UPDATE mission_images "
                  "SET side_image =%s, back_image = %s, instrument_panel = %s, "
                  "travelled_distance = %s, updated_time = NOW() "
                  "WHERE ad_mission_card_user_id = %s",
            args=[save_to_db_dict["side_image"], save_to_db_dict["back_image"],
                  save_to_db_dict["instrument_panel_image"], travelled_distance, ad_mission_card_user_id]
        )
        db.execute(
            query="UPDATE ad_mission_card_user SET status = %s WHERE ad_mission_card_user_id = %s",
            args=[review_status, ad_mission_card_user_id]
        )
    # 선택미션인 경우
    elif mission_type == 1:
        db.execute(
            query="UPDATE mission_images "
                  "SET side_image =%s, back_image = %s, updated_time = NOW() "
                  "WHERE ad_mission_card_user_id = %s",
            args=[save_to_db_dict["side_image"], save_to_db_dict["back_image"], ad_mission_card_user_id]
        )
        db.execute(
            query="UPDATE ad_mission_card_user SET status = %s WHERE ad_mission_card_user_id = %s",
            args=[review_status, ad_mission_card_user_id]
        )
    else:
        return False

    db.commit()
    return True


# 미션 review -> success
# review -> reject -> re_review -> success or fail
# register_time, end_date, title, mission_name, name, call_number, mission_status,
# image
# 사용자의 미션 인증 신청 리스트
def admin_review_mission_list(page, count):
    db = Database()
    per_page = page_nation(int(page), int(count))

    result = db.executeAll(
        query="SELECT "
              "DATE_FORMAT(amcu.register_time, '%%Y-%%m-%%d %%H:%%m:%%s') as register_time, "
              "DATE_FORMAT(amcu.mission_end_date, '%%Y-%%m-%%d %%H:%%m:%%s') as mission_end_date, "
              "aua.ad_user_apply_id, amc.ad_mission_card_id as mission_card_id,"
              "ai.title, amc.mission_name, u.name, u.call_number, "
              "amcu.status, mi.side_image, mi.back_image, mi.instrument_panel, mi.travelled_distance, "
              "amc.mission_type "
              "FROM ad_mission_card_user amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN user u on aua.user_id = u.user_id " 
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "JOIN mission_images mi on amcu.ad_mission_card_user_id = mi.ad_mission_card_user_id "
              "WHERE aua.status IN ('accept', 'stand_by') AND amcu.status IN ('review', 're_review') "
              "GROUP BY amcu.ad_mission_card_user_id "
              "LIMIT %s OFFSET %s",
        args=[int(count), per_page]
    )
    item_count = db.executeAll(
        query="SELECT aua.ad_user_apply_id "
              "FROM ad_mission_card_user amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN user u on aua.user_id = u.user_id " 
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "JOIN mission_images mi on amcu.ad_mission_card_user_id = mi.ad_mission_card_user_id "
              "WHERE aua.status IN ('accept', 'stand_by') AND amcu.status IN ('review', 're_review') "
              "GROUP BY amcu.ad_mission_card_user_id"
    )
    return result, len(item_count)


# 사용자 미션 인증 신청에서 디테일 미션 리스트
def admin_review_detail_mission_list(ad_mission_card_id, ad_user_apply_id):
    db = Database()
    result = db.executeAll(
        query="SELECT "
              "amcu.status, amc.mission_name, mi.side_image, mi.back_image, "
              "mi.instrument_panel, mi.travelled_distance, amcu.mission_type "
              "FROM ad_mission_card_user as amcu "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "JOIN mission_images mi on amcu.ad_mission_card_user_id = mi.ad_mission_card_user_id "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "WHERE amc.ad_mission_card_id NOT IN (%s) AND aua.ad_user_apply_id = %s",
        args=[ad_mission_card_id, ad_user_apply_id]
    )
    return result
