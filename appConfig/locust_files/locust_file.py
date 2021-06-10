from locust import HttpUser, TaskSet, task


class WebsiteUser(HttpUser):
    min_wait = 5
    max_wait = 1000

    # @task
    # def my_task(self):
        # self.client.get('main/my-ad?user_id=14', headers={"Authorization": })

