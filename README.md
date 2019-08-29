# gitpullemail

Perform a git pull on a repo and send an email if something changed.

## Installation

1. `git clone <this_repo_path>`
2. create an environment
   1. `virtualenv venv`
   2. `source venv/bin/activate`
   3. `pip install -r requirements.txt`
3. fill in settings.cfg
4. run `python main.py`

## Cron job

To run hourly you could add this line to your crontab:

    0 * * * * cd /path/to/this/repo && python gpe.py
