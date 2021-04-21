from ..database.dbConnection import Database
from werkzeug.utils import secure_filename
import os

BASE_IMAGE_LOCATION = os.getcwd() + "/CashCar/appConfig/static/image/mission"


# 미션카드 등록
# def register(**kwargs):
#     db = Database()
#     sql = "INSERT INTO mission_card " \
#           "(mission_type, mission_name, additional_point, due_date) " \
#           "VALUES " \
#           "(%s, %s, %s, %s)"
#     value_list = [
#         kwargs.get('mission_type'),
#         kwargs.get('mission_name'),
#         kwargs.get('additional_point'),
#         kwargs.get('due_date')
#     ]
#     db.execute(query=sql, args=value_list)
#     db.commit()
#     return True


# 미션 이미지 등록
def mission_save_images(image_dict):
    db = Database()
    save_to_db_dict = {}
    directory = f"{BASE_IMAGE_LOCATION}"
    os.makedirs(directory, exist_ok=True)
    for key, val in image_dict.items():
        # save_db = BASE_IMAGE_LOCATION_BACK + "/" + secure_filename(val.filename)
        val.save(directory + "/" + secure_filename(val.filename))
        save_to_db_dict.setdefault(key, directory + "/" + secure_filename(val.filename))

    db.execute(
        query="INSERT INTO mission_images (side_image, back_image) VALUES (%s, %s)",
        args=[save_to_db_dict["side_image"], save_to_db_dict["back_image"]]
    )
    db.commit()

    return True


# 미션 입
def get_mission_type_idx_by_stand_by(ad_mission_card_user_id):
    db = Database()
    amcu_id_and_mission_type = db.executeOne(
        query="SELECT mission_type, ad_mission_card_user_id, ad_mission_card_id "
              "FROM ad_mission_card_user WHERE ad_mission_card_user_id = %s AND status != 'stand_by'",
        args=ad_mission_card_user_id
    )
    return amcu_id_and_mission_type

# def get_mission_type_idx_by_review(ad_mission_card_user_id):
#     db = Database()
#     amcu_information = db.executeOne(
#         query="SELECT "
#     )


# 사용자 미션 하기
def user_apply_mission(ad_mission_card_user_id, ad_mission_card_id, mission_type, image_dict, travelled_distance):
    db = Database()
    save_to_db_dict = {}
    directory = f"{BASE_IMAGE_LOCATION}/{ad_mission_card_id}"
    os.makedirs(directory, exist_ok=True)
    # 필수미션 인증하기
    for key, val in image_dict.items():
        val.save(directory + "/" + secure_filename(val.filename))
        save_to_db_dict.setdefault(key, f"/mission/{ad_mission_card_id}/" + secure_filename(val.filename))

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
            query="UPDATE ad_mission_card_user SET status = 'review' WHERE ad_mission_card_user_id = %s",
            args=ad_mission_card_user_id
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
            query="UPDATE ad_mission_card_user SET status = 'review' WHERE ad_mission_card_user_id = %s",
            args=ad_mission_card_user_id
        )
    else:
        return False

    db.commit()
    return True

