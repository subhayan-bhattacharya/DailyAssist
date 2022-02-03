class DummyBackend:
    @staticmethod
    def retrieve_all_reminders():
        return [
            {
                "name": "Call the doctor!!",
            },
            {
                "name": "Pay DVB bill!!"
            }
        ]

    @staticmethod
    def create_a_new_reminder():
        return {
            "message": "Created new reminder!!"
        }
