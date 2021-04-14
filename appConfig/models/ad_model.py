from ..database.dbConnection import Database
from werkzeug.utils import secure_filename
import os

BASE_IMAGE_LOCATION = os.getcwd() + "/appConfig/static/image/adverting"
BASE_IMAGE_LOCATION_BACK = "/appConfig/static/image/adverting"


# 광고 등록 / (현재 이미지는 미정 2021-04-13 )
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
    per_page = (page-1)*20
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

#
# # 광고 신청 POST
# def ad_apply(user_id, ad_id, **kwargs):
#     db = Database()
#     target_user = db.getUserById(user_id)
#     target_ad = db.getOneAdByAdId(ad_id)
#
#     if target_ad and target_user:
#








