from ..database.dbConnection import Database


# 제조사
def manufacturer(manufacturer_type):
    db = Database()
    sql = "SELECT manufacturer_id, manufacturer_name FROM manufacturer WHERE type = %s"
    result = db.executeAll(sql, manufacturer_type)
    return result


# 차량 등록
# manufacturer_id, user_id, name, year, car_number, post_code, address_name, building_name, detail_address
def register_car(**kwargs):
    db = Database()
    user = db.getUserById(kwargs.get("user_id"))
    if not user:
        return False

    sql = "INSERT INTO car" \
          "(user_id, manufacturer_id, car_name, year, car_number, post_code, address_name, building_name, " \
          "detail_address)" \
          "VALUES" \
          "(%s, %s, %s, %s, %s, %s, %s, %s, %s)"

    value_list = [val for key, val in kwargs.items()]
    db.execute(query=sql, args=value_list)
    db.commit()
    return True



