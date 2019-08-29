import re
import configparser
import smtplib
from email.mime.text import MIMEText

from git import Repo

ALREADY_UP_TO_DATE = 'Already up to date.'


class GitPullEmailParser(configparser.ConfigParser):

    def __init__(self, config_path):
        super().__init__()
        self.read(config_path)
        self.__fetch_config()

    def __fetch_config(self):
        self.repo_name = self.getstring('repo_name')
        self.repo_path = self.getstring('repo_path')
        self.smtp_host = self.getstring('smtp_host')
        self.email_from = self.getstring('email_from')
        self.email_to = self.getlist('email_to')
        self.email_subject = self.getstring('email_subject')
        self.email_text = self.getstring('email_text')

    def getstring(self, option):
        return super().get('root', option)

    def getlist(self, option):
        return self.getstring(option).split(',')


def get_configparser():
    return GitPullEmailParser('settings.cfg')


def git_pull(repo_dir):
    repo = Repo(repo_dir)
    return repo.git.pull()


def send_email(host, frm, to, subject, text):
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = frm
    msg['To'] = ', '.join(to)

    s = smtplib.SMTP(host)
    s.sendmail(frm, to, msg.as_string())
    s.quit()


def replace_variables(configparser, value):
    results = re.findall(r'\{\{\w+\}\}', value)
    product = value

    for result in results:
        product = product.replace(result, configparser.getstring(result[2:-2]))

    return product


def process():
    cp = get_configparser()

    result = git_pull(cp.repo_path)
    if result != ALREADY_UP_TO_DATE:
        send_email(cp.smtp_host, cp.email_from, cp.email_to, replace_variables(cp, cp.email_subject), replace_variables(cp, cp.email_text))


if __name__ == "__main__":
    process()
