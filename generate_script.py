import csv
import json
import os
from threading import Thread

import falcon
import jinja2

from commons.logger import set_up_logging
from script_buddy.utils import load_model, generate, send_mail
from config import SENDER_EMAIL_CREDENTIALS, ADMIN_EMAIL_CREDENTIALS

logger = set_up_logging()


class Success:
    def on_get(self, req, resp):
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/script/success.html')
        html_content = open(html_path, 'r').read()
        html_template = jinja2.Template(html_content)

        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/script/script.css')
        css_content = open(css_path, 'r').read()

        resp.body = html_template.render(css_content=css_content)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML


class StaticResource:
    def on_get(self, req, resp, file_name):
        img_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/%s' % file_name)
        with open(img_path, 'rb') as out:
            resp.body = out.read()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_PNG


class Script:
    def __init__(self):
        logger.info('Loading GPT2 model.................')
        self._model, self._tokenizer = load_model()
        logger.info('Model loaded')

    def generate_script(self, context, max_length):
        sample_script = generate(self._model, self._tokenizer, input_text=context, max_length=max_length)
        return sample_script

    def process_context(self, email, context, max_length, first_name, last_name):
        try:
            logger.info('Generating script')
            generated_script = self.generate_script(context, max_length)
            logger.info('Generated script: %s' % generated_script)

            logger.info('Sending email')
            generated_script = generated_script if generated_script else \
                "Sorry, the script cannot be generated due to technical issues. Please retry again."
            mail_content = "Thanks for assisting us at Bookscribs.io to improve our algorithms and your user experience." \
                           "\n" \
                           "Please feel free to generate as many scripts as possible periodically to see how the system improves." \
                           "\n\n" \
                           "Your Story Submission:\n" + context \
                           + '\n\n' + \
                           'At Bookscribs.io, our first goal is to generate a standardized ' \
                           'screenplay structure, then iterate to produce amazing stories that will evolve into ' \
                           'award-winning and highly successful film scripts. ' \
                           '\n\nBelow is the initial development of our vision.\n\n' \
                           'Please note: Your generated screenplay will contain errors, laughable moments, ' \
                           'weird characters, strange ideas; and, even diverse storylines unlike what you\'ve probably imagined. ' \
                           'That\'s okay; with your help, we will improve radically.' \
                           '\n\n' + \
                           'Your Generated Script:\n' + generated_script + \
                           '\n\n' + \
                           'Thank you for your contribution to Bookscribs.io - Let\'s rewrite your stories for the movie screens!'

            send_mail(SENDER_EMAIL_CREDENTIALS['email_id'], SENDER_EMAIL_CREDENTIALS['password'],
                      ADMIN_EMAIL_CREDENTIALS['email_id'], email, mail_content)
            logger.info('Email sent')

            logger.info('Writing data to csv')
            file = os.path.join(os.path.dirname(__file__), 'data/leads/leads.csv')
            Files().save_data_into_file(file, email, context, max_length, first_name, last_name, generated_script)
            logger.info('Data written to csv')
        except Exception as e:
            logger.error('Exception occurred while processing context in thread')
            logger.error(str(e))

    def on_get(self, req, resp):
        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/script/script.html')
        html_content = open(html_path, 'r').read()
        html_template = jinja2.Template(html_content)

        js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/script/script.js')
        js_content = open(js_path, 'r').read()

        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/script/script.css')
        css_content = open(css_path, 'r').read()

        resp.body = html_template.render(js_content=js_content, css_content=css_content)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML

    def on_post(self, req, resp):
        logger.info('script generation invoked')
        try:
            data = req.params
            email = data.get('email', None)
            context = data.get('context', None)
            max_length = data.get('max_length', None)
            first_name = data.get('first_name', None)
            last_name = data.get('last_name', None)
            if not email or not context or not max_length or not first_name or not last_name:
                logger.error('Context or max length missing for script generation')
                resp.status = falcon.HTTP_412
                return

            Thread(target=self.process_context, args=(email, context, int(max_length), first_name, last_name)).start()

            resp.body = json.dumps('Success')
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as e:
            logger.error('Exception occurred while generating script')
            logger.error(str(e))
            resp.status = falcon.HTTP_500


class Files:
    def __init__(self):
        pass

    def save_data_into_file(self, file, email, context, max_length, first_name, last_name, generated_script):
        heading = ['First Name', 'Last Name', 'Email', 'Context', 'Max Length', 'Generated Script']
        contents = [first_name, last_name, email, context, max_length, generated_script]
        self.write_contents_to_file(file, heading, contents)

    def write_contents_to_file(self, file, heading, contents):
        lines = self.create_file_if_not_exists(file, heading)

        with open(file, 'a') as writeFile:
            writer = csv.writer(writeFile)
            if lines is not None and len(lines) < 1:
                writer.writerow(heading)
            # for row in contents:
            writer.writerow(contents)

    def create_file_if_not_exists(self, file, heading):
        try:
            with open(file, 'r') as readFile:
                reader = csv.reader(readFile)
                lines = list(reader)
                return lines
        except FileNotFoundError:
            with open(file, 'a') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerow(heading)
                return None


if __name__ == '__main__':
    context = 'Untold words of a heart is a fictional romance. A lighthearted young boy Riyal sees Aadya for the first time in his educational consultancy while applying for masters in the same university as hers. He thought, It was all just the infatuation, but it was only after a few years Aadya came into his life and everything changed.'
    email = 'bbbalu47@gmail.com'
    script = Script().process_context(email, context, 250)
    print(script)
