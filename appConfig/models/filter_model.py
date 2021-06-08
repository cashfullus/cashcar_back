

class Filter:
    def __init__(self):
        self.ad_status = None
        self.apply_status = None
        self.mission_status = None
        self.area = None
        self.gender = None
        self.age = None
        self.distance = None
        self.point = None
        self.start_datetime = None
        self.end_datetime = None

    def get_mission_status(self):
        if not self.mission_status:
            return "amcu.status IN ('review', 're_review', 'reject', 'success', 'fail')"
        else:
            q = self.mission_status.split(',')
            if len(q) >= 2:
                set_q = "|".join(q)
                return f"amcu.status REGEXP '{set_q}'"
            else:
                return f"amcu.status = {self.mission_status}"

    def get_ad_status(self):
        if self.ad_status:
            q = self.ad_status.split(',')
            if len(q) >= 2:
                set_q = "|".join(q)
                query = f"ai.status REGEXP '{set_q}'"
                return query
            else:
                return f"ai.status = {self.ad_status}"
        else:
            return "ai.status IN ('scheduled', 'ongoing', 'done')"

    def get_apply_status(self):
        if self.apply_status:
            q = self.apply_status.split(',')
            if len(q) >= 2:
                set_q = "|".join(q)
                query = f"aua.status REGEXP '{set_q}'"
                return query
            else:
                return f"aua.status = '{self.apply_status}'"
        else:
            return "aua.status IN ('stand_by', 'accept', 'success', 'fail')"

    def get_area(self):
        if self.area:
            q = self.area.split(',')
            if len(q) >= 2:
                set_q = "|".join(q)
                query = f"u.main_address REGEXP '{set_q}'"
                return query
            else:
                return f"u.main_address LIKE '%%{self.area}%%'"
        else:
            return f"u.main_address LIKE '%%'"

    def get_gender(self):
        if self.gender == 0:
            return f"u.resident_registration_number_back IN ('', '1', '2')"
        else:
            return f"u.resident_registration_number_back IN ({str(self.gender)})"

    def get_age(self):
        q = self.age.split('~')
        return f"(u.age >= {q[0]} AND u.age <= {q[1]})"

    def get_user_register_datetime(self):
        return f"(u.register_time >= '{self.start_datetime}' AND u.register_time <= '{self.end_datetime}')"

    def get_ad_apply_register_time(self):
        return f"(aua.register_time >= '{self.start_datetime}' AND aua.register_time <= '{self.end_datetime}')"




