import subprocess
import google.generativeai as genai
import time
import datetime
import os

# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

def main():
  # loading variables from .env file
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
  Subject: [Subject of the mail]
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
  13- If the provided subject in the input is a respond to another mail, write "Re: " followed by the subject.
  """
  final_input=user_input+'. \n'+complementary_input
  response = chat_session.send_message(f"{final_input}")
  # Extract the AI response text
  ai_response = response.text
  # Print the AI response (optional)
  print("\n\nAlright, here's my proposal. It will be delivered shortly:\n", flush=True)
  time.sleep(1.25)
  print(ai_response)
  subprocess.Popen(["python", "send_email.py", "start_scheduler", ai_response], creationflags=subprocess.CREATE_NEW_CONSOLE)

if __name__ == "__main__":
    main()