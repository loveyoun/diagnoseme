from locust import HttpUser, task


class TortoiseUser(HttpUser):
    @task
    def get_and_update_and_get(self) -> None:
        create_meeting_response = self.client.post(
            url="/v1/mysql/meetings",
        )
        url_code = create_meeting_response.json()["url_code"]

        self.client.patch(
            url=f"/v1/mysql/meetings/{url_code}/date_range",
            json={
                "start_date": "2025-01-01",
                "end_date": "2025-02-20",
            },
            name="patch_date_range_mysql",
        )

        self.client.post(
            url="/v1/mysql/participants",
            json={
                "name": "test_name",
                "meeting_url_code": url_code,
            },
            name="post_participants_mysql",
        )

        self.client.get(
            url=f"/v1/mysql/meetings/{url_code}",
            name="get_meetings_mysql",
        )
