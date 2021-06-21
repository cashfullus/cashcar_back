from database.dbConnection import Database
import datetime


# Datetime to String
def datetime_to_str(time):
    return time.strftime('%Y-%m-%d %H:%M:%S')


# 차량 등록 supporters 걸러내기
def register_vehicle(**kwargs):
    db = Database()
    result = {"user": True, "register": True, "double_check_number": True}
    # 계정유무 확인
    user = db.getUserById(kwargs.get("user_id"))
    if not user:
        result["user"] = False
        db.db_close()
        return result

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
        db.db_close()
        return result

    # 차량 번호 중복 확인
    elif check_vehicle_number:
        result["double_check_number"] = False
        db.db_close()
        return result

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

    # INSERT
    sql = "INSERT INTO vehicle " \
          "(user_id, supporters, is_foreign_car, brand, vehicle_model_name, year, car_number, owner_relationship) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    db.execute(query=sql, args=value_list)
    db.commit()
    result["vehicle_information"] = kwargs
    db.db_close()
    return result


class Vehicle:
    def __init__(self):
        self._user_id = None
        self._vehicle_id = None
        self.update_result = {"target_vehicle": True, "double_check_number": True}
        self.db = Database()

    @property
    def user_id(self):
        return self._user_id

    @property
    def vehicle_id(self):
        return self._vehicle_id

    @user_id.setter
    def user_id(self, user_id):
        self._user_id = user_id

    @vehicle_id.setter
    def vehicle_id(self, vehicle_id):
        self._vehicle_id = vehicle_id

    def get_vehicle_all_by_user_id(self):
        return self.db.getAllVehicleByUserId(user_id=self._user_id)

    def get_vehicle_one_by_vehicle_user_id(self):
        return self.db.getOneVehicleByVehicleIdAndUserId(user_id=self._user_id, vehicle_id=self._vehicle_id)

    def get_supporters(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE user_id = %s AND vehicle_id = %s AND status IN ('stand_by', 'accept')",
            args=[self._user_id, self._vehicle_id]
        )


class VehicleList(Vehicle):
    def set_is_delete(self):
        vehicle_list = self.get_vehicle_all_by_user_id()
        if vehicle_list:
            for i in range(len(vehicle_list)):
                self.vehicle_id = vehicle_list[i]['vehicle_id']
                is_supporters = self.get_supporters()
                if is_supporters:
                    vehicle_list[i]['is_delete'] = False
                else:
                    vehicle_list[i]['is_delete'] = True
        return vehicle_list

    def response(self, user_id):
        self.user_id = user_id
        response_data = self.set_is_delete()
        self.db.db_close()
        return response_data


class VehicleDetail(Vehicle):
    def set_is_delete(self):
        vehicle = self.get_vehicle()
        if vehicle:
            is_delete = self.get_is_delete_vehicle()
            if is_delete:
                vehicle['is_delete'] = False
            else:
                vehicle['is_delete'] = True
        return vehicle

    def get_vehicle(self):
        return self.db.getOneVehicleByVehicleIdAndUserId(
            vehicle_id=self._vehicle_id,
            user_id=self.user_id
        )

    def get_is_delete_vehicle(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE user_id = %s AND vehicle_id = %s AND status IN ('stand_by', 'accept')",
            args=[self.user_id, self.vehicle_id]
        )

    def response(self, user_id, vehicle_id):
        self.user_id = user_id
        self.vehicle_id = vehicle_id
        response_data = self.set_is_delete()
        self.db.db_close()
        return response_data


class VehicleUpdate(Vehicle):
    def __init__(self, **data):
        super().__init__()
        self.data = data

    def double_check(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM vehicle WHERE vehicle_id NOT IN (%s) AND car_number = %s AND removed = 0",
            args=[self.vehicle_id, self.data.get('car_number')]
        )

    def is_supporters(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE user_id = %s AND vehicle_id = %s AND status IN ('stand_by', 'accept')",
            args=[self.user_id, self.vehicle_id]
        )

    def is_valid(self):
        double_check = self.double_check()
        is_supporters = self.is_supporters()
        if double_check:
            self.update_result['double_check_number'] = False
            return False

        if is_supporters:
            self.update_result['target_vehicle'] = False
            return False
        return True

    def is_valid_supporters(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply WHERE user_id = %s AND status IN ('stand_by', 'accept')",
            args=self.user_id
        )

    def update_supporters(self):
        self.db.execute(
            query="UPDATE vehicle SET supporters = 0 WHERE user_id = %s",
            args=self.user_id
        )
        self.db.commit()

    def update_information(self):
        self.db.execute(
            query="UPDATE vehicle SET "
                  "supporters = %s, is_foreign_car = %s, brand = %s, "
                  "vehicle_model_name = %s, year = %s, car_number = %s, owner_relationship = %s "
                  "WHERE vehicle_id = %s AND user_id = %s",
            args=[self.data.get('supporters'), self.data.get('is_foreign_car'), self.data.get('brand'),
                  self.data.get('vehicle_model_name'), self.data.get('year'), self.data.get('car_number'),
                  self.data.get('owner_relationship'), self.vehicle_id, self.user_id
                  ]
        )
        self.db.commit()

    def update(self):
        # 유효한 데이터 검사
        if self.is_valid():
            # 서포터즈 차량으로 변경시
            if self.data.get('supporters') == 1:
                # 만약 서포터즈를 진행중인 차량이 있을시 서포터즈 차량선택 불가
                if self.is_valid_supporters():
                    self.data['supporters'] = 0
                # 진행중인 서포터즈 차량이 없을시 다른 차량 서포터즈 해제 후 업데이트 진행
                else:
                    self.update_supporters()
            # 차량 정보 업데이트
            self.update_information()

    def response(self, user_id, vehicle_id):
        self.user_id = user_id
        self.vehicle_id = vehicle_id
        self.update()
        self.db.db_close()
        return self.update_result


class VehicleDelete(Vehicle):
    def is_valid(self):
        vehicle = self.get_vehicle_one_by_vehicle_user_id()
        if vehicle:
            if self.is_delete():
                return True
            return False
        return False

    def is_delete(self):
        if self.get_delete_vehicle():
            return False
        return True

    def get_delete_vehicle(self):
        return self.db.executeOne(
            query="SELECT vehicle_id FROM ad_user_apply "
                  "WHERE vehicle_id = %s AND user_id = %s AND status IN ('stand_by', 'accept')",
            args=[self.vehicle_id, self.user_id]
        )

    def delete_vehicle(self):
        self.db.execute(
            query="UPDATE vehicle SET removed = 1, remove_time = NOW() WHERE vehicle_id = %s AND user_id = %s",
            args=[self.vehicle_id, self.user_id]
        )
        self.db.commit()

    def response(self, user_id, vehicle_id):
        self.user_id = user_id
        self.vehicle_id = vehicle_id
        if self.is_valid():
            self.delete_vehicle()
            self.db.db_close()
            return True
        else:
            self.db.db_close()
            return False
