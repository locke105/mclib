
import cgi
import json
from wsgiref import simple_server

import falcon

from mclib import mc_info

class MCInfo(object):

    def on_get(self, req, resp):

        host = req.get_param('host', required=True)
        port = req.get_param_as_int('port', min=1024,
                                    max=65565)

        try:
            if port is not None:
                info = mc_info.get_info(host=host,
                                        port=port)
            else:
                info = mc_info.get_info(host=host)
        except Exception:
            raise Exception('Couldn\'t retrieve info.')

        if '.json' in req.uri:
            resp.body = self.get_json(info)
            return

        preferred = req.client_prefers(['application/json', 'text/html'])
        if 'html' in preferred:
            resp.content_type = 'text/html'
            resp.body = self.get_html(info)
        else:
            resp.body = self.get_json(info)

    def get_html(self, info):

        html = """<body>
<style>
table,th,td
{
border:1px solid black;
border-collapse:collapse
}
th,td
{
padding: 5px
}
</style>

<table>
"""

        for k,v in info.iteritems():
            items = {'key': cgi.escape(k)}
            if isinstance(v, basestring):
                items['val'] = cgi.escape(v)
            else:
                items['val'] = v
            html = html + '<tr><td>%(key)s</td><td>%(val)s</td></tr>' % items

        html = html + '</table></body>'

        return html

    def get_json(self, info):
        return json.dumps(info)

app = falcon.API()

mcinfo = MCInfo()

app.add_route('/mcinfo', mcinfo)
app.add_route('/mcinfo.json', mcinfo)

if __name__ == '__main__':
    httpd = simple_server.make_server('0.0.0.0', 3000, app)
    httpd.serve_forever()
