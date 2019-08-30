import re
import configparser
import smtplib
import logging
from email.mime.text import MIMEText

from git import Repo

LOGGER = None
ALREADY_UP_TO_DATE = 'Already up to date.'


class GitPullEmailParser(configparser.ConfigParser):

    def __init__(self, config_path):
        super().__init__()
        self.read(config_path)

    def getlist(self, section, option):
        return self.get(section, option).split(',')


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


def replace_variables(configparser, section, value):
    results = re.findall(r'\{\{\w+\}\}', value)
    product = value

    for result in results:
        if result == '{{section}}':
            product = product.replace(result, section)
        else:
            product = product.replace(result, configparser.get(section, result[2:-2], fallback=result))

    return product


def logger():
    logger = logging.getLogger('gitpullemail')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler('gpe.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def process():
    cp = get_configparser()
    repos = cp.sections()

    for repo in repos:
        LOGGER.info('Checking for changes in %s' % repo)
        result = git_pull(cp.get(repo, 'repo_path'))
        if result != ALREADY_UP_TO_DATE:
            LOGGER.info('Changes detected, sending e-mail')
            send_email(cp.get(repo, 'smtp_host'),
                       cp.get(repo, 'email_from'),
                       cp.getlist(repo, 'email_to'),
                       replace_variables(cp, repo, cp.get(repo, 'email_subject')),
                       replace_variables(cp, repo, cp.get(repo, 'email_text')))


if __name__ == "__main__":
    LOGGER = logger()
    process()
