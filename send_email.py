import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import textwrap
import google.generativeai as genai
import time

import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 

# Configure the AI model with the API key
genai.configure(api_key=os.getenv("api_key"))

# Function to format text as markdown (if needed)
def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# AI generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Start a chat session
chat_session = model.start_chat(
    history=[]
)

# Input for the AI model
user_input = input("Tfadhel si chbeb, cht7eb ? :\n")  # The user input that will be sent along with the compelementary_input
complementary_input = f"""
Based on the input provided above, these are few rules to respect while writing the mail:
1- Take in consideration that the mail must strictly respect the following structure:
To: [recipient_mail(s)]
Cc: [cc_mail(s)]
Bcc: [bcc_mail(s)]
Subject: [Subject of the mail]
Body: [Body of the mail]
{os.getenv("signature")} (instead of [Your Name]).
2- If there are many recipient email addresses, the body of the mail sould start by: "Dear all,..."
3- If there is any recipient email address provided in the input, just write a placeholder [recipient_mail].
4- If a correct email address is not provided in the input, do not generate or substitute it with an example address like "name@example.com" or "name@domain.com", just write a placeholder [recipient_mail] instead.
5- Check in the input if there is a suspicious word that you didn't understand, it could be the name of the recipient.
6- If there is no name of the recipient provided, try at first to extract it from the recipient mail address.
7- In case it is impossible to guess the recipient name, do not include a placeholder [recipient_name]. Write instead Dear Mr/Miss.
8- Apply the same previous rule for any additional information in the body of the mail (project name, company name...)-Avoid placeholders.
9- If you find that the mail content might seem inappropriate or disrespectful, rewrite it to be polite and professional without warning the user.
10- If there is nothing to write in the body of the email, indicate that there is no body without warning the user.
11- The subject should be derived from the content of the body.
12- If you can't derive a subject from the body of the email, or if the input specifies that the email should have no subject, indicate that there is no subject.
"""
response = chat_session.send_message(f"{user_input}. \n{complementary_input}")

# Extract the AI response text
ai_response = response.text

#Test part (make the response and ai_response in comments)
'''ai_response = """
To: fathallah.youssef@etudiant-fst.utm.tn
Subject: 
Body: this is a test mail without subject
"""'''

# Print the AI response (optional)
print("\n\nAlright, here's my proposal. It will be delivered shortly:\n", flush=True)
time.sleep(1.25)
print(ai_response)

# Functions to extract the recipient mails (recipient, cc, bcc), the subject and the body of the mail
def extract_recipient_mails(ai_response):
  mail_session = model.start_chat(
    history=[]
  )
  return mail_session.send_message(f"Extract all email addresses of the recipients ('To:' only) from the following mail. Write only the email addresses separated by commas, nothing else. If there aren't any email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')

def extract_cc_mails(ai_response):
  mail_session = model.start_chat(
    history=[]
  )
  return mail_session.send_message(f"Extract all cc email addresses of the recipients from the following mail. Write only the cc email addresses separated by commas, nothing else. If there aren't any cc email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')

def extract_bcc_mails(ai_response):
  mail_session = model.start_chat(
    history=[]
  )
  return mail_session.send_message(f"Extract all bcc email addresses of the recipients from the following mail. Write only the bcc email addresses separated by commas, nothing else. If there aren't any bcc email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')


def extract_subject(ai_response):
  subject_session = model.start_chat(
    history=[]
  )
  return subject_session.send_message(f"Extract only the subject from the following mail. Write only the subject, nothing else. If there isn't any subject or 'No subject', write None\n\n{ai_response}").text

def extract_body(ai_response):
  body_session = model.start_chat(
    history=[]
  )
  return body_session.send_message(f"Extract only the body from the following mail. Write only the body, nothing else. If there isn't any body or 'No body', write None.\n\n{ai_response}").text

# Function to send an email
def send_email(subject, body, recipient_emails, cc_emails, bcc_emails):
    # Sender email credentials
    sender_email = os.getenv("sender_mail")
    app_password = os.getenv("password")  # Use the 16-digit App Password

    #initializing the subject and body in case of None
    if subject.strip() == "None":
      subject = "No Subject - Generated by AI"
      print(f"No subject detected, changed it to default value: \n{subject} \n")
    if body.strip() == 'None' or body == os.getenv("signature"):
      body = f"No body - Generated by AI \n\n{os.getenv("signature")}"
      print(f"No body detected, changed it to default value: \n{body} \n")

    #initializing the recipients, cc and bcc mails in case of None
    if "None" in [email.strip() for email in recipient_emails]:
      recipient_emails = [os.getenv("default_recipient_email")]
      print(f"No recipient email detected, changed it to default value: \n{str(recipient_emails)} \n")
    if "None" in [email.strip() for email in cc_emails]:
      cc_emails = []
    if "None" in [email.strip() for email in bcc_emails]:
      bcc_emails = []
    
    #Adding the signature in case there is not
    if os.getenv("signature") not in body:
      body = body + '\n\n' + os.getenv("signature")
    
    # Compose the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] =  ', '.join([email.strip() for email in recipient_emails])
    if cc_emails:
       message["Cc"] = ', '.join([email.strip() for email in cc_emails])
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Combine all recipients for the sendmail function
    all_recipients = recipient_emails + cc_emails + bcc_emails

    # Connect to the SMTP server (in this case, Gmail's SMTP server)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, all_recipients, message.as_string())

    print("\n\nSending the mail", end='', flush=True)
    for i in range(3):
        print('.', end='', flush=True)
        time.sleep(1.25)
    print('\n', end='')
    print("Email sent successfully!")

# Calling the send_email() function with AI response as the body
send_email(subject=extract_subject(ai_response), body=extract_body(ai_response), recipient_emails=extract_recipient_mails(ai_response), cc_emails=extract_cc_mails(ai_response), bcc_emails=extract_bcc_mails(ai_response))