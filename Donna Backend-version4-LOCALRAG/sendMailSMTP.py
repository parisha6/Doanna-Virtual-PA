import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List


def send_email(sender_email: str, receiver_emails: List[str], password: str, subject: str, body: str) -> None:
    """
    Sends an email using Gmail's SMTP server.

    Parameters:
    sender_email (str): The email address of the sender.
    receiver_emails (List[str]): A list of email addresses to receive the email.
    password (str): The password or app password for the sender's Gmail account.
    subject (str): The subject of the email.
    body (str): The body content of the email.

    Returns:
    None: This function does not return a value. It attempts to send the email 
          and prints an error message if it fails.
    """
    # Set up the MIME (Multipurpose Internet Mail Extensions)
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)  # Join the list of email addresses with a comma
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))  # Attach the body of the email as plain text

    try:
        # Connect to Gmail's SMTP server using SSL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

        # Log in to the server using your credentials
        server.login(sender_email, password)

        # Send the email to multiple recipients
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        print("Email sent successfully!")

        # Close the connection to the server
        server.quit()

    except Exception as e:
        # Print any error that occurs during the sending process
        print(f"Error: {e}")


def main() -> None:
    """
    Main function to set up email details and call the send_email function.

    This function defines the email sender, receiver(s), subject, and body content
    and then invokes the send_email function to send the email.

    Returns:
    None
    """
    # Your email details
    sender_email = "mamulpuri@gmail.com"
    receiver_emails = [
        "ashutoshmishra2808@gmail.com",
        "ashutoshmishra280897@outlook.com",
        "misha02@pfw.edu"
    ]
    password = "<your-app-password>"  # Replace with your Gmail app password

    # Email content
    subject = "Test Email"
    body = "This is a test email sent using Python SMTP."

    # Call the send_email function to send the email
    send_email(sender_email, receiver_emails, password, subject, body)


# Entry point for the script
if __name__ == "__main__":
    main()
