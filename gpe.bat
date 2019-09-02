:: BAT which can be used for Windows Task Scheduler
SET DIR=%~dp0
set DIR=%DIR:~0,-1%
%DIR%\venv\Scripts\activate.bat && python %DIR%\gpe.py && %DIR%\venv\Scripts\deactivate.bat
