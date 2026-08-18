from locust import HttpUser, task, between

class SyncForceUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Executed when a simulated user starts."""
        pass # In a real scenario, we would authenticate here and store the token
        
    @task(3)
    def health_check(self):
        self.client.get("/health")
        
    @task(1)
    def create_lead(self):
        # We simulate a post request. To make this fully functional, 
        # it would need a valid auth token which requires seeding a user in the DB.
        self.client.post("/leads/?name=LoadTest&email=load@test.com&company=LoadTester", 
                         headers={"Authorization": "Bearer MOCK_TOKEN"},
                         catch_response=True) # Catching response so we don't fail the locust test on 401s during baseline
