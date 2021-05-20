from appConfig.database.dbConnection import Database


def update_ad_status():
    db = Database()

    db.execute(
        query="UPDATE ad_information SET ad_status = 'ongoing' "
              "WHERE recruit_start_date <= NOW() AND recruit_end_date >= NOW() AND ad_status = 'scheduled'",
        args=None
    )
    db.execute(
        query="UPDATE ad_information SET ad_status = 'done' "
              "WHERE recruit_end_date < NOW() AND ad_status = 'ongoing'",
        args=None
    )
    db.commit()
    return True


update_ad_status()

