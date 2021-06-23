from appConfig.database.dbConnection import Database
from appConfig.notification.user_push_nofitication import multiple_cloud_messaging, one_cloud_messaging


def app_push():
    db = Database()
    result = db.executeAll(
        query="SELECT app_push_reservation_id, uapr.user_id, contents, fcm_token, alarm "
              "FROM user_app_push_reservation uapr "
              "JOIN user u on uapr.user_id = u.user_id "
              "JOIN user_fcm uf on u.user_id = uf.user_id "
              "WHERE is_send = 0"
    )
    if result:
        for _, value in enumerate(result):
            if value.get('alarm') == 1:
                one_cloud_messaging(token=value.get('fcm_token'), body=value.get('contents'))

            db.execute(
                query="UPDATE user_app_push_reservation SET is_send = 1 WHERE app_push_reservation_id = %s",
                args=value.get('app_push_reservation_id')
            )
        db.commit()

    db.db_close()
    return result


print(app_push())



