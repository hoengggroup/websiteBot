# this is a blueprint for the main network commands we have to use

import urllib3
import html2text



http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=4.0, read=2.0))
try:
    r = http.request('GET', 'http://example.com')
    print(html2text.html2text(r.data.decode('utf-8')))
except urllib3.exceptions.ConnectionError as e:
    print("Time out:")
    print(e.reason)
except urllib3.exceptions.MaxRetryError as e:
    print("Max retry:")
    print(e.reason)

except Exception as e:
    print("unkown error:")
    print(e.__class__.__name__)
    print(e.reason)