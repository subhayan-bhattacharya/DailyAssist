from chalice import Chalice
from chalice import CognitoUserPoolAuthorizer
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend
from datetime import datetime
import json
import os

app = Chalice(app_name="daily_assist_reminders")


authorizer = CognitoUserPoolAuthorizer(
    os.getenv('COGNITO_USER_POOL_NAME'),
    provider_arns=[os.getenv('COGNITO_USER_POOL_ARN')]
)


@app.route("/reminders", methods=['POST'], content_types=['application/json'], authorizer=authorizer)
def new_reminder():
    """Creates a new reminder in the database."""
    json_request = json.loads(app.current_request.raw_body.decode())
    return {
        "app": "daily_assist",
        "request_time": datetime.now().ctime(),
        "json": json_request,
        "request_context": app.current_request.context
    }
