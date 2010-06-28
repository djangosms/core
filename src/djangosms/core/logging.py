from StringIO import StringIO

def format_incoming(message):
    requests = message.requests.all()
    out = StringIO()
    for i, request in enumerate(requests):
        time = message.time and message.time.isoformat() or '-'
        print >> out, "%d/%d %s" % (i+1, len(requests), time)
        print >> out, "--> %s" % (request.text.encode('utf-8') or "(empty)")
        print >> out, "----" + "-"*len(request.text)

        responses = request.responses.all()
        for j, response in enumerate(responses):
            print >> out, "    %d/%d %s" % (j+1, len(responses), response.uri)
            print >> out, "    <-- %s" % (response.text.encode('utf-8') or "(empty)")

    return out.getvalue()
