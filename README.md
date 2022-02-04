# Donation Management System


## 1. Overview

This application was created for a charitable organisation to store and modify donations being made to the institution. The intention behind this application was to have control over donations and all their related models apart from the contacts themselves, which are retrieved from an existing external database (SeminarDesk) on creation / modification / deletion. The challenge to this program was defining this distinction, and has involved the use of background tasks and webhooks to fully integrate this program to the institut's existing platform.


## 2. Functionality

- Create / Modify / Delete donations by filling in all their related fields
- Create receipts for eligible donations, either individual receipts for unique donations or annual receipts for a fiscal year
- Filter donations / donators / receipts base on their fields
- Export filtered / non-filtered data of donations and donators to Excel and CSV files
- Retrieve contact information from an external database through the use of webhooks - (the process_webhook_payload function in **dm_page/tasks.py** should be modified to fit the JSON files received or the JSON files should correspond to the existing configuration)
- View contact profile pages with their information and a link to view/modify that contact in the external platform
- Send automatic and manual emails to contacts with regards to their receipts for tax.
In this admin 
- Add locks to donations to prevent them from being modified or deleted
- Cancel receipts with mistakes and a short description as explanation
- Add / Modify / Delete related donation models
- Change Eligibility conditions with regards to a donations organisation and donation type
- Change fiscal year date range, change date for notification reminders to process annual receipts
- Change email parameters such as host, port, subject, body, etc



## 3. Installation 

1. Create a directory where you want to build your environment

2. Clone this project into your directory: `git clone https://github.com/AlexanderHalsey/Donation-Manager`

3. Create a virtual environment within it, activate it, then install dependencies. I personally use venv: `python3 -m venv venv | source venv/bin/activate | pip install -r requirements.txt`

4. Add a database of your choosing such as a db.sqlite3 (change the DATABASE default in **donation/settings.py** if needed) then create random fixtures: `python3 dataset/random_dataset_generator.py`

5. Once you've created the fixtures load them int the database: `python3 manage.py loaddata dataset/fixtures/*.json`

6. Finally give youself a superuser account to log in and you're all set: `python3 manage.py createsuperuser`



## 4. Configurations

There are lots of parameters that you can add to increase the functionality of the application.

### 4.a. Environment file Configurations

Create a `.env` file and include these variables:

`SECRET_KEY=''` 

> Secret key of the application (put secret key within the string)
______________________________

`DEBUG_VALUE = ''`

> Development / Production (put boolean value within the string)
______________________________

`EMAIL_ADDRESS = `

`PASSWORD = `

`SMTP_DOMAIN = `

`SMTP_PORT = `

> These email configurations are used in the eventual case where the pages or background tasks give errors
______________________________

`ADMIN_NAME = `

`ADMIN_EMAIL = `

> Recipient receiving the errors
______________________________

`errortoggle = ''`

> Inject an error in dashboard.html to ensure traceback emails are getting sent (put boolean value within the string))
______________________________

`DMS_WEBHOOK_USERNAME = `

`DMS_WEBHOOK_PASSWORD = `

> If you wish to use the webhooks to connect with an external database you can set the username and password on both ends for a secure connection
>You can find the url of the webhook view function in the `dm_page/urls.py` file
______________________________

`REDIS_TLS_URL =` 

> Use an external redis broker to get the Celery module functioning correctly for background tasks in the dm_page/tasks.py file
> **IMPORTANT**: These tasks include creating receipts, receiving webhook payloads, sending receipt confirmations and traceback emails. **Without this broker connection you will not be able to use these functions**
______________________________

`DROPBOX_OAUTH2_TOKEN = `

> Create a dropbox account and create an authentication token to link application to the dropbox file storage system
> Follow the instructions on this link to set up your dropbox account: https://www.dropbox.com/developers/documentation/python#tutorial
______________________________

`SDID_ACCESS = ` 

> Url to access external database for contacts (This is a particular case where the contact's id suffixes the url address to land you on the contact's page on the external application. This link is used on the individual contacts's page)


### 4.b. Django Admin Configurations

**Admin --> Paramètres généraux (General Settings)**
- Change Fiscal Receipt Date range: *Plage de dates pour l'année fiscale*
- Change Fiscal Receipt release date notification: *Date d'ouverture des reçus annuels*
- Change email settings for sending receipt confirmations: *Configuration des emails*

**Other Settings**
- Cancel receipts that have mistakes on them: *Reçus Fiscaux*
- Change eligibility conditions for donations that have the right to a receipt: *Eligibilité*
- Add / Modify / Delete related donation models: *Forme des dons (form of donations), Mode paiement (Payment Mode), Nature des dons (nature of donations), Types de dons (donation types), Organisations (organisations)* **
- Add locks with date ranges for certain donations to prevent them being modified: Verrouillage

** **IMPORTANT**: Make sure you fill all the fields for Organisations that are to be amongst the eligibility conditions in the Eligibility model. This is to ensure no errors occur when trying to create a pdf receipt containing this particular organisation's model.



## 5. MIT License

Copyright (c) 2021 Donation Management System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.