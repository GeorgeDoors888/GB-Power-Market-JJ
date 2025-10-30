#!/usr/bin/env python3#!/usr/bin/env python3

"""Download the 3 key DUoS files identified from Drive search.""""""Download the 3 key DUoS files identified from Drive search."""



import osimport os

import pickleimport pickle

from google.auth.transport.requests import Requestfrom google.auth.transport.requests import Request

from google.oauth2.credentials import Credentialsfrom google.oauth2.credentials import Credentials

from googleapiclient.discovery import buildfrom googleapiclient.discovery import build

from googleapiclient.http import MediaIoBaseDownloadfrom googleapiclient.http import MediaIoBaseDownload

import ioimport io



TOKEN_FILE = 'token.pickle'TOKEN_FILE = 'token.pickle'

SCOPES = ['https://www.googleapis.com/auth/drive.readonly',SCOPES = ['https://www.googleapis.com/auth/drive.readonly',

          'https://www.googleapis.com/auth/spreadsheets']          'https://www.googleapis.com/auth/spreadsheets'\]



# Files to download# Files to download

FILES_TO_DOWNLOAD = [FILES_TO_DOWNLOAD = [

    {    {

        'id': '1mFgGUUC86HTUAgWn7kGoi6Cd3ampdWEZsLQ3YS20TrY',        'id': '1mFgGUUC86HTUAgWn7kGoi6Cd3ampdWEZsLQ3YS20TrY',

        'name': 'test_DUOS',        'name': 'test_DUOS',

        'type': 'spreadsheet',        'type': 'spreadsheet',

        'export_format': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',        'export_format': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

        'local_name': 'test_DUOS.xlsx'        'local_name': 'test_DUOS.xlsx'

    },    },

    {    {

        'id': '1VqbuIM25gk22jQgUOavggU2phYVArKd5',        'id': '1VqbuIM25gk22jQgUOavggU2phYVArKd5',

        'name': 'Updated_DUoS_Band_Rates___Times.csv',        'name': 'Updated_DUoS_Band_Rates___Times.csv',

        'type': 'csv',        'type': 'csv',

        'local_name': 'Updated_DUoS_Band_Rates___Times.csv'        'local_name': 'Updated_DUoS_Band_Rates___Times.csv'

    },    },

    {    {

        'id': '14Rce26sllDpGvFLKCMj_6E0jairS6XLI',        'id': '14Rce26sllDpGvFLKCMj_6E0jairS6XLI',

        'name': 'DUoS_Analysis_SSP_Integrated',        'name': 'DUoS_Analysis_SSP_Integrated',

        'type': 'spreadsheet',        'type': 'spreadsheet',

        'export_format': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',        'export_format': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

        'local_name': 'DUoS_Analysis_SSP_Integrated.xlsx'        'local_name': 'DUoS_Analysis_SSP_Integrated.xlsx'

    }    }

]]



def get_drive_service():def get_drive_service():

    """Authenticate and return Drive service."""    """Authenticate and return Drive service."""

    creds = None    creds = None

        

    if os.path.exists(TOKEN_FILE):    if os.path.exists(TOKEN_FILE):

        with open(TOKEN_FILE, 'rb') as token:        with open(TOKEN_FILE, 'rb') as token:

            creds = pickle.load(token)            creds = pickle.load(token)

        

    if not creds or not creds.valid:    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())            creds.refresh(Request())

        else:        else:

            raise Exception("No valid credentials.")            raise Exception("No valid credentials.")

        

    return build('drive', 'v3', credentials=creds)    return build('drive', 'v3', credentials=creds)



def download_file(service, file_info):def download_file(service, file_info):

    """Download a file from Google Drive."""    """Download a file from Google Drive."""

    file_id = file_info['id']    file_id = file_info['id']

    local_name = file_info['local_name']    local_name = file_info['local_name']

        

    print(f"\n📥 Downloading: {file_info['name']}")    print(f"\n📥 Downloading: {file_info['name']}")

    print(f"   → {local_name}")    print(f"   → {local_name}")

        

    try:    try:

        if file_info['type'] == 'spreadsheet':        if file_info['type'] == 'spreadsheet':

            # Export spreadsheet            # Export spreadsheet

            request = service.files().export_media(            request = service.files().export_media(

                fileId=file_id,                fileId=file_id,

                mimeType=file_info['export_format']                mimeType=file_info['export_format']

            )            )

        else:        else:

            # Download regular file            # Download regular file

            request = service.files().get_media(fileId=file_id)            request = service.files().get_media(fileId=file_id)

                

        fh = io.BytesIO()        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request)        downloader = MediaIoBaseDownload(fh, request)

                

        done = False        done = False

        while not done:        while not done:

            status, done = downloader.next_chunk()            status, done = downloader.next_chunk()

            if status:            if status:

                progress = int(status.progress() * 100)                progress = int(status.progress() * 100)

                print(f"   Progress: {progress}%", end='\r')                print(f"   Progress: {progress}%", end='\r')

                

        print(f"   Progress: 100% ✓")        print(f"   Progress: 100% ✓")

                

        # Write to file        # Write to file

        with open(local_name, 'wb') as f:        with open(local_name, 'wb') as f:

            f.write(fh.getvalue())            f.write(fh.getvalue())

                

        size_mb = len(fh.getvalue()) / (1024 * 1024)        size_mb = len(fh.getvalue()) / (1024 * 1024)

        print(f"   Size: {size_mb:.2f} MB")        print(f"   Size: {size_mb:.2f} MB")

        return True        return True

                

    except Exception as e:    except Exception as e:

        print(f"   ❌ Error: {e}")        print(f"   ❌ Error: {e}")

        return False        return False



def main():def main():

    print("=" * 70)    print("=" * 70)

    print("DOWNLOADING KEY DUoS FILES FROM GOOGLE DRIVE")    print("DOWNLOADING KEY DUoS FILES FROM GOOGLE DRIVE")

    print("=" * 70)    print("=" * 70)

        

    service = get_drive_service()    service = get_drive_service()

        

    success_count = 0    success_count = 0

    for file_info in FILES_TO_DOWNLOAD:    for file_info in FILES_TO_DOWNLOAD:

        if download_file(service, file_info):        if download_file(service, file_info):

            success_count += 1            success_count += 1

        

    print()    print()

    print("=" * 70)    print("=" * 70)

    print(f"✅ Downloaded {success_count}/{len(FILES_TO_DOWNLOAD)} files")    print(f"✅ Downloaded {success_count}/{len(FILES_TO_DOWNLOAD)} files")

    print("=" * 70)    print("=" * 70)



if __name__ == '__main__':if __name__ == '__main__':

    main()    main()

