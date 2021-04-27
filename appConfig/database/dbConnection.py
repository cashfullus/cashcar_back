import pymysql


# 실서버에서는 port 33906
class Database:
    def __init__(self):
        self.db = pymysql.connect(host='101.101.217.231',
                                  port=33906,
                                  user='cashcarapiuser',
                                  password='akTmzmtlfgdj2)2!',
                                  db='appservice',
                                  charset='utf8')

        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)

    def execute(self, query, args):
        self.cursor.execute(query, args)

    def executeOne(self, query, args=None):
        if args is None:
            args = {}
        self.cursor.execute(query, args)
        row = self.cursor.fetchone()
        return row

    def executeAll(self, query, args=None):
        if args is None:
            args = {}
        self.cursor.execute(query, args)
        rows = self.cursor.fetchall()
        return rows

    def commit(self):
        self.db.commit()

    def getUserById(self, user_id):
        sql = f"SELECT * FROM user WHERE user_id = {user_id}"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        return row

    def getUserByEmail(self, email):
        sql = "SELECT email FROM user WHERE email = %s"
        self.cursor.execute(sql, email)
        row = self.cursor.fetchone()
        return row

    def getLoginTypeUserByEmail(self, email, login_type):
        sql = "SELECT * FROM user WHERE email = %s AND login_type = %s"
        self.cursor.execute(sql, [email, login_type])
        row = self.cursor.fetchone()
        return row

    def getOneVehicleByVehicleIdAndUserId(self, vehicle_id, user_id):
        sql = "SELECT " \
              "vehicle_id, user_id, supporters, is_foreign_car, " \
              "brand, vehicle_model_name, year, car_number, owner_relationship, " \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS register_time, " \
              "DATE_FORMAT(remove_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS remove_time, removed " \
              "FROM vehicle WHERE user_id = %s AND vehicle_id = %s"
        self.cursor.execute(query=sql, args=[user_id, vehicle_id])
        row = self.cursor.fetchone()
        return row

    def getAllVehicleByUserId(self, user_id):
        sql = "SELECT " \
              "vehicle_id, user_id, supporters, is_foreign_car, " \
              "brand, vehicle_model_name, year, car_number, owner_relationship," \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS register_time, " \
              "DATE_FORMAT(remove_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS remove_time, removed " \
              "FROM vehicle WHERE user_id = %s AND removed = 0 ORDER BY supporters"
        self.cursor.execute(query=sql, args=user_id)
        rows = self.cursor.fetchall()
        return rows

    # 광고 디테일 By ad_id
    def getOneAdByAdId(self, ad_id):
        sql = "SELECT " \
              "ad_id, title, thumbnail_image, min_distance, " \
              "side_image, side_length, side_width, " \
              "back_image, back_length, back_width, " \
              "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
              "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date, " \
              "activity_period, max_recruiting_count, recruiting_count, " \
              "total_point, area, description " \
              "FROM ad_information WHERE ad_id = %s"
        self.cursor.execute(query=sql, args=ad_id)
        row = self.cursor.fetchone()
        return row

    # 광고 이미지 전체
    def getAllAdImageById(self, ad_id):
        sql = "SELECT image FROM ad_images WHERE ad_id = %s"
        self.cursor.execute(query=sql, args=ad_id)
        rows = self.cursor.fetchall()
        return rows

    # 광고 신청할때 사용 by ad_id
    def getOneAdApplyByAdId(self, ad_id):
        sql = "SELECT " \
              "ad_id, title, thumbnail_image, " \
              "side_image, side_length, side_width, " \
              "back_image, back_length, back_width, " \
              "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
              "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date, " \
              "activity_period, max_recruiting_count, recruiting_count, " \
              "total_point, area, description " \
              "FROM ad_information WHERE " \
              "recruiting_count < max_recruiting_count " \
              "AND NOW() BETWEEN recruit_start_date AND recruit_end_date AND " \
              "ad_id = %s"
        self.cursor.execute(query=sql, args=ad_id)
        row = self.cursor.fetchone()
        return row

    # 광고 신청한 건에 대하여 By ad_user_apply_id
    def getOneAdUserApplyById(self, ad_user_apply_id):
        sql = "SELECT " \
              "ad_user_apply_id, user_id, ad_id, status, " \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "DATE_FORMAT(change_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as change_status_time " \
              "FROM ad_user_apply WHERE ad_user_apply_id = %s"
        self.cursor.execute(query=sql, args=ad_user_apply_id)
        row = self.cursor.fetchone()
        return row

    # 광고 신청한 건에 대하여
    def getAllAdUserApply(self):
        sql = "SELECT " \
              "ad_user_apply_id, user_id, ad_id, status, " \
              "DATE_FORMAT(register_time, '%Y-%m-%d %H:%i:%s') as register_time, " \
              "DATE_FORMAT(change_status_time, '%Y-%m-%d %H:%i:%s') as change_status_time " \
              "FROM ad_user_apply"
        self.cursor.execute(query=sql)
        rows = self.cursor.fetchall()
        return rows

    # 신청한 광고의 status 만 가져오기
    def getOneApplyStatus(self, ad_user_apply_id):
        sql = "SELECT status FROM ad_user_apply WHERE ad_user_apply_id = %s"
        self.cursor.execute(query=sql, args=ad_user_apply_id)
        row = self.cursor.fetchone()
        return row

    # 광고 신청 수락 후 id 데이터 가져오기
    def getAdMissionCardIdxByAcceptApply(self, ad_user_apply_id):
        sql = "SELECT ad_mission_card_id, amc.ad_id, amc.due_date, amc.mission_type " \
              "FROM ad_user_apply " \
              "JOIN ad_mission_card amc on ad_user_apply.ad_id = amc.ad_id " \
              "WHERE ad_user_apply_id = %s"
        self.cursor.execute(query=sql, args=ad_user_apply_id)
        rows = self.cursor.fetchall()
        return rows

    def getAllAdMissionCardInfoByAcceptApply(self, ad_user_apply_id):
        sql = "SELECT ad_mission_card_id, mission_type, mission_name, " \
              "additional_point, due_date, `order`, from_default_order, " \
              "from_default_order_date, based_on_activity_period " \
              "FROM ad_user_apply as aua " \
              "JOIN ad_mission_card amc on aua.ad_id = amc.ad_id " \
              "WHERE ad_user_apply_id = %s ORDER BY mission_type, `order`"
        self.cursor.execute(query=sql, args=ad_user_apply_id)
        rows = self.cursor.fetchall()
        return rows

    def getMainMyAd(self, user_id):
        sql = "SELECT " \
              "aua.ad_user_apply_id as ad_user_apply_id, user_id, aua.ad_id as ad_id, aua.status as apply_status, " \
              "default_mission_success_count, additional_mission_success_count, ad_mission_card_id, day_point as point," \
              "DATE_FORMAT(aua.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as apply_register_time, " \
              "DATE_FORMAT(activity_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_start_date, " \
              "DATE_FORMAT(activity_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as activity_end_date, " \
              "title, thumbnail_image, amcu.status as mission_status, amcu.mission_type as mission_type " \
              "FROM ad_user_apply as aua " \
              "JOIN ad_information ai on aua.ad_id = ai.ad_id " \
              "LEFT JOIN ad_mission_card_user amcu on aua.ad_user_apply_id = amcu.ad_user_apply_id " \
              "WHERE user_id = %s AND (amcu.status NOT IN ('success') or amcu.status IS NULL) " \
              "ORDER BY FIELD(mission_start_date, ad_mission_card_id) LIMIT 1"
        self.cursor.execute(query=sql, args=user_id)
        row = self.cursor.fetchone()
        return row

    #  사용자가 진행할 미션 리스트 조회
    def getAllMyMissionByUserId(self, user_id):
        sql = "SELECT " \
              "ad_mission_card_user_id, " \
              "amcu.ad_user_apply_id, amc.ad_mission_card_id, " \
              "amc.mission_type, amcu.status, amc.mission_name, amc.additional_point, " \
              "DATE_FORMAT(mission_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as mission_start_date, " \
              "DATE_FORMAT(mission_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as mission_end_date " \
              "FROM ad_mission_card_user as amcu " \
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id " \
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id " \
              "WHERE aua.user_id = %s AND aua.status IN ('accept', 'stand_by')"
        self.cursor.execute(query=sql, args=user_id)
        rows = self.cursor.fetchall()
        return rows

    # 미션 인증에 사용
    def getOneMissionUserInfoByIdx(self, ad_user_apply_id, ad_mission_card_id):
        sql = "SELECT " \
              "amcu.ad_mission_card_user_id, status, mission_fail_count, " \
              "amc.mission_name, amc.mission_type, amc.additional_point, amc.from_default_order, " \
              "amc.from_default_order_date, based_on_activity_period, amc.`order`, amc.mission_type, activity_period, " \
              "mission_fail_count " \
              "FROM ad_mission_card_user as amcu " \
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id " \
              "JOIN ad_information ai on amc.ad_id = ai.ad_id " \
              "WHERE ad_user_apply_id = %s AND amcu.ad_mission_card_id = %s"
        self.cursor.execute(query=sql, args=[ad_user_apply_id, ad_mission_card_id])
        row = self.cursor.fetchone()
        return row

    # 필수미션 기준으로 추가할 추가미션 데이터 조회
    def getAllAddMissionUserInfoByApplyIdFirst(self, ad_user_apply_id, ad_mission_card_id, from_default_order):
        sql = "SELECT " \
              "ad_mission_card_user_id, amc.mission_type, amc.additional_point, " \
              "amc.order, amc.from_default_order, amc.from_default_order_date, due_date " \
              "FROM ad_mission_card_user amcu " \
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id " \
              "WHERE amcu.ad_user_apply_id = %s " \
              "AND amcu.ad_mission_card_id NOT IN (%s) " \
              "AND amc.mission_type NOT IN (0) " \
              "AND amc.from_default_order IN (%s) " \
              "AND amcu.status = 'stand_by' " \
              "AND mission_start_date = '0000-00-00 00:00:00'"
        self.cursor.execute(query=sql, args=[ad_user_apply_id, ad_mission_card_id, from_default_order])
        rows = self.cursor.fetchall()
        return rows





