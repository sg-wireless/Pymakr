from __future__ import print_function

from os import path
import json
import urllib2

import mimetypes
import random
import string

import uuid
import hashlib

baseURL = "http://nodejs-pycom.rhcloud.com"


_BOUNDARY_CHARS = string.digits + string.ascii_letters

def generateID():
    val = uuid.getnode()
    for i in xrange(0, 128):
        val = hashlib.sha1(val).hexdigest()

def encode_multipart(fields, files, files_field_name = "upload", boundary=None):
    def escape_quote(s):
        return s.replace('"', '\\"')

    if boundary is None:
        boundary = ''.join(random.choice(_BOUNDARY_CHARS) for i in range(30))
    lines = []

    for name, value in fields.items():
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"'.format(escape_quote(name)),
            '',
            str(value),
        ))

    for item in files:
        filename = item['filename']
        if 'mimetype' in value:
            mimetype = item['mimetype']
        else:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(
                    escape_quote(files_field_name), escape_quote(filename)),
            'Content-Type: {0}'.format(mimetype),
            '',
            item['content'],
        ))

    lines.extend((
        '--{0}--'.format(boundary),
        '',
    ))
    body = '\r\n'.join(lines)

    headers = {
        'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary),
        'Content-Length': str(len(body)),
    }

    return (body, headers)

def sendReport(formData, files = [], uploadFieldName = "upload"):
    '''
    formData must include:
        type, product, version, email, title, description and extra info
    '''
    def loadFile(name):
        filename = path.basename(name)
        with open(name, 'r') as content_file:
            content = content_file.read()
        return {"filename": filename, "content": content}

    url = baseURL + "/reports/report"

    loadedFiles = map(loadFile, files)
    body, headers =  encode_multipart(formData, loadedFiles)

    req = urllib2.Request(url, body, headers)
    f = urllib2.urlopen(req)
    response = f.read()
    f.close()

    return True if json.loads(response)['result'] == "ok" else False

