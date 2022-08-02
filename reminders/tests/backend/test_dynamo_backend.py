import pytest
import boto3
from chalicelib.data_structures import SingleReminder
from chalicelib.backend.dynamodb import dynamo_backend, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


@pytest.fixture(scope="session")
def docker_compose_files(pytestconfig):
    """Get the docker-compose.yml absolute path.
    Override this fixture in your tests if you need a custom location.
    """
    return [pytestconfig.invocation_dir / "tests/backend/docker-compose.yml"]


@pytest.fixture(scope="session")
def docker_app(docker_services):
    """Start the dynamodb application."""
    docker_services.start("dynamodb-local")
    public_port = docker_services.wait_for_service("dynamodb-local", 8000)
    url = "http://{docker_services.docker_ip}:{public_port}".format(**locals())
    return url


@pytest.fixture(scope="session")
def session():
    """Create boto3 session object."""
    return boto3.session.Session(profile_name="dynamo_local")


@pytest.fixture()
def reminders(docker_app, session):
    """Create dynamodb table on local dynamodb."""
    dynamodb = session.resource("dynamodb", endpoint_url=docker_app)
    dynamodb.create_table(
        TableName="Reminders",
        KeySchema=[
            {"AttributeName": "reminder_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "reminder_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "reminder_title", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserIdReminderTitleGsi",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "reminder_title", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "reminder_expiration_date_time",
                        "reminder_id",
                    ],
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    yield
    # Delete the above table so that we can start afresh
    table = dynamodb.Table("Reminders")
    table.delete()


@pytest.fixture()
def reminders_model(docker_app):
    """Update reminders meta information for local testing."""
    models.Reminders.Meta.host = docker_app
    models.Reminders.Meta.aws_access_key_id = "something"
    models.Reminders.Meta.aws_secret_access_key = "anything"


@pytest.fixture()
def new_reminder():
    def _new_reminder(reminder_id: str, reminder_title: str, user_id: str):
        """Create a new reminder."""
        return SingleReminder(
            reminder_id=reminder_id,
            user_id=user_id,
            reminder_title=reminder_title,
            reminder_description="Test reminder",
            reminder_tags=["Test"],
            reminder_frequency="once",
            should_expire=True,
            reminder_expiration_date_time=datetime.now() + relativedelta(months=1),
            next_reminder_date_time=datetime.now() + relativedelta(days=20),
            reminder_creation_time=datetime.now(),
        )

    return _new_reminder


def test_create_single_reminder(reminders, reminders_model, new_reminder):
    """Test creating a single reminder."""
    reminder = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder)
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="test_user_1", reminder_title="Test reminder"
    )
    for item in reminder_from_db:
        assert item.reminder_id == "abc"


def test_get_a_reminder_for_a_user(reminders, reminders_model, new_reminder):
    """Test the function get a reminder for a user."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    reminder_2 = new_reminder(
        reminder_id="abc", user_id="test_user_2", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_for_user_1 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    assert len(reminder_for_user_1) == 1
    reminder_for_user_2 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_2"
    )
    assert len(reminder_for_user_2) == 1


def test_get_all_reminders_for_a_user(reminders, reminders_model, new_reminder):
    """Test the function get all reminders for a user."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    reminder_2 = new_reminder(
        reminder_id="def", user_id="test_user_1" "", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    all_reminders_for_user_1 = (
        dynamo_backend.DynamoBackend.get_all_reminders_for_a_user(user_id="test_user_1")
    )
    assert len(all_reminders_for_user_1) == 2
    reminder_ids = [reminder.reminder_id for reminder in all_reminders_for_user_1]
    assert sorted(reminder_ids) == sorted(["abc", "def"])


def test_update_a_reminder_for_a_user(reminders, reminders_model, new_reminder):
    """Test that updating a reminder for a single user works."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_1.reminder_description = "Changed reminder description"
    dynamo_backend.DynamoBackend.update_a_reminder(
        reminder_id="abc", updated_reminder=reminder_1.dict()
    )
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    for reminder in reminder_from_db:
        assert reminder.reminder_description == "Changed reminder description"


def test_update_a_reminder_works_for_a_shared_reminder(
    reminders, reminders_model, new_reminder
):
    """Test that updating a shared reminder works."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_2 = new_reminder(
        reminder_id="abc", user_id="test_user_2" "", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_1.reminder_description = "Changed reminder description"
    dynamo_backend.DynamoBackend.update_a_reminder(
        reminder_id="abc", updated_reminder=reminder_1.dict()
    )
    reminder_from_db_user_1 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    for reminder in reminder_from_db_user_1:
        assert reminder.reminder_description == "Changed reminder description"

    reminder_from_db_user_2 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_2"
    )
    for reminder in reminder_from_db_user_2:
        assert reminder.reminder_description == "Changed reminder description"


def test_get_a_reminder_gsi(reminders, reminders_model, new_reminder):
    """Test the function get_a_reminder_gsi."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_from_db_gsi = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="test_user_1", reminder_title="Test reminder"
    )
    all_reminders_from_db_gsi = list(reminder_from_db_gsi)
    assert len(all_reminders_from_db_gsi) == 1
    for reminder in all_reminders_from_db_gsi:
        assert reminder.reminder_id == "abc"
        assert reminder.reminder_title == "Test reminder"
        assert isinstance(reminder.reminder_expiration_date_time, datetime)
        assert (
            datetime.strftime(reminder.reminder_expiration_date_time, "%d/%m/%y")
            == "02/09/22"
        )
