import os
import re
import smtplib
import time
import imaplib
import email
import markdown2
import google.generativeai as genai
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from dotenv import load_dotenv

class Email:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.sender_email = os.getenv("sender_mail")
        self.app_password = os.getenv("password")
        self.signature = os.getenv("signature")

    def to_markdown(self, text):
    # Replace bullet points with Markdown asterisks
        text = text.replace('•', '  *')
        
        # Convert bold text wrapped in **bold** or __bold__
        text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', text)
        text = re.sub(r'__(.*?)__', r'**\1**', text)
        
        # Convert italic text wrapped in *italic* or _italic_
        text = re.sub(r'\*(.*?)\*', r'*\1*', text)
        text = re.sub(r'_(.*?)_', r'*\1*', text)
        
        # Indent every line of text with '> ' to format as blockquote
        return text

    def extract_recipient_mails(self, ai_response, model):
        mail_session = model.start_chat(
        history=[]
      )
        return mail_session.send_message(f"Extract all email addresses of the recipients ('To:' only) from the following mail. Write only the email addresses separated by commas, nothing else. If there aren't any email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')


    def extract_cc_mails(self, ai_response, model):
        mail_session = model.start_chat(
        history=[]
      )
        return mail_session.send_message(f"Extract all cc email addresses of the recipients from the following mail. Write only the cc email addresses separated by commas, nothing else. If there aren't any cc email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')


    def extract_bcc_mails(self, ai_response, model):
        mail_session = model.start_chat(
        history=[]
      )
        return mail_session.send_message(f"Extract all bcc email addresses of the recipients from the following mail. Write only the bcc email addresses separated by commas, nothing else. If there aren't any bcc email addresses, or a malformed one, write None. If the address has '@example.com', write None:\n\n{ai_response}").text.split(',')


    def extract_subject(self, ai_response, model):
        subject_session = model.start_chat(
        history=[]
      )
        return subject_session.send_message(f"Extract only the subject from the following mail. Write only the subject, nothing else. If there isn't any subject or 'No subject', write None\n\n{ai_response}").text


    def extract_body(self, ai_response, model):
        body_session = model.start_chat(
        history=[]
      )
        return body_session.send_message(f"Extract only the body from the following mail. Write only the body, nothing else. The body starts with 'Dear ...' or something similar and ends with the signature. If there isn't any body or 'No body', write None.\n\n{ai_response}").text


    def extract_attachments(self, ai_response, model):
        attachments_session = model.start_chat(
        history=[]
      )
        attachments = attachments_session.send_message(f"Extract only the attachments from the following mail. Write only the attachments separated by commas (','), nothing else. If there isn't any attachments or 'No attachments', write None.\n\n{ai_response}").text.split(',')
        if "None" in [attachment.strip() for attachment in attachments]:
            attachments = []
        return attachments

    def extract_reply_info(self, ai_response):
        return bool(re.search('Re:', ai_response))

    def extract_forward_info(self, ai_response):
        return bool(re.search('Fwd:', ai_response))

    def extract_time(self, ai_response, model):
        time_session = model.start_chat(
            history=[]
        )
        send_time = time_session.send_message(
            f"Extract the time in which the mail will be sent. If it's written something like 'in 5 minutes', calculate it given the fact that now the time is {datetime.datetime.now()}. The result must be strictly follow this structure: (year, month, day, hour, minute, second). If one of these information is not provided, write 0. If there's any information about the time to send, write the now time following the structure mentioned earlier. Do not include any additional text or code in your response. Here is the mail to analyze: \n{ai_response}"
        ).text
        # Remove any leading/trailing spaces and parentheses
        send_time = send_time.strip().strip('()')
        # Split the response by comma and strip any extra spaces
        time_values = [int(value.strip()) for value in send_time.split(',')]
        scheduled_time = datetime.datetime(*time_values)
        # Ensure the scheduled time is at least 10 seconds in the future
        if scheduled_time <= datetime.datetime.now() + datetime.timedelta(seconds=10):
            scheduled_time = datetime.datetime.now() + datetime.timedelta(seconds=10)
        return scheduled_time

    def extract_mail_id(self, search_subject):
        try:
            # Connect to the Gmail IMAP server
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(os.getenv("sender_mail"), os.getenv("password"))

            # Select the mailbox you want to use (in this case, the inbox)
            mail.select("inbox")

            # Ensure the search subject is properly encoded
            encoded_subject = f'"{search_subject.strip()}"'

            # Search for emails with the specified subject
            status, messages = mail.search(None, 'SUBJECT', encoded_subject)

            # If no messages found, return None
            if status != "OK" or not messages[0]:
                print("No messages found.")
                return None

            # Get the list of email IDs
            email_ids = messages[0].split()

            # Fetch the latest email's headers
            status, msg_data = mail.fetch(email_ids[-1], "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    msg_id = msg["Message-ID"]
                    print(f"Original message-ID: {msg_id}")
                    return msg_id

            # Logout from the server
            mail.logout()
        except Exception as e:
            print(f"An error occurred while determining the original mail Id: {e}")
            return None


    def send_email(self, ai_response, reply_info, forward_info, model):
        try:
            subject = self.extract_subject(ai_response, model)
            recipient_emails = self.extract_recipient_mails(ai_response, model)
            cc_emails = self.extract_cc_mails(ai_response, model)
            bcc_emails = self.extract_bcc_mails(ai_response, model)

            if not forward_info:
                body = self.extract_body(ai_response, model)
                attachments = self.extract_attachments(ai_response, model)
            else:
                while subject.strip().lower().startswith("fwd: "):
                    subject = subject.strip()[5:]
                subject = subject.strip()
                original_msg_id = self.extract_mail_id(subject)
                if original_msg_id:
                    try:
                        mail = imaplib.IMAP4_SSL('imap.gmail.com')
                        mail.login(self.sender_email, self.app_password)
                        mail.select('inbox')

                        result, data = mail.search(None, f'(HEADER Message-ID "{original_msg_id}")')
                        if result != 'OK':
                            raise ValueError(f"Failed to find email with message-ID {original_msg_id}")

                        email_ids = data[0].split()
                        if not email_ids:
                            raise ValueError(f"No email found with message-ID {original_msg_id}")

                        result, data = mail.fetch(email_ids[0], '(RFC822)')
                        if result != 'OK':
                            raise ValueError(f"Failed to fetch email with ID {email_ids[0]}")

                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        mail.logout()
                    except Exception as e:
                        print(f"Failed to fetch email: {e}")
                        return None
                    if msg is None:
                        return

                    original_body = ""
                    attachments = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                attachments.append(filename)
                                with open(filename, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                            elif content_type == "text/plain" or content_type == "text/html":
                                original_body += part.get_payload(decode=True).decode()
                    else:
                        original_body = msg.get_payload(decode=True).decode()

                    original_from = msg["From"]
                    original_date = msg["Date"]
                    original_subject = msg["Subject"]
                    body = f"""---------- Forwarded message ---------\n
                        From: {original_from}\n
                        Date: {original_date}\n
                        Subject: {original_subject}\n
                    """
                    body += f"\n{original_body}"

                    # Print the mail to forwrad
                    print(f"To: {recipient_emails} \nCc: {cc_emails} \nBcc: {bcc_emails} \nSubject: Fwd: {subject} \nBody: \n{body} \nAttachments: {attachments}")


            if subject.strip() == "None":
                subject = "No Subject - Generated by AI"
                print(f"No subject detected, changed it to default value: \n{subject} \n")
            if body.strip() == 'None' or body == self.signature:
                body = f"No body - Generated by AI \n\n{self.signature}"
                print(f"No body detected, changed it to default value: \n{body} \n")

            if "None" in [email.strip() for email in recipient_emails]:
                recipient_emails = [os.getenv("default_recipient_email")]
                print(f"No recipient email detected, changed it to default value: \n{recipient_emails[0].strip()} \n")
            if "None" in [email.strip() for email in cc_emails]:
                cc_emails = []
            if "None" in [email.strip() for email in bcc_emails]:
                bcc_emails = []

            if self.signature not in body:
                body = body + '\n \n' + self.signature

            body = self.to_markdown(body)
            body = markdown2.markdown(body)

            if reply_info:
                while subject.strip().lower().startswith("re: "):
                    subject = subject.strip()[4:]
            subject = subject.strip()

            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = ', '.join([email.strip() for email in recipient_emails])
            if cc_emails:
                message["Cc"] = ', '.join([email.strip() for email in cc_emails])
            message["Subject"] = subject
            if reply_info:
                original_msg_id = self.extract_mail_id(subject)
                if original_msg_id:
                    message["In-Reply-To"] = original_msg_id
                    message["References"] = original_msg_id
            message.attach(MIMEText(body, "html"))

            for attachment in attachments:
                try:
                    attachment = attachment.strip()
                    with open(attachment, "rb") as attachment_file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment_file.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {os.path.basename(attachment)}",
                    )
                    message.attach(part)
                except Exception as e:
                    print(f"Error attaching file {attachment}: {e}")

            all_recipients = recipient_emails + cc_emails + bcc_emails

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, all_recipients, message.as_string())

            print("\n\nSending the mail", end='', flush=True)
            for i in range(3):
                print('.', end='', flush=True)
                time.sleep(1.25)
            print('\n', end='')
            print("Email sent successfully!")
            

        except Exception as e:
            print(f"failed to send email: {e}")
        finally:
            try:
                sys.exit()
            except SystemExit:
                pass

    def start_scheduler(self, send_time, ai_response, reply_info, forward_info, model):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.send_email, 'date', run_date=send_time, args=[ai_response, reply_info, forward_info, model])
        print(f"Email scheduled for {send_time}")
        scheduler.start()
        # Keep the scheduler running
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()


def main():
  load_dotenv()
# Configure the AI model with the API key
  genai.configure(api_key=os.getenv("api_key"))

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
    Based on the input provided above, these are few rules to respect while writing the mail (write only the mail, nothing else):
    1- Take in consideration that the mail must strictly respect the following structure:
    To: [recipient_mail(s)]
    Cc: [cc_mail(s)]
    Bcc: [bcc_mail(s)]
    Subject: [Subject of the mail] OR [Re: [Subject of the mail]] if the mail is a reply OR [Fwd: [Subject of the mail]] if the mail is to forward
    Body: [Body of the mail]
    {os.getenv("signature")} (instead of [Your Name]).
    Attachments: path/to/file1.txt, path/to/file2.jpg, ...
    Send time: [any information provided in the input]
    2- If there are many recipient email addresses, the body of the mail sould start by: "Dear all,..."
    3- If there is any recipient email address provided in the input, just write a placeholder [recipient_mail].
    4- If a correct email address is not provided in the input, do not generate or substitute it with an example address like "name@example.com" or "name@domain.com", just write a placeholder [recipient_mail] instead.
    5- Check in the input if there is a suspicious word that you didn't understand, it could be the name of the recipient.
    6- If there is no name of the recipient provided, try at first to extract it from the recipient mail address.
    7- In case it is impossible to guess the recipient name, do not include a placeholder [recipient_name]. Write instead Dear Mr/Miss.
    8- Apply the same previous rule for any additional information in the body of the mail (project name, company name...)-Avoid placeholders.
    9- If you find that the mail content might seem inappropriate or disrespectful, rewrite it to be polite and professional without warning the user.
    10- If there is nothing to write in the body of the email, indicate that there is no body without warning the user.
    11- If there is no subject mentionned explicitly in the input, then the subject should be derived from the content of the body.
    12- If you can't derive a subject from the body of the email, or if the input specifies that the email should have no subject, indicate that there is no subject.
    """
  final_input=user_input+'. \n'+complementary_input
  response = chat_session.send_message(f"{final_input}")
    # Extract the AI response text
  ai_response = response.text
    # Print the AI response (optional)
  print("\n\nAlright, here's my proposal. It will be delivered shortly:\n", flush=True)
  time.sleep(1.25)
  email_sender = Email()
  send_time=email_sender.extract_time(ai_response, model)
  subject=email_sender.extract_subject(ai_response, model)
  reply_info=email_sender.extract_reply_info(subject)
  forward_info=email_sender.extract_forward_info(subject)
  if not forward_info:
      print(ai_response)
  try:
      email_sender.start_scheduler(send_time, ai_response, reply_info, forward_info, model)
      print("main program finished")
      sys.exit(0)
  except Exception as e:
       print(f"An error occured: {e}")


if __name__ == '__main__':
    main()
