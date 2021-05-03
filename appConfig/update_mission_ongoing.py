from database.dbConnection import Database


def update_mission_list():
    db = Database()
    mission_list = db.executeAll(
        query="SELECT ad_mission_card_user_id FROM ad_mission_card_user "
              "WHERE status = 'stand_by' AND mission_type IN (1) "
              "AND mission_start_date != '0000-00-00 00:00:00' AND mission_start_date <= NOW()"
    )

    if mission_list:
        for i in range(len(mission_list)):
            db.execute(
                query="UPDATE ad_mission_card_user SET status = 'ongoing' WHERE ad_mission_card_user_id = %s",
                args=mission_list[i]['ad_mission_card_user_id']
            )

        db.commit()


update_mission_list()
