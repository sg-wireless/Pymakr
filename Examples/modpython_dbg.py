from mod_python import apache

apache.initDebugger('/Path/To/modpython_dbg.py')

def handler(req):
    req.content_type = "text/plain"
    req.send_http_header()
    req.write("Hello World!\n")

    return apache.OK
