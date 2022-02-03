from chalice import Chalice
from chalicelib.backend.dummy_backend import DummyBackend

app = Chalice(app_name="daily_assist_reminders")


@app.route("/reminders")
def reminders():
    return DummyBackend.retrieve_all_reminders()


@app.route("/reminders", methods=['POST'])
def new_reminder():
    return DummyBackend.create_a_new_reminder()
