from appConfig.database.dbConnection import Database
from appConfig.notification.user_push_nofitication import multiple_cloud_messaging, one_cloud_messaging
from time import sleep

# 필수미션 1차 미션 발생
def default_mission_list():
    db = Database()
    first_default_mission_send_message = db.executeAll(
        query="SELECT u.user_id, fcm_token, aua.ad_user_apply_id FROM ad_mission_card_user amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN user u on aua.user_id = u.user_id "
              "JOIN user_fcm uf on aua.user_id = uf.user_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "WHERE amcu.mission_type = 0 AND amc.order = 1 AND amcu.status = 'ongoing' AND alarm = 1 "
              "AND aua.status = 'accept' AND amcu.mission_start_date <= NOW() AND is_first_message = 0 "
              "GROUP BY u.user_id"
    )
    if first_default_mission_send_message:
        for i in range(len(first_default_mission_send_message)):
            db.execute(
                query="UPDATE ad_user_apply SET is_first_message = 1 WHERE ad_user_apply_id = %s",
                args=first_default_mission_send_message[i]['ad_user_apply_id']
            )
            db.execute(
                query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                args=[first_default_mission_send_message[i]['user_id'], "[1차 미션]이 발생하였습니다. 미션 내용 확인 후 인증해주세요!"]
            )
        db.commit()
        sleep(0.2)

    mission_list = db.executeAll(
        query="SELECT u.user_id, fcm_token, ad_mission_card_user_id, mission_name, alarm "
              "FROM ad_mission_card_user amcu "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN user u on aua.user_id = u.user_id "
              "JOIN user_fcm uf on aua.user_id = uf.user_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "WHERE amcu.mission_type = 0 AND amc.order NOT IN (1) AND amcu.status = 'stand_by'"
              "AND aua.status = 'accept' AND amcu.mission_start_date <= NOW() "
              "GROUP BY u.user_id"
    )
    if mission_list:
        for i in range(len(mission_list)):
            db.execute(
                query="UPDATE ad_mission_card_user SET status = 'ongoing' WHERE ad_mission_card_user_id = %s",
                args=mission_list[i]['ad_mission_card_user_id']
            )
            if mission_list[i]['alarm'] == 1:
                body_name = f"[{mission_list[i]['mission_name']}]이 발생하였습니다. 미션 내용 확인 후 인증해주세요!"
                db.execute(
                    query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                    args=[mission_list[i]['user_id'], body_name]
                )
                db.commit()
            sleep(0.08)

    db.db_close()
    return "default_mission_list success"


print(default_mission_list())


