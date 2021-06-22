from appConfig.database.dbConnection import Database


def delete_user():
    db = Database()
    db.execute("DELETE FROM user", None)
    db.execute("DELETE FROM user_activity_history", None)
    db.execute("DELETE FROM user_app_push_log", None)
    db.execute("DELETE FROM user_fcm", None)
    db.execute("DELETE FROM vehicle", None)
    db.execute("DELETE FROM alarm_history", None)
    db.execute("DELETE FROM point_history", None)
    db.execute("ALTER TABLE user AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE user_activity_history AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE user_app_push_log AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE user_fcm AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE vehicle AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE alarm_history AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE point_history AUTO_INCREMENT = 1", None)
    db.db_close()
    return True


def delete_advertisement():
    db = Database()
    db.execute("DELETE FROM ad_user_apply", None)
    db.execute("DELETE FROM ad_images", None)
    db.execute("DELETE FROM ad_mission_card", None)
    db.execute("DELETE FROM ad_mission_card_user", None)
    db.execute("DELETE FROM ad_mission_reason", None)
    db.execute("DELETE FROM mission_images", None)
    db.execute("DELETE FROM withdrawal_donate", None)
    db.execute("DELETE FROM withdrawal_self", None)
    db.execute("DELETE FROM app_push_log", None)
    db.execute("ALTER TABLE ad_user_apply AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE ad_images AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE ad_mission_card AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE ad_mission_card_user AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE ad_mission_reason AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE mission_images AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE withdrawal_self AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE withdrawal_donate AUTO_INCREMENT = 1", None)
    db.execute("ALTER TABLE app_push_log AUTO_INCREMENT = 1", None)
    db.db_close()
    return True


a = delete_user()
print(a)
b = delete_advertisement()
print(b)