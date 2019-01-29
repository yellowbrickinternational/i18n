from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

LANGUAGES = {'en_GB': 3, 
             'nl_NL': 4, 
             'de_DE': 5,
             'nl_BE': 6,
             'fr_BE': 7 }

COUNTRIES = { 'nl': ['en_GB', 'nl_NL'],
              'be': ['en_GB', 'nl_BE', 'fr_BE'],
              'de': ['en_GB', 'de_DE']}


def connect_to_spreadsheet_service():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet


def read_from_gdrive(sheet_service, filename):
    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '14fAvcZ6Ze9kJHm9p9omylYz9anrv9ZNjCepeAxK3LJo'
    SAMPLE_RANGE_NAME = 'sheet1!A2:I39'
    result = sheet_service.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=SAMPLE_RANGE_NAME, 
                                        majorDimension='COLUMNS').execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        generate_insert_queries(values)
        generate_delete_queries(values)

def generate_delete_queries(values):
    labels = values[0]
    with open(os.path.join('.', 'labels.delete.sql'), 'w') as delete_queries_file:
        for index in range(len(labels)):
            label = labels[index]
            query = 'delete from message where key=\'%s\'\n' % (label)

            delete_queries_file.write(query)

def generate_insert_queries(values):
    for country in COUNTRIES:
        generate_insert_queries_for_country(values, country)

def generate_insert_queries_for_country(values, country):
    print('Processing country %s' % country)
    with open(os.path.join('.', 'labels.%s.sql' % (country)), 'w') as country_queries_file:
        for locale in COUNTRIES[country]:
            generate_insert_queries_for_locale(values, country, locale, country_queries_file)
            country_queries_file.write('\n\n')

def generate_insert_queries_for_locale(values, country, locale, out_file):
    print('\tProcessing locale %s' % locale)
    labels = values[0]
    for index in range(len(labels)):
        label = labels[index]
        if len(label):
            text_in_locale = values[LANGUAGES[locale]][index]

            if text_in_locale == 'not needed':
                print('\t\tSkipping %s, looks like translation is not needed' % label)
            elif text_in_locale.strip() == '':
                print('\t\tWarning: No translation found for %s' % label)
            else:
                query = 'insert into message (key, locale, text, description, mutator) values (\'%s\', \'%s\', \'%s\', \'labels release3\', \'labels release3\');' % (label, locale, text_in_locale)
                out_file.write('%s\n' % (query))


if __name__ == "__main__":
    sheet_service = connect_to_spreadsheet_service()
    read_from_gdrive(sheet_service, 'en_BG')