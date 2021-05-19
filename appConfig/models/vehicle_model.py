from database.dbConnection import Database
import datetime


# Datetime to String
def datetime_to_str(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')


# 차량 등록 supporters 걸러내기
def register_vehicle(**kwargs):
    db = Database()
    result = {"user": True, "register": True, "double_check_number": True}
    fcm_token = db.getOneFcmToken(user_id=kwargs['user_id'])
    # 계정유무 확인
    user = db.getUserById(kwargs.get("user_id"))
    if not user:
        result["user"] = False
        fcm_token = ""
        return result, fcm_token

    # 본인이 등록한 차량 수 조회
    counter_register_vehicle = db.executeOne(
        query="SELECT COUNT(*) as cnt FROM vehicle WHERE user_id = %s AND removed = 0",
        args=kwargs.get("user_id")
    )

    # 차량 번호 유무 확인
    check_vehicle_number = db.executeOne(
        query="SELECT car_number FROM vehicle WHERE car_number = %s AND removed = 0",
        args=kwargs.get("car_number")
    )
    # 최대 허용 등록 개수 3개
    if counter_register_vehicle["cnt"] >= 3:
        result["register"] = False
        fcm_token = ""
        return result, fcm_token

    # 차량 번호 중복 확인
    elif check_vehicle_number:
        result["double_check_number"] = False
        fcm_token = ""
        return result, fcm_token

    else:
        pass
    # 현재 진행중인 광고가 있을경우에는 supporters 미선정
    check_apply = db.executeOne(
        query="SELECT * FROM ad_user_apply WHERE status IN('stand_by', 'accept') AND user_id = %s",
        args=kwargs['user_id']
    )
    all_vehicle = db.executeAll(
        query="SELECT vehicle_id FROM vehicle WHERE user_id = %s",
        args=kwargs['user_id']
    )
    if check_apply:
        kwargs['supporters'] = 0
        value_list = [kwargs['user_id'], kwargs['supporters'], kwargs['is_foreign_car'],
                      kwargs['brand'], kwargs['vehicle_model_name'],
                      kwargs['year'], kwargs['car_number'], kwargs['owner_relationship']]
    else:
        value_list = [kwargs['user_id'], kwargs['supporters'], kwargs['is_foreign_car'],
                      kwargs['brand'], kwargs['vehicle_model_name'],
                      kwargs['year'], kwargs['car_number'], kwargs['owner_relationship']]

        if all_vehicle:
            if int(kwargs['supporters']) == 1:
                for i in range(len(all_vehicle)):
                    db.execute(
                        query="UPDATE vehicle SET supporters = 0 WHERE vehicle_id = %s",
                        args=all_vehicle[i]['vehicle_id']
                    )

    # fcm_token get
    fcm_token = db.getOneFcmToken(user_id=kwargs['user_id'])
    # INSERT
    sql = "INSERT INTO vehicle " \
          "(user_id, supporters, is_foreign_car, brand, vehicle_model_name, year, car_number, owner_relationship) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    db.execute(query=sql, args=value_list)
    db.commit()
    result["vehicle_information"] = kwargs

    return result, fcm_token




# 사용자 ID로 등록한 차량 GET ALL    차량삭제 유무 확인
def vehicle_list_by_user_id(user_id):
    db = Database()
    vehicle_list = db.getAllVehicleByUserId(user_id)
    if vehicle_list:
        for i in range(len(vehicle_list)):
            is_supporters = db.executeOne(
                query="SELECT vehicle_id FROM ad_user_apply "
                      "WHERE user_id = %s AND vehicle_id = %s AND status IN ('stand_by', 'accept')",
                args=[user_id, vehicle_list[i]['vehicle_id']]
            )
            if is_supporters:
                vehicle_list[i]['is_delete'] = False
            else:
                vehicle_list[i]['is_delete'] = True
    return vehicle_list


# 차량의 ID 로 하나의 정보 조회
def vehicle_detail_by_id(user_id, vehicle_id):
    db = Database()
    target_vehicle = db.getOneVehicleByVehicleIdAndUserId(
        vehicle_id=vehicle_id,
        user_id=user_id
    )
    if target_vehicle:
        is_delete = db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE user_id = %s AND vehicle_id = %s AND status IN ('stand_by', 'accept')",
            args=[user_id, vehicle_id]
        )
        if is_delete:
            target_vehicle['is_delete'] = False
        else:
            target_vehicle['is_delete'] = True

    return target_vehicle


# 차량의 ID로 정보 업데이트
def vehicle_update_by_id(user_id, vehicle_id, **kwargs):
    db = Database()
    result = {"target_vehicle": True, "double_check_number": True}
    sql = "SELECT * FROM vehicle WHERE vehicle_id = %s AND user_id = %s AND removed = 0"
    target_vehicle = db.executeOne(
        query=sql,
        args=[vehicle_id, user_id]
    )

    sql = "SELECT * FROM vehicle WHERE vehicle_id not in (%s) AND car_number = %s AND removed = 0"
    double_check_data = db.executeOne(query=sql, args=[vehicle_id, kwargs.get('car_number')])
    if double_check_data:
        result["double_check_number"] = False
        return result

    # vehicle_id 와 user_id에 맞는 데이터가 존재한다면
    if target_vehicle:
        if kwargs.get('supporters') == 1:
            db.execute(
                query="UPDATE vehicle SET supporters = 0 WHERE user_id = %s",
                args=user_id
            )
            db.execute(
                query="UPDATE vehicle SET "
                      "supporters = %s, is_foreign_car = %s, brand = %s, "
                      "vehicle_model_name = %s, year = %s, car_number = %s, owner_relationship = %s "
                      "WHERE vehicle_id = %s AND user_id = %s",
                args=[kwargs['supporters'], kwargs['is_foreign_car'], kwargs['brand'],
                      kwargs['vehicle_model_name'], kwargs['year'], kwargs['car_number'], kwargs['owner_relationship'],
                      vehicle_id, user_id
                      ]
            )
            db.commit()
            return result
        else:
            # 업데이트 쿼리 진행
            sql = "UPDATE vehicle SET " \
                  "supporters = %s, is_foreign_car = %s, brand = %s, " \
                  "vehicle_model_name = %s, year = %s, car_number = %s, owner_relationship = %s " \
                  "WHERE vehicle_id = %s AND user_id = %s"
            value_list = [kwargs['supporters'], kwargs['is_foreign_car'], kwargs['brand'],
                          kwargs['vehicle_model_name'], kwargs['year'], kwargs['car_number'],
                          kwargs['owner_relationship'], vehicle_id, user_id
                          ]
            db.execute(query=sql, args=value_list)
            db.commit()

            return result
    # 차량 정보가 존재하지않다면 False
    else:
        result["target_vehicle"] = False
        return result


# 차량 ID로 차량 삭제 서포터즈 진행시 미삭제 불가
def vehicle_delete_by_id(vehicle_id, user_id):
    db = Database()
    sql = "SELECT * FROM vehicle WHERE vehicle_id = %s AND user_id = %s AND removed = 0"
    target_vehicle = db.executeOne(
        query=sql,
        args=[vehicle_id, user_id]
    )

    if target_vehicle:
        is_delete = db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE vehicle_id = %s AND user_id = %s AND status NOT IN ('success', 'fail')",
            args=[vehicle_id, user_id]
        )
        if is_delete:
            return False
        else:
            db.execute(
                query="UPDATE vehicle SET removed = 1, remove_time = NOW() WHERE vehicle_id = %s AND user_id = %s",
                args=[vehicle_id, user_id]
            )
            db.commit()
            return True

    else:
        return False




