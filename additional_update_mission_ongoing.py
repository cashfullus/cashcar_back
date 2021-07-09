from appConfig.database.dbConnection import Database
from appConfig.notification.user_push_nofitication import one_cloud_messaging
from time import sleep


def update_mission_list():
    db = Database()
    mission_list = db.executeAll(
        query="SELECT ad_mission_card_user_id, mission_name, fcm_token, uf.user_id FROM ad_mission_card_user amcu "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
              "JOIN user_fcm uf on aua.user_id = uf.user_id "
              "JOIN user u on aua.user_id = u.user_id "
              "WHERE amcu.status = 'stand_by' AND amcu.mission_type IN (1) and aua.status IN ('accept')"
              "AND mission_start_date != '0000-00-00 00:00:00' AND mission_start_date <= NOW() AND alarm = 1"
    )
    if mission_list:
        for _, value in enumerate(mission_list):
            body_name = f"[{value.get('mission_name')}]이 오픈되었습니다. 서포터즈 활동 창에서 확인해보세요!"
            db.execute(
                query="UPDATE ad_mission_card_user SET status = 'ongoing' WHERE ad_mission_card_user_id = %s",
                args=value.get('ad_mission_card_user_id')
            )
            db.execute(
                query="INSERT INTO user_app_push_reservation (user_id, contents) VALUES (%s, %s)",
                args=[value.get('user_id'), body_name]
            )
            db.execute(
                query="INSERT INTO alarm_history (user_id, alarm_type, required, description) "
                      "VALUES (%s, %s, %s, %s)",
                args=[value.get('user_id'), "mission", 1, body_name]
            )
            db.commit()
    db.db_close()
    data = {"update_mission_list success": "OK", "mission_list": mission_list}
    return data


print(update_mission_list())
