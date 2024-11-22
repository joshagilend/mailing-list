import os
from flask import Flask, request, jsonify
from twilio.rest import Client
import boto3
from requests import post

app = Flask(__name__)

# Load environment variables (you can use dotenv or set these manually in your environment)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')

WHATSAPP_API_URL = "https://graph.facebook.com/v16.0/YOUR_WHATSAPP_PHONE_ID/messages"
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize SNS client
sns_client = boto3.client(
    'sns',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Home route
@app.route('/')
def home():
    return "Welcome to the Mailing List App!"

# Add a subscriber to SNS topic
@app.route('/add-subscriber', methods=['POST'])
def add_subscriber():
    data = request.json
    phone_number = data.get('phone_number')
    topic_arn = data.get('topic_arn')
    
    if not phone_number or not topic_arn:
        return jsonify({"error": "phone_number and topic_arn are required"}), 400
    
    try:
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='SMS',
            Endpoint=phone_number
        )
        return jsonify({"message": "Subscriber added successfully!", "SubscriptionArn": response['SubscriptionArn']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Send SMS via Twilio
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.json
    to_number = data.get('to_number')
    message_body = data.get('message_body')
    
    if not to_number or not message_body:
        return jsonify({"error": "to_number and message_body are required"}), 400
    
    try:
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return jsonify({"message": "SMS sent successfully!", "sid": message.sid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Send WhatsApp message
@app.route('/send-whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.json
    to_number = data.get('to_number')
    message_body = data.get('message_body')
    
    if not to_number or not message_body:
        return jsonify({"error": "to_number and message_body are required"}), 400
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_body
        }
    }
    
    try:
        response = post(WHATSAPP_API_URL, json=payload, headers=headers)
        response_data = response.json()
        if response.status_code == 200:
            return jsonify({"message": "WhatsApp message sent successfully!", "response": response_data})
        else:
            return jsonify({"error": "Failed to send WhatsApp message", "response": response_data}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Broadcast to SNS subscribers
@app.route('/broadcast', methods=['POST'])
def broadcast():
    data = request.json
    topic_arn = data.get('topic_arn')
    message_body = data.get('message_body')
    
    if not topic_arn or not message_body:
        return jsonify({"error": "topic_arn and message_body are required"}), 400
    
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message_body
        )
        return jsonify({"message": "Broadcast sent successfully!", "MessageId": response['MessageId']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
