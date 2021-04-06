import pymysql


class Database():
    def __init__(self):
        self.db = pymysql.connect(host='localhost',
                                  user='root',
                                  password='',
                                  db='nodebasic',
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

    def getUserByPhoneNumber(self, user_phone_number):
        sql = "SELECT * FROM user WHERE phone_number = %s"
        self.cursor.execute(sql, user_phone_number)
        row = self.cursor.fetchone()
        return row

    def getUserById(self, user_id=None):
        if user_id is None:
            return False
        sql = f"SELECT * FROM user WHERE user_id = {user_id}"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        return row

    def _checkUserJwt(self, user_id, jwt_token):
        if user_id is None or jwt_token is None:
            return False

        sql = f"SELECT user_id FROM user WHERE user_id = {user_id} AND jwt_token = {jwt_token}"
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        if row:
            return True
        else:
            return False


