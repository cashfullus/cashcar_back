from database.dbConnection import Database


def check_gender_filter(gender):
    if int(gender) == 0:
        where_gender = f"resident_registration_number_back IN (0, 1, 2)"
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
    per_page = (page-1) * count
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
    vehicle_information = {"vehicle_model": "", "brand": "", "car_number": ""}
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
    return user_list, item_count




