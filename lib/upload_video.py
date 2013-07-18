#!/usr/bin/env python

import httplib
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from optparse import OptionParser


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# CLIENT_SECRETS_FILE, name of a file containing the OAuth 2.0 information for
# this application, including client_id and client_secret. You can acquire an
# ID/secret pair from the API Access tab on the Google APIs Console
#   http://code.google.com/apis/console#access
# For more information about using OAuth2 to access Google APIs, please visit:
#   https://developers.google.com/accounts/docs/OAuth2
# For more information about the client_secrets.json file format, please visit:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# Please ensure that you have enabled the YouTube Data API for your project.
CLIENT_SECRETS_FILE = "client_secrets.json"

# A limited OAuth 2 access scope that allows for uploading files, but not other
# types of account access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Helpful message to display if the CLIENT_SECRETS_FILE is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console
https://code.google.com/apis/console#access

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service():
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(flow, storage)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


def initialize_upload(options):
  youtube = get_authenticated_service()

  tags = None
  if options.keywords:
    tags = options.keywords.split(",")

  insert_request = youtube.videos().insert(
    part="snippet,status",
    body=dict(
      snippet=dict(
        title=options.title,
        description=options.description,
        tags=tags,
        categoryId=options.category
      ),
      status=dict(
        privacyStatus=options.privacyStatus
      )
    ),
    # chunksize=-1 means that the entire file will be uploaded in a single
    # HTTP request. (If the upload fails, it will still be retried where it
    # left off.) This is usually a best practice, but if you're using Python
    # older than 2.6 or if you're running on App Engine, you should set the
    # chunksize to something like 1024 * 1024 (1 megabyte).
    media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
  )

  resumable_upload(insert_request)


def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print "Uploading file..."
      status, response = insert_request.next_chunk()
      if 'id' in response:
        print "'%s' (video id: %s) was successfully uploaded." % (
          options.title, response['id'])
      else:
        exit("The upload failed with an unexpected response: %s" % response)
    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print error
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print "Sleeping %f seconds and then retrying..." % sleep_seconds
      time.sleep(sleep_seconds)


if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option("--file", dest="file", help="Video file to upload")
  parser.add_option("--title", dest="title", help="Video title",
    default="Test Title")
  parser.add_option("--description", dest="description",
    help="Video description",
    default="Test Description")
  parser.add_option("--category", dest="category",
    help="Numeric video category. " +
      "See https://developers.google.com/youtube/v3/docs/videoCategories/list",
    default="22")
  parser.add_option("--keywords", dest="keywords",
    help="Video keywords, comma separated", default="")
  parser.add_option("--privacyStatus", dest="privacyStatus",
    help="Video privacy status: public, private or unlisted",
    default="public")
  (options, args) = parser.parse_args()

  if options.file is None or not os.path.exists(options.file):
    exit("Please specify a valid file using the --file= parameter.")
  else:
    initialize_upload(options)
