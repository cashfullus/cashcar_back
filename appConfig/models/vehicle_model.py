from ..database.dbConnection import Database


# 차량 등록
def register_vehicle(**kwargs):
    db = Database()
    result = {"user": True, "register": True, "double_check_number": True}
    # 계정유무 확인
    user = db.getUserById(kwargs.get("user_id"))
    if not user:
        result["user"] = False
        return result

    # 본인이 등록한 차량 수 조회
    counter_register_vehicle = db.executeAll(
        query="SELECT COUNT(*) as cnt FROM vehicle WHERE user_id = %s",
        args=kwargs.get("user_id")
    )

    # 차량 번호 유무 확인
    check_vehicle_number = db.executeOne(
        query="SELECT * FROM vehicle WHERE car_number = %s",
        args=kwargs.get("car_number")
    )
    # 최대 허용 등록 개수 3개
    if counter_register_vehicle[0]["cnt"] >= 3:
        result["register"] = False
        return result

    # 차량 번호 중복 확인
    elif check_vehicle_number:
        result["double_check_number"] = False
        return result

    else:
        pass

    # INSERT
    sql = "INSERT INTO vehicle (user_id, supporters, country, brand, year, car_number) VALUES (%s, %s, %s, %s, %s, %s)"
    # kwargs 가 아닌 args 인 value만 필요하기때문에 val만 리스트로 만들어서 전달
    # kwargs 로 보내도 확인 결과 똑같은 과정을 진행하여 value를 가져오는것으로 확인
    value_list = [val for val in kwargs.values()]
    db.execute(query=sql, args=value_list)
    db.commit()
    return result


def vehicle_detail_by_id(**kwargs):
    db = Database()
    target_vehicle = db.executeOne(
        query="SELECT * FROM vehicle WHERE vehicle_id = %s AND user_id = %s",
        args=[kwargs.get("vehicle_id"), kwargs.get("user_id")]
    )
    return target_vehicle


def vehicle_update_by_id(**kwargs):
    db = Database()
    result = {"target_vehicle": True}
    target_vehicle = db.executeOne(
        query="SELECT * FROM vehicle WHERE vehicle_id = %s AND user_id = %s",
        args=[kwargs.get("vehicle_id"), kwargs.get("user_id")]
    )

    # vehicle_id 와 user_id에 맞는 데이터가 존재한다면
    if target_vehicle:
        # 업데이트 쿼리 진행
        sql = "UPDATE vehicle SET " \
              f"supporters = {kwargs.get('supporters')}, " \
              f"country = {kwargs.get('country')}, " \
              f"brand = {kwargs.get('brand')}, " \
              f"year = {kwargs.get('year')}, " \
              f"car_number = {kwargs.get('car_number')} " \
              f"WHERE vehicle_id = {kwargs.get('vehicle_id')} AND user_id = {kwargs.get('user_id')}"

        db.execute(query=sql, args=None)
        db.commit()

        return result
    # 차량 정보가 존재하지않다면 False
    else:
        result["target_vehicle"] = False
        return result





