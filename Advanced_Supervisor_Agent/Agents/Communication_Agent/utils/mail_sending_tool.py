 
import requests
import json
import os
import base64
 
TENANT_ID='b27025bd-c085-406f-b4be-acc54b08a991'
CLIENT_ID='2681b872-0237-4a1a-9f81-f5e8771894d8'
CLIENT_SECRET='bOE8Q~Uvgfjr7SUdcLqPbOLy2osJ.uRGVBA-icX3'
EMAIL_USER='abhirajsingh.rajpurohit@idolizesolutions.com'
EMAIL_PASSWORD='Viking@@ibs2025'


class GraphEmailSender:
    def __init__(self):
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID  
        self.client_secret = CLIENT_SECRET
        self.sender_email = EMAIL_USER    
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print("Missing required credentials. Please check .env file.")
            print("Required variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET")
            return
   
    def get_access_token(self):
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
       
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
       
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
       
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            print(f"Failed to get access token: {e}")
            if response.status_code == 400:
                print("Check your TENANT_ID, CLIENT_ID, and CLIENT_SECRET")
            return None
   
    def send_email(self, to_emails, subject, message, cc_emails=None, attachments=None, msg=None):
        access_token = self.get_access_token()
        if not access_token:
            return False
       
        to_recipients = []
        if isinstance(to_emails, str):
            to_emails = [to_emails]
       
        for email in to_emails:
            to_recipients.append({
                "emailAddress": {
                    "address": email
                }
            })
       
        cc_recipients = []
        if cc_emails:
            if isinstance(cc_emails, str):
                cc_emails = [cc_emails]
            for email in cc_emails:
                cc_recipients.append({
                    "emailAddress": {
                        "address": email
                    }
                })
       
        # Track attachments
        attachment_list = []
        missing_attachments = []
 
        if attachments:
            if isinstance(attachments, str):
                attachments = [attachments]
 
            attachments = [att.replace("\\", "/") for att in attachments]
 
           
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                   
                    file_name = os.path.basename(file_path)
                    file_base64 = base64.b64encode(file_content).decode('utf-8')
                   
                    attachment = {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": file_name,
                        "contentBytes": file_base64
                    }
                    attachment_list.append(attachment)
                else:
                    missing_attachments.append(file_path)
 
       
        if missing_attachments:
            warn_text = f"\n⚠️ Attachments was downlaoded but was not founded at that path: {', '.join(missing_attachments)}"
            if "Best regards" in message:
                message = message.replace("Best regards", warn_text + "\n\nBest regards")
            else:
                message += warn_text
 
        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": message
                },
                "toRecipients": to_recipients
            },
            "saveToSentItems": "true"
        }
       
        if cc_recipients:
            email_payload["message"]["ccRecipients"] = cc_recipients
       
        if attachment_list:
            email_payload["message"]["attachments"] = attachment_list
       
        url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
       
        try:
            response = requests.post(url, headers=headers, json=email_payload)
           
            if response.status_code == 202:
                print("=" * 50)
                print("SUCCESS! Email sent via Microsoft Graph API")
                print("=" * 50)
                print(f"From: {self.sender_email}")
                print(f"To: {', '.join(to_emails)}")
                if cc_emails:
                    print(f"CC: {', '.join(cc_emails)}")
                print(f"Subject: {subject}")
                print("=" * 50)
                return True
            else:
                print(f"Failed to send email. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
               
        except requests.exceptions.RequestException as e:
            print(f"Error sending email: {e}")
            return False
 
def show_setup_instructions():
    print("""
MICROSOFT GRAPH API
This works with modern Microsoft 365 security.
""")
 
def mail_send(to_emails,cc_emails,subject,message,attachments):
    print("Microsoft Graph API Email Sender")
    print("=" * 40)
   
    try:
        sender = GraphEmailSender()
       
        success = sender.send_email(
            to_emails=to_emails,
            subject=subject,
            message=message,
            cc_emails=cc_emails,
            attachments=attachments
        )
       
        if not success:
            print("\nEmail sending failed. Showing setup instructions...")
            show_setup_instructions()
           
    except Exception as e:
        print(f"Error: {e}")
        print("\nShowing setup instructions...")
        show_setup_instructions()

 
