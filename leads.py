import os
import falcon
import jinja2
import csv
import json


class ViewCreditRequestingLeads:
    def on_get(self, req, resp):
        file_contents = read_file_contents('leads.csv')

        html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates/leads/leads.html')
        with open(html_path, 'r') as f:
            jinja_template = jinja2.Template(f.read())
            html_content = jinja_template.render(title='Leads', leads=file_contents)
            resp.body = html_content
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_HTML


class DownloadCreditRequestingLeads:
    def on_get(self, req, resp):
        leads_csv_path = os.path.join(os.path.dirname(__file__), 'data/leads/leads.csv')
        with open(leads_csv_path, 'r') as f:
            csv_content = f.read()
            resp.body = csv_content

            resp.status = falcon.HTTP_200
            resp.content_type = 'text/csv'
            resp.set_header("Content-Disposition", "attachment; filename=leads.csv")


def read_file_contents(file):
    file_dir_path = os.path.join(os.path.dirname(__file__), 'data/leads')
    file = os.path.join(file_dir_path, file)
    try:
        with open(file, 'r') as readFile:
            reader = csv.reader(readFile)
            lines = list(reader)
            return lines
    except FileNotFoundError:
        return None
