from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import AutoTokenizer, AutoModelWithLMHead

import os
import random
import smtplib
import re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_model(model_dir=None):
    """Loads the saved GPT2 model from disk if the directory exists.
    Otherwise it will download the model and tokenizer from hugging face.
    Returns
    a tuple consisting of `(model,tokenizer)`
    """

    if model_dir is None:
        model_dir = 'models/'
        if not os.path.isdir(model_dir):
            tokenizer = AutoTokenizer.from_pretrained("cpierse/gpt2_film_scripts")
            model = AutoModelWithLMHead.from_pretrained("cpierse/gpt2_film_scripts")
            return model, tokenizer

    tokenizer = GPT2Tokenizer.from_pretrained(model_dir)
    model = GPT2LMHeadModel.from_pretrained(model_dir)
    return model, tokenizer


def generate(model, tokenizer, input_text=None, num_samples=1, max_length=1000):
    model.eval()

    if input_text:
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        output = model.generate(
            input_ids=input_ids,
            do_sample=True,
            top_k=50,
            max_length=max_length,
            top_p=0.95,
            num_return_sequences=num_samples
        )
    else:
        output = model.generate(
            bos_token_id=random.randint(1, 50000),
            do_sample=True,
            top_k=50,
            max_length=max_length,
            top_p=0.95,
            num_return_sequences=num_samples

        )

    decoded_output = ''
    for sample in output:
        decoded_output += tokenizer.decode(sample, skip_special_tokens=True)

    return decoded_output


def send_mail(from_email, password, bcc_email, to_email, content):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Movie Script Generated"
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Bcc'] = bcc_email

    # Create the body of the message (a plain-text and an HTML version).
    text = content
    html = """
            <html>
              <head></head>
              <body>
                     {content}
              </body>
            </html>
            """.format(content=content)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    # part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    # msg.attach(part2)

    # Send the message via local SMTP server.
    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(from_email, password)
    s.sendmail(from_email, [to_email, bcc_email], msg.as_string())
    s.quit()


if __name__ == '__main__':
    from config import SENDER_EMAIL_CREDENTIALS, ADMIN_EMAIL_CREDENTIALS

    mail_content = "I have 10 apples                    and I live in bangalore"
    send_mail(SENDER_EMAIL_CREDENTIALS['email_id'], SENDER_EMAIL_CREDENTIALS['password'],
              'balumatta01@gmail.com', 'balumatta01@gmail.com', mail_content)
