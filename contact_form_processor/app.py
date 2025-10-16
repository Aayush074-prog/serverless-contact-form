import json
import os
import boto3
import uuid
import datetime

# Get environment variables
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def lambda_handler(event, context):
    """
    Handles form submissions from the API Gateway.
    - Stores data in DynamoDB.
    - Sends an email notification via SES.
    """
    print(f"Received event: {event}")

    try:
        # 1. Parse the incoming request body
        body = json.loads(event.get("body", "{}"))
        name = body.get("name")
        email = body.get("email")
        message = body.get("message")

        if not all([name, email, message]):
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*", # Allow requests from any origin
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({"error": "Missing required fields: name, email, message."}),
            }

        # 2. Prepare data for DynamoDB
        submission_id = str(uuid.uuid4())
        timestamp = str(datetime.datetime.utcnow().isoformat())

        item = {
            'submissionId': submission_id,
            'name': name,
            'email': email,
            'message': message,
            'submittedAt': timestamp
        }

        # 3. Store the data in DynamoDB
        table.put_item(Item=item)
        print(f"Successfully stored item in DynamoDB: {item}")

        # 4. Send an email notification using SES
        email_subject = f"New Contact Form Submission from {name}"
        email_body = f"""
        You have received a new message from your website's contact form.

        Name: {name}
        Email: {email}
        Message:
        {message}

        Submission ID: {submission_id}
        """

        ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECIPIENT_EMAIL]},
            Message={
                'Subject': {'Data': email_subject},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        print(f"Successfully sent email notification to {RECIPIENT_EMAIL}")

        # 5. Return a success response
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"message": "Form submitted successfully!", "submissionId": submission_id}),
        }

    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": "An internal error occurred."}),
        }