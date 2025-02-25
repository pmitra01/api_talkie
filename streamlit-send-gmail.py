import streamlit as st
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scope for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CLIENT_JSON_FILE = "client_secret_507912620340-m9r7mhmfrqm7jleiq4r0f7ilcrpifivv.apps.googleusercontent.com.json"

def authenticate():
    """
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_JSON_FILE, SCOPES, redirect_uri = "http://localhost:8501/")
    creds = flow.run_local_server(port=8501)
    return creds
    """
    pass


def send_email(creds, recipient, subject, body):
    """
    service = build('gmail', 'v1', credentials=creds)
    message = {
        'raw': base64.urlsafe_b64encode(
            f"To: {recipient}\nSubject: {subject}\n\n{body}".encode("utf-8")
        ).decode("utf-8")
    }
    service.users().messages().send(userId="me", body=message).execute()
    """
    pass

# Streamlit UI
st.title("Send Gmail Emails from Streamlit")
st.button("Dummy")
if st.button("Authenticate with Google"):
    credentials = authenticate()
    st.session_state['credentials'] = credentials

if 'credentials' in st.session_state:
    recipient = st.text_input("Recipient Email")
    subject = st.text_input("Subject")
    body = st.text_area("Email Body")

    if st.button("Send Email"):
        send_email(st.session_state['credentials'], recipient, subject, body)
        st.success("Email sent successfully!")
