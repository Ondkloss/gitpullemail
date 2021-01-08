# gitpullemail

Performs a fetch, diff and merge to check if any of your chosen paths are affected by recent changes.

If changes to your chosen paths are detected an email is sent about the change.

## Installation

1. `git clone <this_repo_path>`
2. create an environment
   1. `virtualenv venv`
   2. `source venv/bin/activate`
   3. `pip install -r requirements.txt`
3. `cp settings.ini.example settings.ini`
4. fill in settings.ini
5. run `python gpe.py`

## Cron job

To run hourly you could add this line to your crontab:

    0 * * * * /path/to/repo/gpe.sh

## Scheduled task

To run as a scheduled task execute this command:

    C:\path\to\repo\gpe.bat

## License

The contents of this repo are released under the MIT license.
