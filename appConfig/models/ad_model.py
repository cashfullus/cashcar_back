from database.dbConnection import Database
from werkzeug.utils import secure_filename

from datetime import date, timedelta, datetime

from .filter_model import Filter

import os
from .user_model import saveAlarmHistory

BASE_IMAGE_LOCATION = os.getcwd() + "/static/image/adverting"
AD_IMAGE_HOST = "https://app.api.service.cashcarplus.com:50193/image/adverting"


def ad_insert_mission_card(**kwargs):
    db = Database()
    default_mission_items = kwargs['default_mission_items']
    additional_mission_items = kwargs['additional_mission_items']
    if default_mission_items[0]:
        for item in default_mission_items[0]:
            mission_name = f"{item['order']}차 미션"
            db.execute(
                query="INSERT INTO ad_mission_card "
                      "(ad_id, mission_type, mission_name,due_date, `order`, based_on_activity_period) "
                      "VALUES (%s, %s, %s, %s, %s, %s)",
                args=[kwargs.get('ad_id'), item['mission_type'], mission_name,
                      item['due_date'], item['order'], item['based_on_activity_period']]
            )

    if additional_mission_items[0]:
        for item in additional_mission_items[0]:
            db.execute(
                query="INSERT INTO ad_mission_card "
                      "(ad_id, mission_type, mission_name, additional_point, due_date, based_on_activity_period) "
                      "VALUES (%s, %s, %s, %s, %s, %s)",
                args=[kwargs.get('ad_id'), item['mission_type'],
                      item["mission_name"], item["additional_point"],
                      item["due_date"], item["based_on_activity_period"]
                      ]
            )
    db.commit()
    db.db_close()
    return default_mission_items[0], additional_mission_items[0]


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
                if ad_images:
                    for image in ad_images:
                        image.save(directory + "/" + secure_filename(image.filename))
                        value = f"{AD_IMAGE_HOST}/{register_id['ad_id']}/{secure_filename(image.filename)}"
                        save_to_db_list.append(value)

                    for i in range(len(save_to_db_list)):
                        db.execute(
                            query="INSERT INTO ad_images (ad_id, image) VALUES (%s, %s)",
                            args=[register_id['ad_id'], save_to_db_list[i]]
                        )
                db.execute(
                    query="UPDATE ad_information "
                          "SET logo_image = %s, thumbnail_image = %s, side_image = %s, back_image = %s "
                          "WHERE ad_id = %s",
                    args=[save_to_db_dict['logo_image'],
                          save_to_db_dict['thumbnail_image'],
                          save_to_db_dict['side_image'],
                          save_to_db_dict['back_image'],
                          register_id['ad_id']
                          ]
                )
                db.commit()
                kwargs['ad_id'] = register_id['ad_id']
                default, additional = ad_insert_mission_card(**kwargs)
                kwargs['ad_images'] = db.executeAll(
                    query="SELECT image FROM ad_images WHERE ad_id = %s",
                    args=register_id['ad_id']
                )
                kwargs['side_image'] = save_to_db_dict['side_image']
                kwargs['back_image'] = save_to_db_dict['back_image']
                kwargs['logo_image'] = save_to_db_dict['logo_image']
                kwargs['thumbnail_image'] = save_to_db_dict['thumbnail_image']
                kwargs['activity_period'] = int(kwargs['activity_period'])
                kwargs['gender'] = int(kwargs['gender'])
                kwargs['max_age_group'] = int(kwargs['max_age_group'])
                kwargs['max_recruiting_count'] = int(kwargs['max_recruiting_count'])
                kwargs['min_age_group'] = int(kwargs['min_age_group'])
                kwargs['min_distance'] = int(kwargs['min_distance'])
                kwargs['total_point'] = int(kwargs['total_point'])
                kwargs['default_mission_items'] = default
                kwargs['additional_mission_items'] = additional
                db.db_close()
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

            db.execute(
                query="DELETE FROM ad_images WHERE ad_id = %s",
                args=kwargs.get('ad_id')
            )
            db.execute(
                query="UPDATE ad_information "
                      "SET logo_image = %s, thumbnail_image = %s, side_image = %s, back_image = %s "
                      "WHERE ad_id = %s",
                args=[save_to_db_dict['logo_image'],
                      save_to_db_dict['thumbnail_image'],
                      save_to_db_dict['side_image'],
                      save_to_db_dict['back_image'],
                      kwargs.get('ad_id')
                      ]
            )
            if ad_images:
                for image in ad_images:
                    image.save(directory + "/" + secure_filename(image.filename))
                    value = f"{AD_IMAGE_HOST}/{kwargs.get('ad_id')}/{secure_filename(image.filename)}"
                    save_to_db_list.append(value)
                for i in range(len(save_to_db_list)):
                    db.execute(
                        query="INSERT INTO ad_images (ad_id, image) VALUES (%s, %s)",
                        args=[kwargs.get('ad_id'), save_to_db_list[i]]
                    )
            db.execute(query="DELETE FROM ad_mission_card WHERE ad_id = %s", args=kwargs.get('ad_id'))
            db.commit()
            default, additional = ad_insert_mission_card(**kwargs)
            kwargs['ad_images'] = db.executeAll(
                query="SELECT image FROM ad_images WHERE ad_id = %s",
                args=kwargs.get('ad_id')
            )
            db.db_close()
            kwargs['side_image'] = save_to_db_dict['side_image']
            kwargs['back_image'] = save_to_db_dict['back_image']
            kwargs['logo_image'] = save_to_db_dict['logo_image']
            kwargs['thumbnail_image'] = save_to_db_dict['thumbnail_image']
            kwargs['activity_period'] = int(kwargs['activity_period'])
            kwargs['gender'] = int(kwargs['gender'])
            kwargs['max_age_group'] = int(kwargs['max_age_group'])
            kwargs['max_recruiting_count'] = int(kwargs['max_recruiting_count'])
            kwargs['min_age_group'] = int(kwargs['min_age_group'])
            kwargs['min_distance'] = int(kwargs['min_distance'])
            kwargs['total_point'] = int(kwargs['total_point'])
            kwargs['default_mission_items'] = default
            kwargs['additional_mission_items'] = additional
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
            db.db_close()
            return True


class AdvertisementList(Filter):
    def __init__(self):
        super().__init__()
        self.db = Database()

    def get_all_by_category_ad_list(self, page, category):
        per_page = (page - 1) * 20
        start_at = per_page + 20
        status = {"correct_category": True}
        sql = "SELECT ad_id, title, thumbnail_image, " \
              "max_recruiting_count, recruiting_count, total_point, area," \
              "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
              "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date, " \
              "TIMESTAMPDIFF(day, DATE_FORMAT(NOW(), '%%Y-%%m-%%d %%H:%%i:%%s'), " \
              "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s')) as time_diff " \
              f"FROM ad_information WHERE ad_status = %s AND removed = 0 ORDER BY ad_id DESC " \
              "LIMIT %s OFFSET %s"

        result = self.db.executeAll(query=sql, args=[category, start_at, per_page])
        return result, status

    def get_ad_apply_list_filter(self, page, count, status, area, gender, age, register_time, search, search_type):
        self.apply_status = status
        self.area = area
        self.gender = gender
        self.age = age
        self.start_datetime = register_time.split('~')[0]
        self.end_datetime = register_time.split('~')[1]
        self.search = search
        self.search_type = search_type
        status_filter = self.get_apply_status()
        area_filter = self.get_area()
        gender_filter = self.get_gender()
        age_filter = self.get_age()
        register_time_filter = self.get_ad_apply_register_time()
        search_filter = self.get_ad_apply_search_query()
        per_page = (page - 1) * count
        result = self.db.executeAll(
            query="SELECT "
                  "title, owner_name, name, main_address, detail_address, "
                  "aua.recruit_number, max_recruiting_count, aua.status, "
                  "u.user_id, aua.ad_user_apply_id, call_number, email, "
                  "DATE_FORMAT(aua.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, "
                  "DATE_FORMAT(accept_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as accept_status_time "
                  "FROM ad_user_apply aua "
                  "JOIN ad_information ai on aua.ad_id = ai.ad_id "
                  "JOIN user u on aua.user_id = u.user_id "
                  f"WHERE {status_filter} AND {area_filter} AND {gender_filter} "
                  f"AND {age_filter} AND {register_time_filter} AND {search_filter} "
                  "ORDER BY FIELD(status, 'stand_by', 'accept', 'success', 'reject', 'fail'), aua.register_time DESC "
                  "LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        item_count = self.db.executeOne(
            query="SELECT "
                  "count(aua.ad_user_apply_id) as item_count "
                  "FROM ad_user_apply aua "
                  "JOIN ad_information ai on aua.ad_id = ai.ad_id "
                  "JOIN user u on aua.user_id = u.user_id "
                  f"WHERE {status_filter} AND {area_filter} AND {gender_filter} "
                  f"AND {age_filter} AND {register_time_filter} AND {search_filter} "
                  "ORDER BY FIELD(status, 'stand_by', 'accept', 'success', 'reject'), "
                  "aua.register_time DESC"
        )
        self.db.db_close()
        return result, item_count['item_count']


# 광고 디테일
def get_ad_information_by_id(ad_id):
    db = Database()
    result = db.getOneAdByAdId(ad_id)
    ad_image = db.getAllAdImageById(ad_id=ad_id)
    if result:
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


class UserAdApply:
    def __init__(self, user_id, ad_id, vehicle_id, **kwargs):
        self.db = Database()
        self.user_id = user_id
        self.ad_id = ad_id
        self.vehicle_id = vehicle_id
        self.kwargs = kwargs
        self.status = {"user_information": True, "ad_information": True, "already_apply": True,
                       "area": True, "vehicle": True, "reject_apply": True}
        self.status_bool_list = []
        self.user = self.set_user()
        self.advertisement = self.set_advertisement()
        self.vehicle = self.set_vehicle()
        self.already_apply = self.set_already_apply_advertisement()
        self.rejected_apply = self.set_rejected_apply()
        self.possible_area = self.set_possible_area()

    def set_status(self):
        if self.rejected_apply:
            self.status["reject_apply"] = False
            self.status_bool_list.append(False)

        if not self.advertisement:
            self.status["ad_information"] = False
            self.status_bool_list.append(False)

        elif not self.user:
            self.status["user_information"] = False
            self.status_bool_list.append(False)

        elif self.already_apply:
            self.status["already_apply"] = False
            self.status_bool_list.append(False)

        elif not self.possible_area:
            self.status["area"] = False
            self.status_bool_list.append(False)

        elif not self.vehicle:
            self.status['vehicle'] = False
            self.status_bool_list.append(False)

        else:
            self.update_done_advertisement()
            if False in self.status_bool_list:
                return

            self.update_user()
            self.insert_advertisement_apply()
            self.insert_activity_history()
            self.update_vehicle()

    def set_user(self):
        return self.db.getUserById(user_id=self.user_id)

    def set_advertisement(self):
        return self.db.getOneAdApplyByAdId(ad_id=self.ad_id)

    def set_vehicle(self):
        return self.db.getOneVehicleByVehicleIdAndUserId(user_id=self.user_id, vehicle_id=self.vehicle_id)

    def set_already_apply_advertisement(self):
        return self.db.executeOne(
            query="SELECT ad_user_apply_id FROM ad_user_apply WHERE status IN ('stand_by', 'accept') AND user_id = %s",
            args=self.user_id
        )

    def set_rejected_apply(self):
        return self.db.executeOne(
            query="SELECT ad_user_apply_id FROM ad_user_apply WHERE user_id = %s AND ad_id = %s",
            args=[self.user_id, self.ad_id]
        )

    def set_possible_area(self):
        area = self.kwargs['main_address'].split(' ')[0]
        query = "SELECT ad_id, title, max_recruiting_count, recruiting_count, ad_status FROM ad_information " \
                "WHERE area LIKE '%%{0}%%' AND ad_id = {1}".format(area, self.ad_id)
        return self.db.executeOne(
            query=query
        )

    def update_done_advertisement(self):
        if self.possible_area['recruiting_count'] == self.possible_area['max_recruiting_count']:
            self.db.execute(
                query="UPDATE ad_information SET ad_status = 'done' WHERE ad_id = %s",
                args=self.ad_id
            )
            self.db.commit()
            self.status['ad_information'] = False
            self.status_bool_list.append(False)
        else:
            if self.possible_area['recruiting_count'] + 1 == self.possible_area['max_recruiting_count']:
                self.db.execute(
                    query="UPDATE ad_information SET recruiting_count = recruiting_count + 1, ad_status = 'done' "
                          "WHERE ad_id = %s",
                    args=self.ad_id
                )
            else:
                self.db.execute(
                    query="UPDATE ad_information SET recruiting_count = recruiting_count + 1 WHERE ad_id = %s",
                    args=self.ad_id
                )
            self.db.commit()

    def update_user(self):
        self.db.execute(
            query="UPDATE user SET main_address = %s, detail_address = %s, "
                  "call_number = %s, name = %s "
                  "WHERE user_id = %s",
            args=[self.kwargs.get('main_address'), self.kwargs.get('detail_address'),
                  self.kwargs.get('call_number'), self.kwargs.get('name'), self.user_id
                  ]
        )

    def insert_advertisement_apply(self):
        self.db.execute(
            query="INSERT INTO ad_user_apply (user_id, ad_id, vehicle_id, recruit_number, register_time) "
                  "VALUES (%s, %s, %s, %s, NOW())",
            args=[self.user_id, self.ad_id, self.vehicle_id, self.advertisement['recruiting_count'] + 1]
        )

    def insert_activity_history(self):
        activity_history = f"{self.advertisement['title']} 광고 신청"
        self.db.execute(
            query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
            args=[self.user_id, activity_history]
        )

    def update_vehicle(self):
        self.db.execute(
            query="UPDATE vehicle SET supporters = 0 WHERE user_id = %s AND vehicle_id NOT IN (%s)",
            args=[self.user_id, self.vehicle_id]
        )
        self.db.execute(
            query="UPDATE vehicle SET supporters = 1 WHERE user_id = %s AND vehicle_id = %s",
            args=[self.user_id, self.vehicle_id]
        )

    def check_already_apply_advertisement(self):
        already_apply = self.db.executeOne(
            query="SELECT ad_user_apply_id FROM ad_user_apply WHERE user_id = %s AND ad_id = %s",
            args=[self.user_id, self.ad_id]
        )
        if already_apply:
            return False
        return True

    def response(self):
        check_already_apply = self.check_already_apply_advertisement()
        if check_already_apply is False:
            self.status["already_apply"] = False
            self.db.db_close()
            return self.status
        self.set_status()
        self.db.commit()
        self.db.db_close()
        return self.status


class UserMyAd:
    def __init__(self, user_id):
        self.db = Database()
        self.user_id = user_id
        self.result = {"ad_information": {
            "activity_end_date": "", "activity_start_date": "", "ad_id": -1,
            "ad_mission_card_id": -1, "ad_mission_card_user_id": -1, "ad_user_apply_id": -1,
            "additional_mission_success_count": -1, "apply_register_time": "",
            "apply_status": "", "default_mission_success_count": -1, "mission_end_date": "", "mission_status": "",
            "mission_type": -1, "ongoing_day_percent": -1, "ongoing_days": -1,
            "order": -1, "point": -1, "thumbnail_image": "", "title": "", "user_id": -1, "mission_name": ""
        }, "is_delete": True,
            "is_read_alarm": False,
            "vehicle_information": [],
            "message": {
                "is_additional_fail": 0,
                "is_read": -1,
                "reason": "",
                "reason_id": 0,
                "title": "",
                "message_type": ""
            }
        }

    def get_my_advertisement(self):
        return self.db.getMainMyAd(user_id=self.user_id)

    def get_vehicle_information(self):
        return self.db.getAllVehicleByUserId(user_id=self.user_id)

    def get_not_read_alarm(self):
        return self.db.executeOne(
            query="SELECT user_id FROM alarm_history WHERE is_read_alarm = 0 AND user_id = %s",
            args=self.user_id
        )

    def get_message(self):
        return self.db.getOneReason(user_id=self.user_id)

    @staticmethod
    def get_order_information(self, ad_mission_card_id):
        return self.db.executeOne(
            query="SELECT `order`, mission_name FROM ad_mission_card WHERE ad_mission_card_id = %s",
            args=ad_mission_card_id
        )

    def set_is_delete(self):
        self.result['is_delete'] = False

    def set_default_result(self):
        vehicle_information = self.get_vehicle_information()
        is_not_read_alarm = self.get_not_read_alarm()
        message = self.get_message()

        if vehicle_information:
            self.result["vehicle_information"] = vehicle_information

        if is_not_read_alarm:
            self.result["is_read_alarm"] = True

        if message:
            self.result["message"] = message

        my_ad = self.get_my_advertisement()
        if not my_ad:
            return 0, my_ad
        return 1, my_ad

    def set_null_value(self):
        allowed, ad_information = self.set_default_result()
        if allowed == 0:
            return

        # 미션에 대한 order
        if ad_information['ad_mission_card_user_id'] is not None:
            get_order = self.get_order_information(
                self, ad_mission_card_id=ad_information['ad_mission_card_id']
            )
            ad_information['order'] = get_order['order']
            ad_information['mission_name'] = get_order['mission_name']

        # 삭제여부
        if datetime.strptime(ad_information["apply_register_time"], '%Y-%m-%d %H:%M:%S') + timedelta(
                hours=1) < datetime.now():
            self.set_is_delete()

        # 활동시간에 따른 예외처리
        if ad_information['activity_start_date'] == '0000-00-00 00:00:00':
            ad_information['ongoing_days'] = 0
            ad_information['activity_start_date'] = ""
            ad_information['activity_end_date'] = ""
            ad_information['ongoing_day_percent'] = 0
            ad_information["point"] = 0
        else:
            start_date = datetime.strptime(ad_information['activity_start_date'].split(' ')[0], '%Y-%m-%d').date()
            ad_information['ongoing_days'] = (date.today() - start_date).days
            time_diff = ((date.today() + timedelta(days=1)) - start_date).days
            if time_diff > ad_information['activity_period']:
                time_diff = ad_information['activity_period']
            if (datetime.now().date() - start_date).days > 0:
                ad_information['point'] = time_diff * ad_information['point']
            day_diff = ((time_diff / ad_information['activity_period']) * 100)
            ad_information['ongoing_day_percent'] = int(day_diff)
            ad_information['ongoing_days'] = time_diff

        # 미션 상태에 따른 에외처리
        if not ad_information["mission_status"]:
            ad_information["mission_status"] = ""
            ad_information["mission_type"] = -1
            ad_information["ad_mission_card_id"] = -1
            ad_information["ad_mission_card_user_id"] = -1

        self.result['ad_information'] = ad_information

    def response(self):
        self.set_null_value()
        self.db.db_close()
        return self.result


class UserApplyCancel:
    def __init__(self, ad_user_apply_id):
        self.ad_user_apply_id = ad_user_apply_id
        self.db = Database()
        self.status = {"apply_information": True, "time_out": True}

    def check_status(self):
        apply_information = self.get_user_apply_information()
        if not apply_information:
            self.status['apply_information'] = False
            return False

        if apply_information['register_time'] + timedelta(hours=1) < datetime.now():
            self.status['time_out'] = False
            return False
        return True

    def get_user_apply_information(self):
        return self.db.executeOne(
            query="SELECT * FROM ad_user_apply WHERE ad_user_apply_id = %s",
            args=self.ad_user_apply_id
        )

    def get_ad_information(self):
        return self.db.executeOne(
            query="SELECT title, user_id, ai.ad_id FROM ad_information as ai "
                  "JOIN ad_user_apply aua on ai.ad_id = aua.ad_id "
                  "WHERE ad_user_apply_id = %s",
            args=self.ad_user_apply_id
        )

    def set_history_and_recruiting_count(self):
        adId_userId_information = self.get_ad_information()
        history_name = f"{adId_userId_information['title']} 광고 신청 취소"
        self.db.execute(
            query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
            args=[adId_userId_information['user_id'], history_name]
        )
        self.db.execute(
            query="UPDATE ad_information SET recruiting_count = recruiting_count - 1 WHERE ad_id = %s",
            args=adId_userId_information['ad_id']
        )
        self.db.commit()

    def delete_apply_information(self):
        self.db.execute(
            query="DELETE FROM ad_user_apply WHERE ad_user_apply_id = %s",
            args=self.ad_user_apply_id
        )
        self.db.commit()

    def delete_apply_information_v1(self):
        self.db.execute(
            query="UPDATE ad_user_apply SET status = 'cancel' WHERE ad_user_apply_id = %s",
            args=self.ad_user_apply_id
        )
        self.db.commit()

    def response(self):
        check_status = self.check_status()
        if check_status is False:
            self.db.db_close()
            return self.status
        else:
            self.set_history_and_recruiting_count()
            self.delete_apply_information()
            self.db.db_close()
            return self.status


class AdApplyStatusUpdate:
    def __init__(self, **kwargs):
        self.start_date = date.today()
        self.kwargs = kwargs
        self.apply_user_list = kwargs['apply_user_list']
        self.db = Database()
        self.apply_information = None
        self.apply_status = None
        self.apply_id = None
        self.mission_item = None
        self.item = None
        self.user_fcm_list = []
        self.apply_information = {"rejected": True, "accept": True, "apply_data": True}

    def insert_mission_card_user_information(self):
        ad_mission_card_user_info = self.db.executeAll(
            query="SELECT ad_mission_card_user_id FROM ad_mission_card_user as amcu "
                  "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
                  "WHERE aua.ad_user_apply_id = %s",
            args=self.apply_id
        )
        ad_mission_card_id_list = [info['ad_mission_card_user_id'] for info in ad_mission_card_user_info]
        self.db.executemany(
            query="INSERT INTO mission_images (ad_mission_card_user_id) VALUES (%s)",
            args=ad_mission_card_id_list
        )
        self.db.commit()

    def insert_history(self):
        history_name = f"{self.apply_status['title']} 광고 신청 승인"
        self.db.execute(
            query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
            args=[self.apply_status['user_id'], history_name]
        )
        user_info = self.db.getOneFcmToken(user_id=self.apply_status['user_id'])
        if user_info['alarm'] == 1:
            self.user_fcm_list.append(user_info['fcm_token'])
            saveAlarmHistory(user_id=self.apply_status['user_id'], alarm_type="apply",
                             required=1, description="서포터즈 신청이 승인되었습니다. 스티커를 받은 후 1차 미션을 인증해주세요!"
                             )
        self.db.commit()

    def update_apply_status(self):
        self.db.execute(query="UPDATE ad_user_apply SET status = %s, accept_status_time = NOW() "
                              "WHERE ad_user_apply_id = %s",
                        args=[self.kwargs['status'], self.apply_id]
                        )
        self.db.commit()

    def check_status(self):
        status = self.apply_status['status']
        apply_status = self.kwargs['status']
        if status == 'accept' and apply_status == "accept":
            self.apply_information["accept"] = False

        if status == 'reject' and apply_status == 'reject':
            self.apply_information["rejected"] = False

        if status in ('accept', 'reject', 'success'):
            self.apply_information['accept'] = False
            self.apply_information['rejected'] = False

        if (status == "accept" and apply_status == "reject") or (status == "reject" and apply_status == "accept"):
            self.apply_information['accept'] = False
            self.apply_information['rejected'] = False

    def set_mission_item(self):
        self.mission_item = self.db.getAllAdMissionCardInfoByAcceptApply(ad_user_apply_id=self.apply_id)

    def default_mission(self):
        query = "INSERT INTO ad_mission_card_user (ad_user_apply_id, ad_mission_card_id, mission_type, " \
                "status, mission_start_date, mission_end_date) " \
                f"VALUES (%s, %s, %s, %s, %s, %s)"
        if self.item['order'] == 1 and self.item['mission_type'] == 0:
            end_date = (self.start_date + timedelta(days=self.item["due_date"])).strftime('%Y-%m-%d 23:59:59')
            self.db.execute(
                query=query,
                args=[self.apply_id, self.item["ad_mission_card_id"], self.item["mission_type"],
                      "ongoing", self.start_date.strftime('%Y-%m-%d 00:00:00'), end_date
                      ]
            )
        elif self.item['order'] != 1 and self.item['mission_type'] == 0 and self.item['based_on_activity_period'] != 0:
            start_date = date.today() + timedelta(days=self.item['based_on_activity_period'])
            end_date = (start_date + timedelta(days=self.item['due_date'])).strftime('%Y-%m-%d 23:59:59')
            self.db.execute(
                query=query,
                args=[self.apply_id, self.item["ad_mission_card_id"], self.item["mission_type"],
                      "stand_by", start_date.strftime('%Y-%m-%d 00:00:00'), end_date
                      ]
            )
        elif self.item['order'] != 1 and self.item['mission_type'] == 0 and self.item['based_on_activity_period'] == 0:
            start_date = date.today() + timedelta(days=self.item['based_on_activity_period'])
            end_date = (start_date + timedelta(days=self.item['due_date'])).strftime('%Y-%m-%d 23:59:59')
            self.db.execute(
                query=query,
                args=[self.apply_id, self.item["ad_mission_card_id"], self.item["mission_type"],
                      "ongoing", start_date.strftime('%Y-%m-%d 00:00:00'), end_date
                      ]
            )
        else:
            self.db.commit()
            self.additional_mission()

    def additional_mission(self):
        # 미션 아이템
        mission_start_date = (date.today() + timedelta(days=self.item['based_on_activity_period']))
        mission_end_date = (mission_start_date + timedelta(days=self.item['due_date'])).strftime(
            '%Y-%m-%d 23:59:59')
        if date.today() == mission_start_date:
            mission_status = "ongoing"
        else:
            mission_status = "stand_by"
        self.db.execute(
            query="INSERT INTO ad_mission_card_user "
                  "(ad_user_apply_id, ad_mission_card_id, "
                  "mission_type, status, mission_start_date, mission_end_date) "
                  "VALUES (%s, %s, %s, %s, %s, %s)",
            args=[self.apply_id, self.item["ad_mission_card_id"], self.item["mission_type"],
                  mission_status, mission_start_date, mission_end_date]
        )
        self.db.commit()

    def apply_reject(self):
        if int(self.apply_status['max_recruiting_count'] == int(self.apply_status['recruiting_count'])):
            self.db.execute(
                query="UPDATE ad_information as ad_info "
                      "JOIN ad_user_apply aua on ad_info.ad_id = aua.ad_id "
                      "SET ad_info.recruiting_count = ad_info.recruiting_count - 1, ad_status = 'ongoing' "
                      "WHERE aua.ad_user_apply_id = %s",
                args=self.apply_id
            )
        else:
            self.db.execute(
                query="UPDATE ad_information as ad_info "
                      "JOIN ad_user_apply aua on ad_info.ad_id = aua.ad_id "
                      "SET ad_info.recruiting_count = ad_info.recruiting_count - 1 "
                      "WHERE aua.ad_user_apply_id = %s",
                args=self.apply_id
            )
        history_name = f"{self.apply_status['title']} 광고 신청 거부"
        # 광고 신청 실패시 토스트 메세지 추가
        title = "서포터즈 신청에 실패하였습니다:("
        reason = "브랜드가 제안한 조건에 맞지 않아 안타깝게도 서포터즈 신청에 실패하였습니다. 다음기회에 다시 신청해주세요!"
        self.db.execute(
            query="UPDATE ad_user_apply SET status = %s, reject_status_time = NOW() "
                  "WHERE ad_user_apply_id = %s",
            args=[self.kwargs['status'], self.apply_id]
        )
        self.db.execute(
            query="UPDATE ad_user_apply "
                  "SET recruit_number = recruit_number - 1 "
                  "WHERE ad_user_apply_id NOT IN (%s) AND status IN ('stand_by', 'accept', 'success') "
                  "AND ad_id = %s AND recruit_number > %s",
            args=[self.apply_id, self.apply_status["ad_id"], self.apply_status['recruit_number']]
        )
        self.db.execute(
            query="INSERT INTO user_activity_history (user_id, history_name) VALUES (%s, %s)",
            args=[self.apply_status['user_id'], history_name]
        )
        self.db.execute(
            query="INSERT INTO ad_mission_reason (ad_user_apply_id, reason, title, is_read, message_type) "
                  "VALUE (%s, %s, %s, %s, %s)",
            args=[self.apply_id, reason, title, 0, "apply_reject"]
        )
        user_info = self.db.getOneFcmToken(user_id=self.apply_status['user_id'])
        if user_info['alarm'] == 1:
            self.user_fcm_list.append(user_info['fcm_token'])
            saveAlarmHistory(user_id=self.apply_status['user_id'], alarm_type="apply",
                             required=1, description="서포터즈 신청 조건에 만족하지 못하여 신청이 거절되었습니다, 다음 기회에 다시 도전해주세요ㅠㅜ"
                             )
        self.db.commit()

    def apply_accept(self):
        self.default_mission()
        self.update_apply_status()

    def apply(self):
        for i in range(len(self.apply_user_list)):
            self.apply_status = self.db.getOneApplyStatus(ad_user_apply_id=self.apply_user_list[i])
            self.check_status()
            if False in self.apply_information.values():
                return self.apply_information
            else:
                self.apply_id = self.apply_user_list[i]
                if self.kwargs['status'] == "reject":
                    self.apply_reject()
                elif self.kwargs['status'] != 'reject' and self.kwargs['status'] != 'accept':
                    self.apply_information['apply_data'] = False
                    return self.apply_information, self.user_fcm_list

                if self.kwargs['status'] == "accept":
                    self.set_mission_item()
                    for item in self.mission_item:
                        self.item = item
                        self.apply_accept()
                    self.insert_history()
                    self.insert_mission_card_user_information()
        self.db.db_close()
        return self.apply_information

    def response(self):
        response_data = self.apply()
        return response_data, self.user_fcm_list
