import logging
import os
import re
import smtplib
from configparser import DEFAULTSECT, ConfigParser
from email.mime.text import MIMEText

from git import Repo, exc

LOGGER = None
BLANK = ''


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

    def getfirstlist(self, sections, option, trim=True):
        result = self.getfirst(sections, option).split(',')
        if trim:
            return [x.strip() for x in result]
        else:
            result


def set_cwd():
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)


def get_configparser():
    return GitPullEmailParser('settings.ini')


def git_diff(repo_dir):
    try:
        repo = Repo(repo_dir)
        repo.git.fetch()
        result = repo.git.diff("origin", name_only=True)
        repo.git.merge()
        return result
    except exc.GitError as e:
        LOGGER.error(e)


def find_diff_with_monitor_paths(diff, monitor_paths):
    lines = diff.splitlines()
    result = []

    for line in lines:
        for path in monitor_paths:
            escaped_path = re.escape(path)
            escaped_path = escaped_path.replace('\\*', '.*')
            if re.match(escaped_path, line):
                result.append(line)
                break

    return result


def send_email(host, frm, to, subject, text):
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = frm
    msg['To'] = ', '.join(to)

    s = smtplib.SMTP(host)
    s.sendmail(frm, to, msg.as_string())
    s.quit()


def replace_variables(configparser, section, diff, value):
    results = re.findall(r'\{\{\w+\}\}', value)
    product = value

    for result in results:
        if result == '{{section}}':
            product = product.replace(result, section)
        elif result == '{{diff}}':
            product = product.replace(result, '\n'.join(diff))
        else:
            piece = configparser.get(section, result[2:-2], fallback=result)

            if result == '{{repo_monitor_paths}}':
                product = product.replace(result, piece.replace(',', '\n'))
            else:
                product = product.replace(result, piece)

    return product


def logger(level_global, level):
    logging.basicConfig(level=level_global, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('gitpullemail')
    logger.setLevel(level)

    fh = logging.FileHandler('gpe.log')
    logger.addHandler(fh)

    return logger


def process():
    global LOGGER
    set_cwd()
    cp = get_configparser()
    LOGGER = logger(cp.get(DEFAULTSECT, 'logging_level_global'), cp.get(DEFAULTSECT, 'logging_level'))
    repos = cp.sections()

    for repo in repos:
        sections = [repo, DEFAULTSECT]
        diff = git_diff(cp.getfirst(sections, 'repo_path'))
        if diff != BLANK:
            monitored_diff = find_diff_with_monitor_paths(diff, cp.getfirstlist(sections, 'repo_monitor_paths'))
            if monitored_diff:
                LOGGER.info('Changes detected in %s, sending e-mail. The changes:\n%s' % (repo, '\n'.join(monitored_diff)))
                send_email(cp.getfirst(sections, 'smtp_host'),
                           cp.getfirst(sections, 'email_from'),
                           cp.getfirstlist(sections, 'email_to'),
                           replace_variables(cp, repo, monitored_diff, cp.getfirst(sections, 'email_subject')),
                           replace_variables(cp, repo, monitored_diff, cp.getfirst(sections, 'email_text')))
            else:
                LOGGER.info('No changes detected in %s' % repo)
        else:
            LOGGER.info('No changes detected in %s' % repo)


if __name__ == "__main__":
    process()
