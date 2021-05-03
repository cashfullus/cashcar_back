from database.dbConnection import Database


def select_user():
    db = Database()
    users = db.executeAll(
        query="SELECT DISTINCT aua.ad_user_apply_id FROM ad_user_apply aua "
              "JOIN ad_information ai on aua.ad_id = ai.ad_id "
              "JOIN ad_mission_card_user amcu on aua.ad_user_apply_id = amcu.ad_user_apply_id "
              "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
              "WHERE activity_end_date IS NOT NULL AND aua.status != 'success' "
              "AND activity_end_date <= NOW()"
    )
    return users


def update_point():
    db = Database()
    users = select_user()
    if users:
        for i in range(len(users)):
            check_default_mission = db.executeOne(
                query="SELECT ad_user_apply_id, ad_mission_card_id FROM ad_mission_card_user "
                      "WHERE ad_user_apply_id = %s "
                      "AND mission_type = 0 "
                      "AND status IN ('stand_by', 'review', 'fail', 're_review')",
                args=users[i]['ad_user_apply_id']
            )
            if check_default_mission:
                db.execute(
                    query="UPDATE ad_mission_card_user amcu "
                          "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
                          "SET amcu.status = 'fail', aua.status = 'fail' "
                          "WHERE amcu.ad_user_apply_id = %s AND amcu.ad_mission_card_id = %s",
                    args=[check_default_mission['ad_user_apply_id'], check_default_mission['ad_mission_card_id']]
                )
                title = "신청한 서포터즈 활동에 실패했습니다:("
                reason = """서포터즈 활동 미션 인증에 실패하였습니다. 활동 미행으로 리워드는 지급해드리지 않으며 다른 서포터즈 활동에 지원해주세요."""
                db.execute(
                    query="INSERT INTO ad_mission_reason (ad_apply_id, title, reason, is_read) "
                          "VALUES (%s, %s, %s, %s)",
                    args=[users[i]['ad_user_apply_id'], title, reason, 0]
                )
            else:
                sum_additional_point = 0
                default_point = db.executeOne(
                    query="SELECT ai.total_point, user_id, title FROM ad_user_apply aua "
                          "JOIN ad_information ai on aua.ad_id = ai.ad_id "
                          "WHERE ad_user_apply_id = %s AND aua.status = 'accept'",
                    args=users[i]['ad_user_apply_id']
                )
                additional_point = db.executeAll(
                    query="SELECT additional_point FROM ad_mission_card_user amcu "
                          "JOIN ad_user_apply aua on amcu.ad_user_apply_id = aua.ad_user_apply_id "
                          "JOIN ad_mission_card amc on amcu.ad_mission_card_id = amc.ad_mission_card_id "
                          "WHERE amcu.status = 'success' AND amcu.mission_type IN (1) "
                          "AND amcu.ad_user_apply_id = %s AND aua.status = 'accept'",
                    args=users[i]['ad_user_apply_id']
                )
                sum_additional_point = sum(
                    [additional_point[j]['additional_point'] for j in range(len(additional_point))])
                db.execute(
                    query="UPDATE ad_user_apply SET status = 'success' WHERE ad_user_apply_id = %s",
                    args=users[i]['ad_user_apply_id']
                )
                sql = "UPDATE user u JOIN ad_user_apply aua on u.user_id = aua.user_id SET " \
                      "deposit = deposit + %s + %s WHERE ad_user_apply_id = %s"
                db.execute(
                    query=sql,
                    args=[default_point['total_point'], sum_additional_point, users[i]['ad_user_apply_id']]
                )
                content_name = f"{default_point['title']} 서포터즈 활동 성공"
                db.execute(
                    query="INSERT INTO point_history (user_id, point, register_time, type, contents) "
                          "VALUES (%s, %s, NOW(), %s, %s)",
                    args=[default_point['user_id'], int(default_point['total_point']) + sum_additional_point,
                          "ad_apply", content_name]
                )
                title = "서포터즈 활동에 성공하였습니다:)"
                reason = """열심히 활동해주신 고객님께 감사드리며 이제 차량에서 스티커를 제거하셔도 됩니다. 다음 활동도 잘 부탁드립니다."""
                db.execute(
                    query="INSERT INTO ad_mission_reason (ad_apply_id, title, reason, is_read) "
                          "VALUES (%s, %s, %s, %s)",
                    args=[users[i]['ad_user_apply_id'], title, reason, 0]
                )
            db.commit()


update_point()
