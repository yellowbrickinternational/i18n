from __future__ import print_function
import sys
import pickle
import os.path
import html
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

LANGUAGES = {'en_GB': 3,
             'nl_NL': 4,
             'de_DE': 5,
             'nl_BE': 6,
             'fr_BE': 7}

COUNTRIES = {'nl': ['en_GB', 'nl_NL'],
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


def read_from_gdrive(sheet_service, sheet_id):
    # The ID and range of a sample spreadsheet.
    SAMPLE_RANGE_NAME = 'sheet1'
    result = sheet_service.values().get(spreadsheetId=sheet_id,
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
    with open(os.path.join('.', 'labels.%s.sql' % (country)), 'w', encoding='utf-8') as country_queries_file:
        for locale in COUNTRIES[country]:
            generate_insert_queries_for_locale(values, country, locale, country_queries_file)
            country_queries_file.write('\n\n')


def label_match_country(country, label_apply_for):
    return (label_apply_for == country) or (label_apply_for == 'all')


def generate_insert_queries_for_locale(values, country, locale, out_file):
    try:
        print('\tProcessing locale %s' % locale)
        labels = values[0]
        for index in range(len(labels)):
            label = labels[index]
            label_apply_for = values[2][index]
            match = label_match_country(country, label_apply_for)

            if len(label) and match:
                texts_for_locale = values[LANGUAGES[locale]]
                text_in_locale = values[LANGUAGES[locale]][index] if index < len(texts_for_locale) else ''

                if text_in_locale == 'not needed':
                    print('\t\tSkipping %s, looks like translation is not needed' % label)
                elif text_in_locale.strip() == '':
                    print('\t\tWarning: No translation found for %s' % label)
                    text_in_locale = ' '
                    query = 'insert_or_update_message(\'%s\', \'%s\', \'%s\');' % (label, locale, text_in_locale)
                    out_file.write('%s\n' % (query))
                else:
                    query = 'insert_or_update_message(\'%s\', \'%s\', \'%s\');' % (label, locale, text_in_locale)
                    out_file.write('%s\n' % (query))
    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    sheet_id = sys.argv[1]
    sheet_service = connect_to_spreadsheet_service()
    read_from_gdrive(sheet_service, sheet_id)
