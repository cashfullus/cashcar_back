from locust import HttpUser, TaskSet, task


class UserBehavior(TaskSet):
    def on_start(self):
        self.login()

    def on_stop(self):
        self.logout()

    def login(self):
        r = self.client.get("/agree/clause-service")

    def logout(self):
        r = "a"

    # @task(2)
    # def index(self):
    # self.client.get(“/”)
    @task(1)
    def dashboard(self):
        self.client.get("/agree/clause-service")


class WebsiteUser(HttpUser):
    task_set = UserBehavior
    min_wait = 5
    max_wait = 1000
