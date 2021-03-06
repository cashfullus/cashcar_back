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

    def db_close(self):
        self.cursor.close()
        self.db.close()

    def execute(self, query, args):
        self.cursor.execute(query, args)

    def executemany(self, query, args):
        self.cursor.executemany(query, args)

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
        sql = f"SELECT * FROM user WHERE user_id = {user_id} AND withdrawn = 0"
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
              "FROM vehicle WHERE user_id = %s AND vehicle_id = %s AND removed = 0"
        self.cursor.execute(query=sql, args=[user_id, vehicle_id])
        row = self.cursor.fetchone()
        return row

    def getAllVehicleByUserId(self, user_id):
        sql = "SELECT " \
              "vehicle_id, user_id, supporters, is_foreign_car, " \
              "brand, vehicle_model_name, year, car_number, owner_relationship," \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS register_time, " \
              "DATE_FORMAT(remove_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS remove_time, removed " \
              "FROM vehicle WHERE user_id = %s AND removed = 0 ORDER BY supporters DESC"
        self.cursor.execute(query=sql, args=user_id)
        rows = self.cursor.fetchall()
        return rows

    # 광고 디테일 By ad_id
    def getOneAdByAdId(self, ad_id):
        sql = "SELECT " \
              "ad_id, title, logo_image, thumbnail_image, gender, min_distance, " \
              "side_image, side_length, side_width, " \
              "back_image, back_length, back_width, " \
              "DATE_FORMAT(recruit_start_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_start_date, " \
              "DATE_FORMAT(recruit_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') as recruit_end_date, " \
              "activity_period, max_recruiting_count, recruiting_count, " \
              "total_point, area, description, min_age_group, max_age_group " \
              "FROM ad_information WHERE ad_id = %s AND removed = 0"
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
              "ad_id = %s AND removed = 0"
        self.cursor.execute(query=sql, args=ad_id)
        row = self.cursor.fetchone()
        return row

    # 광고 신청한 건에 대하여 By ad_user_apply_id
    def getOneAdUserApplyById(self, ad_user_apply_id):
        sql = "SELECT " \
              "ad_user_apply_id, user_id, ad_id, status, " \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "DATE_FORMAT(accept_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as accept_status_time " \
              "FROM ad_user_apply WHERE ad_user_apply_id = %s"
        self.cursor.execute(query=sql, args=ad_user_apply_id)
        row = self.cursor.fetchone()
        return row

    # 광고 신청한 건에 대하여
    def getAllAdUserApply(self, count, per_page):
        sql = "SELECT " \
              "title, owner_name, name, main_address, detail_address, " \
              "aua.recruit_number, max_recruiting_count, aua.status, " \
              "u.user_id, aua.ad_user_apply_id, call_number, email, " \
              "DATE_FORMAT(aua.register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time, " \
              "DATE_FORMAT(accept_status_time, '%%Y-%%m-%%d %%H:%%i:%%s') as accept_status_time " \
              "FROM ad_user_apply aua " \
              "JOIN ad_information ai on aua.ad_id = ai.ad_id " \
              "JOIN user u on aua.user_id = u.user_id " \
              "WHERE status IN ('stand_by', 'accept', 'success', 'reject') " \
              "ORDER BY FIELD(status, 'stand_by', 'accept', 'success', 'reject', 'fail'), aua.register_time DESC " \
              "LIMIT %s OFFSET %s"
        self.cursor.execute(query=sql, args=[count, per_page])
        rows = self.cursor.fetchall()
        return rows

    # 신청한 광고의 status, title, user_id, recruting_count 조회
    def getOneApplyStatus(self, ad_user_apply_id):
        sql = "SELECT status, title, aua.user_id, name, recruit_number, aua.ad_id, ad_status, " \
              "max_recruiting_count, recruiting_count " \
              "FROM ad_user_apply aua " \
              "JOIN ad_information ai on aua.ad_id = ai.ad_id " \
              "JOIN user u on aua.user_id = u.user_id " \
              "WHERE ad_user_apply_id = %s"
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
              "additional_point, due_date, `order`," \
              "based_on_activity_period " \
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
              "CASE WHEN mission_end_date IS NULL THEN '0000-00-00 00:00:00' " \
              "WHEN mission_end_date IS NOT NULL THEN DATE_FORMAT(amcu.mission_end_date, '%%Y-%%m-%%d %%H:%%i:%%s') " \
              "END as mission_end_date, " \
              "title, thumbnail_image, amcu.status as mission_status, amcu.mission_type as mission_type, " \
              "ad_mission_card_user_id, activity_period, total_point " \
              "FROM ad_user_apply as aua " \
              "JOIN ad_information ai on aua.ad_id = ai.ad_id " \
              "LEFT JOIN ad_mission_card_user amcu on aua.ad_user_apply_id = amcu.ad_user_apply_id " \
              "WHERE user_id = %s " \
              "AND (amcu.status NOT IN ('fail') or amcu.status IS NULL) " \
              "AND removed = 0 AND aua.status NOT IN ('success', 'fail', 'reject', 'cancel') " \
              "ORDER BY FIELD(amcu.status, 'ongoing', 'review', 're_review', 'stand_by', 'success'), " \
              "amcu.mission_start_date LIMIT 1"
        self.cursor.execute(query=sql, args=user_id)
        row = self.cursor.fetchone()
        return row

    #  사용자가 진행할 미션 리스트 조회
    def getAllMyMissionByUserId(self, user_id):
        sql = "SELECT " \
              "ad_mission_card_user_id, " \
              "amcu.ad_user_apply_id, amc.ad_mission_card_id, " \
              "amc.mission_type, amcu.status, amc.mission_name, amc.additional_point, amc.order, " \
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
              "amcu.ad_mission_card_user_id, amcu.status, mission_fail_count, " \
              "amc.mission_name, amc.mission_type, amc.additional_point, " \
              "based_on_activity_period, amc.`order`, amc.mission_type, activity_period, " \
              "mission_fail_count, title, u.user_id as user_id, fcm_token, alarm " \
              "FROM ad_mission_card_user as amcu " \
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id " \
              "JOIN ad_information ai on amc.ad_id = ai.ad_id " \
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id " \
              "JOIN user u on aua.user_id = u.user_id " \
              "JOIN user_fcm uf on aua.user_id = uf.user_id " \
              "WHERE amcu.ad_user_apply_id = %s AND amcu.ad_mission_card_id = %s AND removed = 0"
        self.cursor.execute(query=sql, args=[ad_user_apply_id, ad_mission_card_id])
        row = self.cursor.fetchone()
        return row

    # 사용자의 광고 상태 및 미션 처리 메세지 가져오기
    def getOneReason(self, user_id):
        self.cursor.execute(
            query="SELECT ad_mission_reason_id as reason_id, title, reason, is_read, message_type, is_additional_fail "
                  "FROM ad_mission_reason amr "
                  "JOIN ad_user_apply aua on amr.ad_user_apply_id = aua.ad_user_apply_id "
                  "JOIN user u on aua.user_id = u.user_id "
                  "WHERE u.user_id = %s AND is_read = 0 AND message_type != 'mission_success'",
            args=user_id
        )
        row = self.cursor.fetchone()
        return row

    # 사용자의 광고 상태 및 미션 처리 메세지 INSERT
    def saveStatusMessage(self, ad_user_apply_id, reason, message_type, title=""):
        self.cursor.execute(
            query="INSERT INTO ad_mission_reason (ad_user_apply_id, title, reason, message_type) "
                  "VALUE (%s, %s, %s, %s)",
            args=[ad_user_apply_id, title, reason, message_type]
        )
        self.commit()
        return

    # 공지사항 리스트
    def getUserAllNotice(self):
        self.cursor.execute(
            query="SELECT "
                  "notice_id, title, description, "
                  "DATE_FORMAT(register_time, '%Y-%m-%d %H:%i:%s') as register_time "
                  "FROM notice_information WHERE is_removed = 0 ORDER BY register_time DESC"
        )
        rows = self.cursor.fetchall()
        return rows

    def getAdminAllNotice(self, count, per_page):
        self.cursor.execute(
            query="SELECT "
                  "notice_id, title, description, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM notice_information WHERE is_removed = 0 ORDER BY register_time DESC LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        rows = self.cursor.fetchall()
        return rows

    def updateNotice(self, notice_id, title, description):
        self.cursor.execute(
            query="UPDATE notice_information "
                  "SET title = %s, description = %s, updated_time = NOW() WHERE notice_id = %s",
            args=[title, description, notice_id]
        )
        self.commit()

    def deleteNotice(self, notice_id):
        self.cursor.execute(
            query="UPDATE notice_information SET is_removed = 1 WHERE notice_id = %s",
            args=notice_id
        )
        self.commit()

    def getOneFcmToken(self, user_id):
        self.cursor.execute(
            query="SELECT fcm_token, uf.user_id, alarm, marketing FROM user_fcm uf "
                  "JOIN user u on uf.user_id = u.user_id "
                  "WHERE uf.user_id = %s",
            args=user_id
        )
        row = self.cursor.fetchone()
        return row

    def getAllFcmToken(self, user_id_list):
        fcm_tokens = []
        if user_id_list:
            for i in range(len(user_id_list)):
                self.cursor.execute(
                    query="SELECT fcm_token, uf.user_id, alarm, marketing FROM user_fcm uf "
                          "JOIN user u on uf.user_id = u.user_id "
                          "WHERE uf.user_id = %s",
                    args=user_id_list[i]
                )
                row = self.cursor.fetchone()
                if row['alarm'] == 1:
                    fcm_tokens.append(row['fcm_token'])

        return fcm_tokens

    def getAuthEmailByEmail(self, email):
        self.cursor.execute(
            query="SELECT user_id, email FROM user WHERE email = %s",
            args=email
        )
        row = self.cursor.fetchone()
        return row

    def getAdminMissionHistory(self, ad_user_apply_id):
        self.cursor.execute(
            query="SELECT reason, DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM ad_mission_reason "
                  "WHERE ad_user_apply_id = %s ORDER BY register_time DESC",
            args=ad_user_apply_id
        )
        rows = self.cursor.fetchall()
        return rows

    def getOneCashCarTipById(self, cash_car_tip_id):
        self.cursor.execute(query="SELECT * FROM cash_car_tip WHERE cash_car_tip_id = %s", args=cash_car_tip_id)
        row = self.cursor.fetchone()
        return row

    def getOneDonationById(self, donation_organization_id):
        self.cursor.execute(query="SELECT * FROM donation_organization "
                                  "WHERE donation_organization_id = %s",
                            args=donation_organization_id
                            )
        row = self.cursor.fetchone()
        return row

    def getOneUserDonateStatus(self, user_id):
        self.cursor.execute(
            query="SELECT status FROM withdrawal_donate "
                  "WHERE user_id = %s AND status IN ('stand_by', 'confirm')",
            args=user_id
        )
        row = self.cursor.fetchone()
        return row

    def getAllUserFcmToken(self, *user_list):
        if len(user_list) == 1:
            sql = f"SELECT fcm_token, user_id FROM user_fcm WHERE user_id IN ({list(user_list)[0]})"
        else:
            sql = f"SELECT fcm_token, user_id FROM user_fcm WHERE user_id IN {user_list} ORDER BY user_id"
        self.cursor.execute(
            query=sql
        )
        rows = self.cursor.fetchall()
        return rows

    # 앱 푸시 로그 last_insert_id return
    def insertAppPushLogReturnId(self, **kwargs):
        self.cursor.execute(
            query="INSERT INTO app_push_log (notification_title, notification_body, transfer_count) "
                  "VALUES (%s, %s, %s)",
            args=[kwargs.get('title'), kwargs.get('body'), kwargs.get('transfer_count')]
        )
        self.commit()
        self.cursor.execute(
            query="SELECT * FROM app_push_log ORDER BY register_time DESC LIMIT 1",
        )
        row = self.cursor.fetchone()
        return row

    # 앱푸시 로그
    def updateAppPushLog(self, **kwargs):
        self.cursor.execute(
            query="UPDATE app_push_log SET success_count = %s, fail_count = %s WHERE id = %s",
            args=[kwargs.get("success_count"), kwargs.get('fail_count'), kwargs.get('id')]
        )
        self.commit()
        return True

    def updateOneSuccessAppPushLog(self, app_push_id, user_id):
        self.cursor.execute(
            query="UPDATE app_push_log apl JOIN user_app_push_log uapl on apl.id = uapl.app_push_log_id "
                  "SET success_count = success_count + 1, fail_count = fail_count - 1, "
                  "status = 'success', updated_time = NOW() "
                  "WHERE app_push_log_id = %s AND user_id = %s",
            args=[app_push_id, user_id]
        )
        self.commit()
        return True

    # 사용자 기록남기기
    def insertUserAppPushLog(self, many_value):
        self.cursor.executemany(
            query="INSERT INTO user_app_push_log (user_id, app_push_log_id) VALUE (%s, %s)",
            args=many_value
        )
        self.commit()
        return True

    # 사용자 진행상태 return
    def updateUserAppPushLog(self, many_value):
        self.cursor.executemany(
            query="UPDATE user_app_push_log SET status = %s, updated_time = NOW() WHERE user_id = %s",
            args=many_value
        )
        self.commit()
        return True

    def getAllNotificationListWithCount(self, page, count):
        per_page = (page - 1) * count
        self.cursor.execute(
            query="SELECT id, notification_title, notification_body, success_count, transfer_count, "
                  "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') as register_time "
                  "FROM app_push_log ORDER BY id DESC LIMIT %s OFFSET %s",
            args=[count, per_page]
        )
        rows = self.cursor.fetchall()
        self.cursor.execute(
            query="SELECT count(id) as item_count FROM app_push_log"
        )
        item_count = self.cursor.fetchone()
        return rows, item_count['item_count']

    def updateAllAlarmHistoryByAppPush(self, many_value):
        if many_value:
            self.cursor.executemany(
                query="INSERT INTO alarm_history (user_id, alarm_type, required, description, is_read_alarm) "
                      "VALUES (%s, %s, %s, %s, 1)",
                args=many_value
            )
            self.commit()
            return True

    def updateOneAlarmHistoryByAppPush(self, **kwargs):
        self.cursor.execute(
            query="INSERT INTO alarm_history (user_id, alarm_type, required, description, is_read_alarm) "
                  "VALUES (%s, %s, %s, %s, 1)",
            args=[kwargs['user_id'], "marketing", 0, kwargs['description']]
        )
        self.commit()
        return True
