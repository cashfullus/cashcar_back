from ..database.dbConnection import Database
from werkzeug.utils import secure_filename
import os
BASE_IMAGE_LOCATION = os.getcwd() + "/appConfig/static/image/mission"


# 미션카드 등록
def register(**kwargs):
    db = Database()
    sql = "INSERT INTO mission_card " \
          "(mission_type, mission_name, additional_point, due_date) " \
          "VALUES " \
          "(%s, %s, %s, %s)"
    value_list = [
        kwargs.get('mission_type'),
        kwargs.get('mission_name'),
        kwargs.get('additional_point'),
        kwargs.get('due_date')
    ]
    db.execute(query=sql, args=value_list)
    db.commit()
    return True


# 미션카드 광고와 매칭하기
def mission_assign_advertisement(**kwargs):
    db = Database()
    sql = "INSERT INTO ad_mission_card (ad_id, mission_card_id) VALUES (%s, %s)"

    mission_list = kwargs['mission_list']

    for i in range(len(mission_list)):
        db.execute(query=sql, args=[kwargs.get('ad_id'), mission_list[i]])

    db.commit()
    return True


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
