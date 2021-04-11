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

    def execute(self, query, args):
        self.cursor.execute(query, args)

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
        sql = f"SELECT * FROM user WHERE user_id = {user_id}"
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
              "vehicle_id, user_id, supporters, country, " \
              "brand, vehicle_model_name, year, car_number, " \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS register_time, " \
              "DATE_FORMAT(remove_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS remove_time, removed " \
              "FROM vehicle WHERE user_id = %s AND vehicle_id = %s"
        self.cursor.execute(query=sql, args=[user_id, vehicle_id])
        row = self.cursor.fetchone()
        return row

    def getAllVehicleByUserId(self, user_id):
        sql = "SELECT " \
              "vehicle_id, user_id, supporters, country, " \
              "brand, vehicle_model_name, year, car_number, " \
              "DATE_FORMAT(register_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS register_time, " \
              "DATE_FORMAT(remove_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS remove_time, removed " \
              "FROM vehicle WHERE user_id = %s AND removed = 0"
        self.cursor.execute(query=sql, args=user_id)
        rows = self.cursor.fetchall()
        return rows
