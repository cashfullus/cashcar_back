from ..database.dbConnection import Database
from werkzeug.utils import secure_filename

from datetime import date, timedelta, datetime

import os

BASE_IMAGE_LOCATION = os.getcwd() + "/CashCar/appConfig/static/image/adverting"
BASE_IMAGE_LOCATION_BACK = "/CashCar/appConfig/static/image/adverting"
AD_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/adverting"


# Admin 광고등록하기
def admin_ad_register(other_images, ad_images, req_method, **kwargs):
    db = Database()
    # 데이터 준비
    if req_method != 'DELETE':
        kwargs['recruit_start_date'] = kwargs['recruit_start_date'] + " 00:00:00"
        kwargs['recruit_end_date'] = kwargs['recruit_end_date'] + " 23:59:59"
        value_list = [kwargs['owner_name'], kwargs['title'], kwargs['recruit_start_date'],
                      kwargs['recruit_end_date'], kwargs['activity_period'], kwargs['max_recruiting_count'],
                      kwargs['total_point'], int(kwargs['total_point']) // int(kwargs['activity_period']),
                      kwargs['area'], kwargs['description'], kwargs['min_distance'], kwargs['gender'],
                      kwargs['min_age_group'], kwargs['max_age_group'], kwargs['side_length'], kwargs['side_width'],
                      kwargs['back_length'], kwargs['back_width']
                      ]
        if kwargs.get('ad_id') == 0:
            sql = "INSERT INTO ad_information " \
                  "(owner_name, title, recruit_start_date, recruit_end_date, " \
                  "activity_period, max_recruiting_count, " \
                  "total_point, day_point, area, description, min_distance, gender, " \
                  "min_age_group, max_age_group, side_length, side_width, back_length, back_width) " \
                  "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            db.execute(query=sql, args=value_list)
            db.commit()
            register_id = db.executeOne(query="SELECT ad_id FROM ad_information ORDER BY register_time DESC LIMIT 1")
            if register_id:
                save_to_db_dict = {}
                save_to_db_list = []
                directory = f"{BASE_IMAGE_LOCATION}/{register_id['ad_id']}"
                os.makedirs(directory, exist_ok=True)

                for key, val in other_images.items():
                    val.save(directory + "/" + secure_filename(val.filename))
                    save_to_db_dict.setdefault(key,
                                               f"{AD_IMAGE_HOST}/{register_id['ad_id']}/" + secure_filename(
                                                   val.filename))

                for image in ad_images:
                    image.save(directory + "/" + secure_filename(image.filename))
                    value = f"{AD_IMAGE_HOST}/{register_id['ad_id']}/{secure_filename(image.filename)}"
                    save_to_db_list.append(value)

                db.execute(
                    query="UPDATE ad_information "
                          "SET thumbnail_image = %s, side_image = %s, back_image = %s "
                          "WHERE ad_id = %s",
                    args=[save_to_db_dict['thumbnail_image'],
                          save_to_db_dict['side_image'],
                          save_to_db_dict['back_image'],
                          register_id['ad_id']
                          ]
                )
                for i in range(len(save_to_db_list)):
                    db.execute(
                        query="INSERT INTO ad_images (ad_id, image) VALUES (%s, %s)",
                        args=[register_id['ad_id'], save_to_db_list[i]]
                    )

                default_mission_items = kwargs['default_mission_items']
                additional_mission_items = kwargs['additional_mission_items']

                if default_mission_items[0]:
                    for item in default_mission_items[0]:
                        mission_name = f"{item['order']}차 필수미션"
                        db.execute(
                            query="INSERT INTO ad_mission_card "
                                  "(ad_id, mission_type, mission_name,due_date, `order`, based_on_activity_period) "
                                  "VALUES (%s, %s, %s, %s, %s, %s)",
                            args=[register_id['ad_id'], item['mission_type'], mission_name,
                                  item['due_date'], item['order'], item['based_on_activity_period']]
                        )
                    kwargs['default_mission_items'] = default_mission_items[0]

                if additional_mission_items[0]:
                    for item in additional_mission_items[0]:
                        db.execute(
                            query="INSERT INTO ad_mission_card "
                                  "(ad_id, mission_type, mission_name, additional_point, due_date, "
                                  "from_default_order, from_default_order_date) "
                                  "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            args=[register_id['ad_id'], item['mission_type'],
                                  item["mission_name"], item["additional_point"],
                                  item["due_date"], item["from_default_order"], item['from_default_order_date']
                                  ]
                        )
                    kwargs['additional_mission_items'] = additional_mission_items[0]
                db.commit()
                kwargs['ad_images'] = db.executeAll(
                    query="SELECT image FROM ad_images WHERE ad_id = %s",
                    args=register_id['ad_id']
                )
                kwargs['ad_id'] = register_id['ad_id']
                kwargs['side_image'] = save_to_db_dict['side_image']
                kwargs['back_image'] = save_to_db_dict['back_image']
                kwargs['thumbnail_image'] = save_to_db_dict['thumbnail_image']
                kwargs['activity_period'] = int(kwargs['activity_period'])
                kwargs['gender'] = int(kwargs['gender'])
                kwargs['max_age_group'] = int(kwargs['max_age_group'])
                kwargs['max_recruiting_count'] = int(kwargs['max_recruiting_count'])
                kwargs['min_age_group'] = int(kwargs['min_age_group'])
                kwargs['min_distance'] = int(kwargs['min_distance'])
                kwargs['total_point'] = int(kwargs['total_point'])
                return kwargs
            else:
                return False
        else:
            value_list.append(kwargs.get('ad_id'))
            db.execute(
                query="UPDATE ad_information "
                      "SET owner_name = %s, title = %s, recruit_start_date = %s, recruit_end_date = %s, "
                      "activity_period = %s, max_recruiting_count = %s, total_point = %s, day_point = %s, "
                      "area = %s, description = %s, min_distance = %s, gender = %s, "
                      "min_age_group = %s, max_age_group = %s, side_length = %s, side_width = %s, "
                      "back_length = %s, back_width = %s "
                      "WHERE ad_id = %s",
                args=value_list
            )
            save_to_db_dict = {}
            save_to_db_list = []
            directory = f"{BASE_IMAGE_LOCATION}/{kwargs.get('ad_id')}"
            os.makedirs(directory, exist_ok=True)
            for key, val in other_images.items():
                val.save(directory + "/" + secure_filename(val.filename))
                save_to_db_dict.setdefault(key,
                                           f"{AD_IMAGE_HOST}/{kwargs.get('ad_id')}/" + secure_filename(val.filename))
            for image in ad_images:
                image.save(directory + "/" + secure_filename(image.filename))
                value = f"{AD_IMAGE_HOST}/{kwargs.get('ad_id')}/{secure_filename(image.filename)}"
                save_to_db_list.append(value)
            db.execute(
                query="DELETE FROM ad_images WHERE ad_id = %s",
                args=kwargs.get('ad_id')
            )
            db.execute(
                query="UPDATE ad_information "
                      "SET thumbnail_image = %s, side_image = %s, back_image = %s "
                      "WHERE ad_id = %s",
                args=[save_to_db_dict['thumbnail_image'],
                      save_to_db_dict['side_image'],
                      save_to_db_dict['back_image'],
                      kwargs.get('ad_id')
                      ]
            )
            for i in range(len(save_to_db_list)):
                db.execute(
                    query="INSERT INTO ad_images (ad_id, image) VALUES (%s, %s)",
                    args=[kwargs.get('ad_id'), save_to_db_list[i]]
                )

            db.commit()
            kwargs['ad_images'] = db.executeAll(
                query="SELECT image FROM ad_images WHERE ad_id = %s",
                args=kwargs.get('ad_id')
            )
            kwargs['side_image'] = save_to_db_dict['side_image']
            kwargs['back_image'] = save_to_db_dict['back_image']
            kwargs['thumbnail_image'] = save_to_db_dict['thumbnail_image']
            kwargs['activity_period'] = int(kwargs['activity_period'])
            kwargs['gender'] = int(kwargs['gender'])
            kwargs['max_age_group'] = int(kwargs['max_age_group'])
            kwargs['max_recruiting_count'] = int(kwargs['max_recruiting_count'])
            kwargs['min_age_group'] = int(kwargs['min_age_group'])
            kwargs['min_distance'] = int(kwargs['min_distance'])
            kwargs['total_point'] = int(kwargs['total_point'])
            return kwargs
    else:
        apply_information = db.executeOne(
            query="SELECT ad_user_apply_id FROM ad_user_apply WHERE ad_id = %s AND status IN ('stand_by', 'accept')",
            args=kwargs.get('ad_id')
        )

        if apply_information:
            return False
        else:
            db.execute(
                query="UPDATE ad_information SET removed = 1, removed_time = NOW() WHERE ad_id = %s",
                args=kwargs.get('ad_id')
            )
            db.commit()
            return True


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

    sql = "SELECT ad_id, title, thumbnail_image, " \
          "max_recruiting_count, recruiting_count, total_point, area," \
          "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
          "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date " \
          f"FROM ad_information WHERE {sql_parameter_val} AND removed = 0 " \
          "LIMIT %s OFFSET %s"

    result = db.executeAll(query=sql, args=[start_at, per_page])
    return result, status


# 광고 디테일
def get_ad_information_by_id(ad_id):
    db = Database()
    result = db.getOneAdByAdId(ad_id)
    ad_image = db.getAllAdImageById(ad_id=ad_id)
    result["images"] = ad_image
    return result


# 광고신청 창 GET
def get_information_for_ad_apply(user_id, ad_id):
    db = Database()
    status = {"ad_information": True, "user_information": True}
    ad_information = db.executeOne(
        query="SELECT ad_id, thumbnail_image, title, total_point "
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
    status = {"user_information": True, "ad_information": True, "already_apply": True, "area": True}
    target_user = db.getUserById(user_id)
    target_ad = db.getOneAdApplyByAdId(ad_id)
    already_apply_ad = db.executeOne(
        query="SELECT ad_user_apply_id FROM ad_user_apply WHERE status in ('stand_by', 'accept') and user_id = %s",
        args=user_id
    )
    area = kwargs['main_address'].split(' ')[0]
    query = "SELECT ad_id, title FROM ad_information WHERE area LIKE '%%{0}%%'".format(area)
    non_delivery_area = db.executeOne(
        query=query
    )

    if not target_ad:
        status["ad_information"] = False
        return status

    elif not target_user:
        status["user_information"] = False
        return status

    elif already_apply_ad:
        status["already_apply"] = False
        return status

    elif not non_delivery_area:
        status['area'] = False
        return status

    else:
        db.execute(
            query="UPDATE user SET main_address = %s, "
                  "detail_address = %s, call_number = %s, name = %s "
                  "WHERE user_id = %s",
            args=[kwargs['main_address'], kwargs['detail_address'], kwargs['call_number'], kwargs['name'], user_id]
        )
        db.execute(
            query="INSERT INTO ad_user_apply (user_id, ad_id, recurit_number,register_time) VALUES (%s, %s, %s, NOW())",
            args=[user_id, ad_id, int(target_ad['recruiting_count']) + 1]
        )
        db.execute(
            query="UPDATE ad_information SET recruiting_count = recruiting_count + 1 WHERE ad_id = %s",
            args=ad_id
        )
        history_name = f"{non_delivery_area['title']} 광고 신청"
        db.execute(
            query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
            args=[user_id, history_name]
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


# 메인화면 본인이 진행중인 광고 카드의 정보 order 와 ad_mission_card_user_id,
def get_ongoing_user_by_id(user_id):
    db = Database()
    ad_information = db.getMainMyAd(user_id=user_id)
    vehicle_information = db.getAllVehicleByUserId(user_id=user_id)
    result = {"ad_information": ad_information, "vehicle_information": vehicle_information, "is_delete": True}
    if not ad_information:
        result = {"ad_information": {}, "vehicle_information": vehicle_information}
        return result
    order_information = db.executeOne(
        query="SELECT `order` FROM ad_mission_card WHERe ad_mission_card_id = %s",
        args=ad_information['ad_mission_card_id']
    )
    ad_information['order'] = order_information['order']
    if not ad_information["mission_status"]:
        ad_information["mission_status"] = ""
        ad_information["ad_mission_card_id"] = 0
        ad_information["mission_type"] = 0
        ad_information['activity_start_date'] = ''
        ad_information['activity_end_date'] = ''
        ad_information['ongoing_day_percent'] = 0
        return result
    elif ad_information["mission_status"]:
        if ad_information['activity_start_date'] == '0000-00-00 00:00:00':
            ad_information['point'] = 0
            ad_information['ongoing_day_percent'] = 0
            ad_information['activity_start_date'] = ''
            ad_information['activity_end_date'] = ''
        else:
            start_date = datetime.strptime(ad_information['activity_start_date'].split(' ')[0], '%Y-%m-%d')
            if (datetime.now().date() - start_date.date()).days > 0:
                ad_information['point'] = (datetime.now().date() - start_date.date()).days * ad_information['point']
            else:
                ad_information['point'] = ad_information['point']

            ad_information['ongoing_day_percent'] = int(datetime.now().hour/24*100)

        # if datetime.strptime(ad_information["apply_register_time"], '%Y-%m-%d %H:%M:%S') + timedelta(
        #         hours=1) < datetime.now():
        #     result["is_delete"] = False
        #     return result
        return result


# 신청한 광고 취소 (사용자)
def cancel_apply_user(ad_user_apply_id):
    db = Database()
    status = {"apply_information": True, "time_out": True}
    user_apply_information = db.executeOne(
        query="SELECT * FROM ad_user_apply WHERE ad_user_apply_id = %s",
        args=ad_user_apply_id
    )
    if not user_apply_information:
        status["apply_information"] = False
        return status

    #if user_apply_information["register_time"] + timedelta(hours=1) < datetime.now():
    #    status["time_out"] = False
    #    return status
    ad_information = db.executeOne(
        query="SELECT title, user_id FROM ad_information as ai JOIN ad_user_apply aua on ai.ad_id = aua.ad_id "
              "WHERE ad_user_apply_id = %s",
        args=ad_user_apply_id
    )
    history_name = f"{ad_information['title']} 광고 신청 취소"
    db.execute(
        query="DELETE FROM ad_user_apply WHERE ad_user_apply_id = %s",
        args=ad_user_apply_id
    )
    db.execute(
        query="UPDATE ad_information SET recruiting_count = recruiting_count - 1 WHERE ad_id = %s",
        args=user_apply_information["ad_id"]
    )

    db.execute(
        query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
        args=[ad_information['user_id'], history_name]
    )
    db.commit()
    return status


# 광고 status 변경
def update_ad_apply_status(ad_user_apply_id, **kwargs):
    db = Database()
    apply_information = {"rejected": True, "accept": True, "mission_data": True}
    apply_status = db.getOneApplyStatus(ad_user_apply_id=ad_user_apply_id)
    if apply_status["status"] == "reject" and kwargs["status"] == "reject":
        apply_information["rejected"] = False
        return apply_information

    elif apply_status["status"] == "accept" and kwargs["status"] == "accept":
        apply_information["accept"] = False
        return apply_information

    else:
        if kwargs["status"] == "reject":
            history_name = f"{apply_status['title']} 광고 신청 거부"
            # ad_user_apply 테이블에서 ad_id 가 같은 ad_information 테이블에서 모집인원 -1 (ad_user_apply_id)에 맞는 데이터
            db.execute(
                query="UPDATE ad_information as ad_info "
                      "JOIN ad_user_apply aua on ad_info.ad_id = aua.ad_id "
                      "SET ad_info.recruiting_count = ad_info.recruiting_count - 1 "
                      "WHERE aua.ad_user_apply_id = %s",
                args=ad_user_apply_id
            )
            db.execute(
                query="UPDATE ad_user_apply SET status = %s WHERE ad_user_apply_id = %s",
                args=[kwargs['status'], ad_user_apply_id]
            )
            db.execute(
                query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                args=[apply_status['user_id'], history_name]
            )

        elif kwargs["status"] == "accept":
            mission_items = db.getAllAdMissionCardInfoByAcceptApply(ad_user_apply_id=ad_user_apply_id)
            if mission_items:
                for mission in mission_items:
                    first_start_date = date.today() + timedelta(days=2)
                    # 필수미션 1회차 일 경우
                    if mission["order"] == 1 and mission["mission_type"] == 0:
                        first_end_date = first_start_date + timedelta(days=(int(mission["due_date"])))
                        db.execute(
                            query="INSERT INTO ad_mission_card_user "
                                  "(ad_user_apply_id, ad_mission_card_id, "
                                  "mission_type, status, mission_start_date, mission_end_date) "
                                  "VALUES (%s, %s, %s, %s, %s, %s)",
                            args=[ad_user_apply_id, mission["ad_mission_card_id"], mission["mission_type"],
                                  "ongoing", first_start_date.strftime('%Y-%m-%d 00:00:00'),
                                  first_end_date.strftime('%Y-%m-%d 23:59:59')]
                        )
                    # 필수미션 n회차 일 경우 (1제외)
                    elif mission["order"] != 1 and mission["mission_type"] == 0:
                        start_date = first_start_date + timedelta(days=mission["based_on_activity_period"])
                        end_date = start_date + timedelta(days=mission["due_date"])
                        db.execute(
                            query="INSERT INTO ad_mission_card_user "
                                  "(ad_user_apply_id, ad_mission_card_id, "
                                  "mission_type, status, mission_start_date, mission_end_date) "
                                  "VALUES (%s, %s, %s, %s, %s, %s)",
                            args=[ad_user_apply_id, mission["ad_mission_card_id"], mission["mission_type"],
                                  "stand_by", start_date.strftime('%Y-%m-%d 00:00:00'),
                                  end_date.strftime('%Y-%m-%d 23:59:59')]
                        )
                    # 선택미션 일 경우(우선 활동시작 기간이 필수미션 1회 완료 후 이기때문에 0000-00-00 으로 (필수미션1회 후 시간정해짐)
                    else:
                        db.execute(
                            query="INSERT INTO ad_mission_card_user "
                                  "(ad_user_apply_id, ad_mission_card_id, "
                                  "mission_type, status) "
                                  "VALUES (%s, %s, %s, %s)",
                            args=[ad_user_apply_id, mission["ad_mission_card_id"], mission["mission_type"],
                                  "stand_by", ]
                        )
                db.execute(
                    query="UPDATE ad_user_apply SET status = %s, accept_status_time = NOW() WHERE ad_user_apply_id = %s",
                    args=[kwargs['status'], ad_user_apply_id]
                )
                history_name = f"{apply_status['title']} 광고 신청 승인"
                db.execute(
                    query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
                    args=[apply_status['user_id'], history_name]
                )
                db.commit()
        else:
            apply_information["mission_data"] = False
            return apply_information

        ad_mission_card_user_info = db.executeAll(
            query="SELECT ad_mission_card_user_id FROM ad_mission_card_user as amcu "
                  "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
                  "WHERE aua.ad_user_apply_id = %s",
            args=ad_user_apply_id
        )
        for i in range(len(ad_mission_card_user_info)):
            db.execute(
                query="INSERT INTO "
                      "mission_images (ad_mission_card_user_id) "
                      "VALUES "
                      "(%s)",
                args=ad_mission_card_user_info[i]["ad_mission_card_user_id"]
            )
        db.commit()
        return apply_information
