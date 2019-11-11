import logging
import os
import re
import smtplib
from configparser import DEFAULTSECT, ConfigParser
from email.mime.text import MIMEText

from git import Repo, exc

LOGGER = None
ALREADY_UP_TO_DATE = 'Already up to date.'


class GitPullEmailParser(ConfigParser):

    def __init__(self, config_path):
        super().__init__()
        self.read(config_path)

    def getfirst(self, sections, option):
        for section in sections:
            value = self.get(section, option)
            if value is not None:
                return value

        return None

    def getfirstlist(self, sections, option):
        return self.getfirst(sections, option).split(',')


def set_cwd():
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)


def get_configparser():
    return GitPullEmailParser('settings.ini')


def git_pull(repo_dir):
    try:
        repo = Repo(repo_dir)
        return repo.git.pull()
    except exc.GitError as e:
        LOGGER.error(e)


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


def logger(level):
    logger = logging.getLogger('gitpullemail')
    logger.setLevel(logging.getLevelName(level))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler('gpe.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def process():
    global LOGGER
    set_cwd()
    cp = get_configparser()
    LOGGER = logger(cp.get(DEFAULTSECT, 'logging_level'))
    repos = cp.sections()

    for repo in repos:
        sections = [repo, DEFAULTSECT]
        result = git_pull(cp.getfirst(sections, 'repo_path'))
        if result != ALREADY_UP_TO_DATE:
            LOGGER.info('Changes detected in %s, sending e-mail' % repo)
            send_email(cp.getfirst(sections, 'smtp_host'),
                       cp.getfirst(sections, 'email_from'),
                       cp.getfirstlist(sections, 'email_to'),
                       replace_variables(cp, repo, cp.getfirst(sections, 'email_subject')),
                       replace_variables(cp, repo, cp.getfirst(sections, 'email_text')))
        else:
            LOGGER.info('No changes detected in %s' % repo)


if __name__ == "__main__":
    process()
