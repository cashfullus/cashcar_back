from database.dbConnection import Database
from notification.user_push_nofitication import one_cloud_messaging


def check_gender_filter(gender):
    if int(gender) == 0:
        where_gender = f"resident_registration_number_back IN ('',0, 1, 2)"
    else:
        where_gender = f"resident_registration_number_back IN ({gender})"
    return where_gender


def check_user_area_filter(area):
    where_area = []
    if type(area) == str:
        if area == "":
            where_area = "main_address LIKE '%%'"
        else:
            where_area = f"main_address LIKE '%%{area}%%'"
    else:
        for i in range(len(area)):
            if i + 1 != len(area):
                where_area.append(f"main_address LIKE '%%{area[i]}%%' OR ")
            else:
                where_area.append(f"main_address LIKE '%%{area[i]}%%'")
        where_area = "({0})".format(''.join(where_area))
    return where_area


def get_all_marketing_user(page, count, area, gender, register_time):
    per_page = (page - 1) * count
    db = Database()

    where_area = check_user_area_filter(area)
    where_gender = check_gender_filter(gender)
    where_register_time = f"(register_time >= '{register_time[0]}' AND register_time <= '{register_time[1]}')"

    query = "SELECT user_id, nickname, name, call_number, email, resident_registration_number_back as gender, age, " \
            "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time " \
            "FROM user " \
            f"WHERE marketing = 1 AND {where_area} AND {where_gender} AND {where_register_time} " \
            f"ORDER BY register_time DESC LIMIT %s OFFSET %s"
    value_list = [count, per_page]
    user_list = db.executeAll(query=query, args=value_list)
    vehicle_information = {"vehicle_model_name": "", "brand": "", "car_number": ""}
    if user_list:
        for i in range(len(user_list)):
            vehicle = db.executeOne(
                query="SELECT vehicle_model_name, brand, car_number FROM vehicle "
                      "WHERE user_id = %s ORDER BY supporters DESC",
                args=user_list[i]['user_id']

            )
            if vehicle:
                user_list[i]['vehicle_information'] = vehicle
            else:
                user_list[i]['vehicle_information'] = vehicle_information
    item_count = len(user_list)
    db.db_close()
    return user_list, item_count


# 사용자 앱푸시 전송
def user_app_push_notification(*user_list, **kwargs):
    db = Database()
    success_list = []
    fail_list = []
    alarm_history = []
    if user_list:
        kwargs.setdefault('transfer_count', len(user_list))
        insert_app_push_log_id = db.insertAppPushLogReturnId(**kwargs)['id']
        if len(user_list) == 1:
            fcm_list = db.getAllUserFcmToken(*user_list)
        else:
            fcm_list = db.getAllUserFcmToken(*user_list)
        sorted_user_list = sorted(user_list, key=lambda x: x)
        many_execute_value_arr_1 = [[sorted_user_list[i], int(insert_app_push_log_id)]
                                    for i in range(len(sorted_user_list))
                                    ]
        db.insertUserAppPushLog(many_value=many_execute_value_arr_1)
        for i in range(len(fcm_list)):
            result = one_cloud_messaging(token=fcm_list[i]['fcm_token'], body=kwargs.get('body'))
            if int(result['success']) == 1:
                user_id = fcm_list[i]['user_id']
                success_list.append(["success", user_id])
                alarm_history.append([user_id, "marketing", 0, kwargs.get('body')])
                continue
            else:
                fail_list.append(["fail", fcm_list[i]['user_id']])
        kwargs.setdefault('success_count', len(success_list))
        kwargs.setdefault('fail_count', len(fail_list))
        kwargs.setdefault('id', insert_app_push_log_id)
        many_execute_value_list = success_list + fail_list
        db.updateAppPushLog(**kwargs)
        db.updateUserAppPushLog(many_execute_value_list)
        db.updateAllAlarmHistoryByAppPush(alarm_history)
        db.db_close()
        return True
    db.db_close()
    return False


# notification 이력 리스트
def get_notification_list(page, count):
    db = Database()
    result, item_count = db.getAllNotificationListWithCount(page=page, count=count)
    db.db_close()
    return result, item_count


# 앱푸쉬 재전송
def app_push_re_transfer(user_id, app_push_id):
    db = Database()
    user_information = db.executeOne(
        query="SELECT fcm_token, user_id FROM user_fcm WHERE user_id = %s",
        args=user_id
    )
    app_push_information = db.executeOne(
        query="SELECT * FROM app_push_log WHERE id = %s",
        args=app_push_id
    )

    if user_information and app_push_information:
        push_result = one_cloud_messaging(token=user_information['fcm_token'],
                                          body=app_push_information['notification_body']
                                          )
        if push_result['success'] == 1:
            data = {"user_id": user_id, "description": app_push_information['notification_body']}
            db.updateOneSuccessAppPushLog(app_push_id=app_push_id, user_id=user_id)
            db.updateOneAlarmHistoryByAppPush(**data)
            db.db_close()
            return True
        else:
            db.db_close()
            return False
    db.db_close()
    return False


# app_push_id에 해당하는 사용자 리스트
def get_user_list_by_app_push_id(app_push_id, page, count):
    db = Database()
    per_page = (page-1) * count
    user_list = db.executeAll(
        query="SELECT uapl.user_id, name, call_number, "
              "resident_registration_number_back as gender, age, status, "
              "DATE_FORMAT(uapl.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, "
              "DATE_FORMAT(updated_time, '%%Y-%%m-%%d %%H:%%i:%%s') as updated_time "
              "FROM user u "
              "JOIN user_app_push_log uapl on u.user_id = uapl.user_id "
              "WHERE uapl.app_push_log_id = %s ORDER BY register_time DESC LIMIT %s OFFSET %s",
        args=[app_push_id, count, per_page]
    )
    vehicle_information = {"vehicle_model_name": "", "brand": "", "car_number": ""}
    item_count = len(user_list)
    if user_list:
        for i in range(len(user_list)):
            vehicle = db.executeOne(
                query="SELECT vehicle_model_name, brand, car_number FROM vehicle "
                      "WHERE user_id = %s ORDER BY supporters DESC",
                args=user_list[i]['user_id']

            )
            if vehicle:
                user_list[i]['vehicle_information'] = vehicle
            else:
                user_list[i]['vehicle_information'] = vehicle_information
        db.db_close()
        return user_list, item_count
    db.db_close()
    return user_list, item_count
