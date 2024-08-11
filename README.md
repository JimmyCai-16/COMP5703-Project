# PLATFORM SETUP INSTRUCTIONS
To understand the Company Guidelines for Programming, click [here][Guidelines]

In case you can't see the images below, please check `Platform Setup Instructions` in the link above.

[PostgreSQL]: https://www.postgresql.org/download/
[Python]: https://www.python.org/downloads/release/python-3810/
[Brew]: https://brew.sh/
[Guidelines]: https://drive.google.com/drive/folders/1zdl1Sj5JfqQgwdTPyQeEQtGngYgkfSun?usp=drive_link

## Contents

- [PLATFORM SETUP INSTRUCTIONS](#platform-setup-instructions)
  - [Contents](#contents)
  - [Install PostGIS Database](#install-postgis-database)
  - [pgAdmin4](#pgadmin4)
  - [SQL Shell](#sql-shell)
  - [Using Terminal](#using-terminal)
  - [VS CODE EXPLORER](#vs-code-explorer)
  - [Final Steps](#final-steps)
  - [MacOS GDAL Installation](#macos-gdal-installation)
- [Installation Errors](#installation-errors)
  - [Errors installing requirements.txt](#errors-installing-requirementstxt)
  - [MacOS Installation Issues](#macos-installation-issues)
  - [Windows GDAL Installation Issue](#windows-gdal-installation-issue)

## Install PostGIS Database
- [Install the latest version of PostgreSQL][PostgreSQL]
- Go with the default settings for everything except for things mentioned below.
- Check “ADD TO PYTHON PATH” or something similar on one of the pages.
- You might be asked to create a password during installation, make the password as `pass`(or change the passwords in the later steps).
- When on this page, select PostGIS in spatial extensions:

![gisExtension](https://i.imgur.com/wnGnOgX.jpg)

- After the page above, you might encounter a checkbox to create a spatial database, no need to check that.
- SQL Shell and pgAdmin4 will be installed automatically once the installation above finishes.

## pgAdmin4
- Open `pgAdmin4` and log in with the password used during installation.
- Go to `Servers -> PostgreSQL 15 -> Databases` and right-click it to create a new database named `django`.
- Go to `Servers -> PostgreSQL 15 -> Databases -> django -> extensions`
- Right-click on extensions and select `create -> extension`
 
 ![Screenshot (3)](https://i.imgur.com/0x3FU3j.png)

- Search and select `postgis` extension from the options(option not available in the image as already added)
  
  ![Screenshot 2023-08-02 171834](https://i.imgur.com/pfio3Oh.png)

## SQL Shell
- Open `SQL Shell`. Everything in square brackets is the default value. Hit enter to keep the default values. Only change the default value of Database to `django` and Password to `pass` (installation password).

  ![Untitled](https://i.imgur.com/4sxaVhE.png)

## Using Terminal

- Clone this repo and change directory in the terminal to where the repo is stored. 
- [Install Python version 3.8][Python]
- Execute the code in a terminal (command prompt for Windows users):
- Check if Python version 3.8 is installed using `py -0`.
- Create and activate virtual environment:
 ```shell
  py -3.8 -m venv venv
  .\venv\Scripts\activate.bat
```
- Install all the required packages:
```shell
  py -m pip install --upgrade pip setuptools wheel
  pip install GDAL-3.3.3-cp38-cp38-win_amd64.whl
  pip install -r requirements.txt
```
- Check if the requirements were installed using `pip list`


## VS CODE EXPLORER
- Navigate to the project's web folder and copy contents of `.env_defaults` onto a new `.env` file.
- Make these changes in .env (installation password is used here)
  
![Screenshot 2023-08-03 093340](https://i.imgur.com/ONJ02fT.png)

<!-- - Then go to your virtual environment folder (venv) outside the web folder and move to `venv -> Lib -> djconfig -> admin.py` and edit line 29.
  	Change
                  `from django.conf.urls import url`
        to
                  `from django.urls import re_path as url` -->


## Final Steps
- Make sure the directory is changed to `web` before executing the following (command prompt for Windows users):
```
cd web
python delete_migrations.py & python manage.py makemigrations & python manage.py migrate
```
- Install `Firefox` web browser		(contains drivers needed for the platform)
- Within the same terminal, execute: `python manage.py runserver`
- Visit this link http://127.0.0.1:8000/
- Register an account and you are ready to use the application

## MacOS GDAL Installation
- [Install brew][Brew]
- Run the following command in your terminal: `brew install gdal`
- Open web/main/settings.py and add the following lines at the end of the file:
	`GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.5.3/lib/libgdal.31.dylib'`
	`GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/geos/3.11.0/lib/libgeos_c.1.dylib'`
- Replace the version numbers with the versions you have installed

# Installation Errors
The following are solutions to the most common problems with the setup.
In case you are still unable to set up the platform, email sahaj@orefox.com with a screenshot of the issue to help you out.

## Errors installing requirements.txt
In case you are having issues with particular packages:
- get the name of the package from the error displayed in the terminal
- final that package name in the requirements.txt file
- add `#` to the left of the package name (this comments the package out of the installation process)
- save the requirements.txt file using `ctrl + s`
- install the requirements file again `pip install -r requirements.txt`
- repeat the process for all packages that give errors
- Install the packages that have been commented out using `pip install <package name and version from the requirements.txt file`, e.g. `pip install Pillow==8.4.0`

## MacOS Installation Issues
In case you are facing an issue installing gssapi
- try fixing the missing GSSAPI_MAIN_LIB variable using the command: `export GSSAPI_MAIN_LIB=/System/Library/Frameworks/GSS.framework/Versions/Current/GSS`
- Install Pillow package: `pip install Pillow==8.4.0`

## Windows GDAL Installation Issue
If installing gdal via pip either doesn't work or isnt recognized, doing the following will work on both Windows 10 and 11:
- Run `pip debug --verbose` and look for compatible tags, e.g., cp38-cp38-win_amd64
- Download the GDAL wheel from Christoph Gohlke's Unofficial Windows Binaries for Python Extension Packages. 
- Use the tags found above to determine which wheel you download.
- Install via pip install '/path/to/GDAL-3.3.3‑cp38-cp38-win_amd64.whl' (or whatever wheel it was you downloaded)
- Navigate to `/path/to/venv/Lib/site-packages/osgeo/`and take note of the `gdalXXX.dll` files name e.g., `gdal304.dll`
-The version name of the dll found above needs to be added to the `/path/to/venv/lib/site-packages/django/contrib/gis/gdal/libgdal.py` file here:
```
elif os.name == 'nt':
    # Windows NT shared libraries
    lib_names = ['gdal304', 'gdal300', 'gdal204', 'gdal203', 'gdal202', 'gdal201', 'gdal20']
	# ^ add dll name to this array if its not there
  ```
Add the following code block to your django settings.py if it does not exists (within the main folder project folder, not site-packages) before the initialization of any packages:
```
if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj') + ';' + os.environ['PATH']
```
Finished! Now continue with the regular setup of django.
Note: If there are still issues, it's possible you might need to install GDAL on windows. As there aren't any binaries available on the GDAL website and you have to build it yourself. The easiest way to install it is by using the network installer for OSGeo4W, just do an express installation but make sure to select GDAL as an additional package.

# COMP5703-Project
All codes related to the COMP5703 CS36 project (e.g. AI-model &amp; Web Application)
