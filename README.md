# AI Mail Automation Chatbot Outlook Add-in

## Overview

The **AI Mail Automation Gizmo** is a powerful tool designed to automate email creation and management within Microsoft Outlook. This tool leverages advanced AI capabilities to generate, schedule, and send emails with minimal user input. It is particularly useful for automating repetitive email tasks, such as responding to common inquiries, forwarding emails, and scheduling future messages based on AI-generated content.

## Features

- **AI-Powered Email Generation**: Generate email content, including subject, body, and attachments, using AI responses based on user input.
- **Email Scheduling**: Automatically schedule emails to be sent at a specific time determined by the AI or the user.
- **Reply and Forward Detection**: The add-in can detect if an email is a reply or a forward, formatting the content accordingly.

## How It Works

1. **User Interaction**: The user interacts with the tool through the command prompt, prompting the user for input, such as selecting between sending an AI-generated email immediately or scheduling it for later.

2. **AI Response Generation**: The tool sends the user's input to an AI model, which generates the appropriate email content, then processes the AI response and determines whether the email is a reply or forward, as well as the scheduled time for sending.

3. **Email Formatting**: The content is formatted as a markdown (if needed), and the necessary email headers are added, including reply or forward indicators.

4. **Email Sending**: The tool sends the email immediately or schedules it to be sent at the specified time using the APScheduler Python library.

5. **Background Processing**: A background scheduler runs the email sending operation at the designated time, ensuring that scheduled emails are sent without any manual intervention.

## Getting Started

### Prerequisites

- Python 3.x
- APScheduler (for scheduling emails)

### Installation

1. **Clone the Repository**:
   ```
   git clone https://github.com/your-username/ai-mail-automation-chatbot.git
   cd ai-mail-automation-chatbot
   ```

2. **Set Up the Python Backend**:
   - Install the required Python packages:
     ```
     pip install -r requirements.txt
     ```
   - Start the python file:
     ```
     python send_email_oo.py
     ```

### Usage

- You simply have to follow the on-screen prompt by writing your input, as if you were writing to any AI chatbot.
  Example:
  ```
  Write to example1@domain.com and example2@domain.com to remind them about tomorrow's meeting. example3@domain.com should be in cc and example4@domain.com in bcc. Attach the following file to the mail: 'C:/path/to/the/file' and schedule this mail to be sent in 7 minutes
  ```
  And the tool will take care of the rest of the process.
- You can also adapt your input to respond to a mail
  ```
  Respond to the mail which has 'Mail_Subject' as a subject to confirm that I will assist to the meeting
  ```
  or to forward a mail
  ```
  Forward the mail which has 'Mail_Subject' as a subject to example@domain.com
  ```
