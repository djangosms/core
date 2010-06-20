import re
import sys
import logging

try:
    import sms
except ImportError: # pragma: NOCOVER
    sms = None

from datetime import datetime
from threading import Thread
from time import sleep
from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen
from time import time as get_time
from traceback import format_exc
from warnings import warn
from weakref import ref as weakref

from django.db.models import signals
from django.dispatch import Signal
from django.conf import settings

from .models import Incoming
from .models import Outgoing
from .models import Connection
from .router import route

pre_route = Signal()
post_route = Signal()
http_event = Signal(providing_args=["name", "request", "response"])
hangup = Signal()

def shrink(string): # pragma: NOCOVER
    return string.replace('\r', '').replace('\n', '').strip()

class Transport(object):
    """Transport.

    Shared by all transport implementations.

    :param name: Name

    :param options: Options; keys may be provided in any case. All options are set as attributes on the transport object.

    If an implementation needs to operate in a separate thread, this
    should be set up in the class constructor.
    """

    router = None

    def __init__(self, name, options={}, router=None):
        for key, value in options.items():
            setattr(self, key.lower(), value)

        self.name = name
        self.router = router or route

class Message(Transport):
    """Message transport.

    This is the base class for all message-based transports.

    When the transport receives an incoming message it should call the
    :meth:`incoming` method for processing.
    """

    def incoming(self, ident, text, time=None):
        """Route incoming text message.

        When the system runs in debug mode (with the ``DEBUG`` setting
        set to a true value), all exceptions are let through to the
        calling method. Otherwise a warning is logged with the full
        traceback while the exception is suppressed.
        """

        time = time or datetime.now()
        message = Incoming(text=text, time=time)

        # make sure we have a connection record for this sender
        message.uri = "%s://%s" % (self.name, ident)
        connection, created = Connection.objects.get_or_create(uri=message.uri)
        if created: connection.save()

        # save message
        message.save()

        pre_route.send(sender=message)
        try:
            self.router(message)
        except:
            if settings.DEBUG:
                raise
            else:
                cls, exc, tb = sys.exc_info()
                warn("%s ERROR [%s] - %s.\n\n%s" % (
                    time.isoformat(),
                    type(exc).__name__,
                    repr(message.text.encode('utf-8')),
                    format_exc(exc)))
        finally:
            post_route.send(sender=message)

        return message

class GSM(Message): # pragma: NOCOVER
    """GSM transport.

    :param name: Transport name

    :param options: ``DEVICE`` is the modem serial port (e.g. ``\"COM1\"``) or special device path (e.g. ``\"/dev/ttyUSB0\"``); ``LOG_LEVEL`` sets the logging level (default is ``\"WARN\"`` which is quiet unless there's an error); ``DCS`` is the data coding scheme (default is ``0`` for normal delivery, ``16`` sends flash messages); ``VALIDITY`` sets the message expiration (use ``167`` for one day); ``STORAGE`` sets the preferred message storage (use ``ME`` for internal, ``SM`` for SIM card or ``MT`` for either); set ``DELIVERY`` to a true value to request delivery reports (may incur an extra charge, use with caution).

    Example::

      TRANSPORTS = {
          'gsm': {
              'TRANSPORT': 'router.transports.GSM',
              'DEVICE': '/dev/ttyUSB0',
          }
      }

    """

    device = None
    dcs = 0
    delivery = None
    validity = ""
    log_level = "WARN"
    storage = ""
    timeout = 3

    _hangup = False

    def __init__(self, *args, **kwargs):
        super(GSM, self).__init__(*args, **kwargs)

        # verify availability of sms module
        if sms is None:
            raise ImportError('sms')

        formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                      "%(levelname)s - %(message)s")
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        level = getattr(logging, self.log_level.upper())
        logger = self.logger = logging.Logger(self.name.upper(), level=level)
        logger.addHandler(handler)

        try:
            self.modem = sms.Modem(self.device)
        except sms.ModemError, error:
            logger.error(error)
        else:
            self.logger.info("Connected to %s..." % self.device)
            if not self.setup():
                return

            # listen to hangup-signal
            hangup.connect(self.stop)

            # start thread
            thread = Thread(target=self.run)
            thread.start()

    def run(self):
        while not self._hangup:
            # wait for signal
            strength = self.check_signal_strength()
            if strength == -1:
                self.logger.warn("No signal; waiting 10 seconds.")
                for i in range(10):
                    sleep(1)
                    if self._hangup:
                        break
                continue
            elif strength is not None:
                self.logger.debug("Signal strength: %d." % strength)

            # incoming
            try:
                self.modem.wait(1)
                messages = self.modem.messages()
            except sms.ModemError, error:
                self.logger.warn(error)
                sleep(1)
                continue

            if len(messages) > 0:
                self.logger.debug("Received %d message(s)." % len(messages))

            for message in messages:
                ignored = ""
                if len(message.number) < 6:
                    ignored = " [IGNORED]"
                self.logger.debug("%s --> %s%s" % (
                    message.number, repr(
                        message.text.encode('utf-8')), ignored))
                if not ignored:
                    self.incoming(message.number, message.text, message.date)

            # outgoing
            messages = Outgoing.objects.filter(
                time=None, connection__uri__startswith="%s://" % self.name)
            if len(messages) > 0:
                self.logger.debug("Sending %d message(s)..." % len(messages))

            for message in messages.all():
                try:
                    self.logger.debug("%s <-- %s" % (
                        message.connection.ident, repr(message.text.encode('utf-8'))))

                    # prepare send
                    self.modem.conn.write("AT+CMGS=\"%s\"\r" % message.connection.ident)
                    result = self.modem.conn.readall()

                    if '>' not in result:
                        self.logger.debug("Sending message failed "
                                          "before text was sent "
                                          "(%s)." % shrink(result))
                        continue

                    # send text
                    self.modem.conn.write(message.text + "\x1A")
                    self.modem.conn.flush()

                    # wait for message id
                    timeout = get_time() + self.timeout
                    while 'ERROR' not in result and get_time() < timeout:
                        result = self.modem.conn.readall()
                        m = re.search(r'\+CMGS: (\d+)', result)
                        if m is not None:
                            message.delivery_id = int(m.group(1))
                            break
                    else:
                        self.logger.debug("Did not receive message id.")
                        raise sms.ModemError(shrink(result))

                except sms.ModemError, error:
                    self.logger.warn(error)
                    sleep(1)
                else:
                    self.logger.debug("Message sent with delivery id: %s." % \
                                      message.delivery_id)
                    message.time = datetime.now()
                    message.save()

            # delete all read (and stored sent) messages
            self.modem.conn.write("AT+CMGD=0,2\r\n")
            self.modem.conn.flush()
            result = self.modem.conn.readall()
            if 'OK' not in result:
                self.logger.critical(
                    "Error deleting messages (%s)." % shrink(result))
                self.stop()

        try:
            del self.modem
        except Exception, exc:
            self.logger.warn("Error disconnecting (%s)." % exc)
        else:
            self.logger.info("Disconnected.")

    def check_signal_strength(self):
        """Returns an integer between 1 and 99, representing the
        current signal strength of the GSM network, ``-1`` if we don't
        know, or ``None`` if the modem can't report it.
        """

        data = self.query("AT+CSQ")
        md = re.match(r"^\+CSQ: (\d+),", data)

        if md is not None:
            csq = int(md.group(1))
            return csq if csq < 99 else -1

    def ping(self):
        result = self.query("AT")
        if 'OK' not in result:
            self.logger.warn("Modem does not respond (%s)." % shrink(result))
            return False
        return True

    def query(self, command):
        self.modem.conn.write("%s\r" % command)
        self.modem.conn.flush()
        return self.modem.conn.readall()

    def setup(self):
        while not self.ping():
            sleep(1)
            if self._hangup:
                return

        # query manufacturer for diagnostics
        result = self.query("AT+GMI")
        manufacturer = shrink(result.split('AT+GMI')[-1].split('OK')[0])
        self.logger.info("%s identified." % manufacturer.capitalize())

        # set preferred message storage
        if self.storage:
            result = self.query("AT+CPMS=\"%s\"" % self.storage)
            if 'OK' not in result:
                self.logger.warn("Could not set preferred "
                                 "storage to %s." % self.storage)

        # query mode availability
        result = self.query("AT+CMGF=?")
        if '1' not in result:
            self.logger.critical("Modem does not support text mode (%s)." % \
                                 shrink(result))
            return

        # set text mode
        result = self.query("AT+CMGF=1")
        if 'OK' not in result:
            self.logger.critical("Unable to set message mode (%s)." % \
                                 shrink(result))
            return

        # verify that we can send messages
        result = self.query("AT+CMGS=?")
        if 'OK' not in result:
            self.logger.critical("Modem reported inability to send "
                                 "messages (%s)." % shrink(result))
            return

        options = 1
        if self.validity:
            options |= 16
        if self.delivery:
            options |= 32

        result = self.query("AT+CSMP=%d,%s,0,%s" % (
            options, self.validity, self.dcs))
        if 'OK' not in result:
            self.logger.warn("Unable to configure message delivery (%s)." % \
                             shrink(result))
        else:
            m = re.match('AT\+CSMP=((\d*(?:,))+)', result)
            if m is not None:
                self.logger.debug("Message delivery options: %s." % m.group(1))

        return True

    def stop(self, *args, **kwargs):
        """Stop transport."""

        self.logger.info("Stopping...")
        self._hangup = True

    def ussd(self, request):
        """Place USSD request."""

        self.logger.info("Requesting %s..." % request)
        self.modem.conn.write("AT+CUSD=1,\"%s\",15\r" % request)
        self.modem.conn.flush()
        result = self.modem.conn.readall()
        self.logger.info(shrink(result))

class HTTP(Message):
    """Generic HTTP transport.

    This transport is modelled after the HTTP interface to the `Kannel
    <http://www.kannel.org>` gateway.

    It uses the CGI parameter names ``\"from\"``, ``\"to\"``,
    ``\"text\"`` and ``\"status\"`` (see :data:`handle
    <djangosms.core.transports.HTTP.handle>``).

    :param name: Transport name

    :param options: Dictionary; define ``'SEND_URL'`` for the (outgoing) service and ``'DLR_URL'`` to set the (incoming) delivery confirmation reply

    Example 1: Kannel

        In this example the server is listening to port ``13013`` (the
        default) and configured with the credentials ``\"kannel\"`` /
        ``\"kannel\"``.

        Delivery confirmation is requested.

        ::

          TRANSPORTS = {
              'http': {
                  'TRANSPORT': 'router.transports.HTTP',
                  'SEND_URL': 'http://localhost:13013/cgi-bin/sendsms?' \\
                              'username=kannel&password=kannel',
                  'DLR_URL': 'http://localhost:8080/incoming',
              }
          }

    Example 2: Forwarding

        We can also use the ``HTTP`` transport to accept messages from
        another DjangoSMS deployment:

        ::

          TRANSPORTS = {
              'http': {
                  'TRANSPORT': 'router.transports.HTTP',
              }
          }

    """

    send_url = None
    dlr_url = None
    timeout = 30.0

    def __init__(self, *args, **kwargs):
        super(HTTP, self).__init__(*args, **kwargs)

        reference = weakref(self)

        # set up event handler for incoming messages
        def on_incoming(sender=None, name=None, request=None, response=None, **kwargs):
            transport = reference()
            if transport is not None and name == transport.name:
                body, status_code = transport.handle(request)
                response.write(body)
                response.status_code = status_code

        http_event.connect(on_incoming, weak=False)
        del on_incoming

        # set up event handler for outgoing messages
        def on_outgoing(sender=None, instance=None, created=False, **kwargs):
            transport = reference()
            if transport is not None:
                if created is True and instance.connection.transport == transport.name:
                    transport.send(instance)

        signals.post_save.connect(on_outgoing, sender=Outgoing, weak=False)
        del on_outgoing

    def fetch(self, request, **kwargs): # pragma: NOCOVER
        """Fetch HTTP request.

        Used internally by the HTTP transport.

        This method operates synchronously. Note that the method is a
        convenience for writing tests without setting up an HTTP
        server (replace with a mock implementation).
        """

        response = urlopen(request, **kwargs)
        return response.getcode() // 100 == 2

    def handle(self, request):
        """
        Accepts Django HTTP requests (method ``GET``) with CGI
        parameters defined as follows:

        Requests can be incoming messages or delivery confirmation
        receipts.

        Required:

        :param timestamp: Epoch integer timestamp (any)

        Incoming messages:

        :param sender: Mobile number
        :param text: Message body

        Delivery confirmation (DLR):

        :param status: Positive integer value means this is a delivery confirmation
        :param id: Message id
        """

        try:
            status = int(request.GET.get('status', 0))
            time = datetime.fromtimestamp(
                float(request.GET['timestamp']))

            if status:
                message_id = int(request.GET['id'])
            else:
                sender = request.GET['from']
                text = request.GET['text']
        except Exception, exc:
            return "There was an error (``%s``) processing the request: %s." % (
                type(exc).__name__, str(exc)), "406 Not Acceptable"

        # the statuses are used by kannel; 1: Delivered to phone, 2:
        # Non-Delivered to Phone, 4: Queued on SMSC, 8: Delivered to
        # SMSC, 16: Non-Delivered to SMSC; since we use the bitmask 3,
        # we can simply check for success or failure
        if status == 1:
            message = Outgoing.objects.get(pk=message_id)
            message.delivery = time
            message.save()
        else:
            self.incoming(sender, text, time)

        return "", "200 OK"

    def send(self, message):
        url = self.send_url
        if url is None: # PRAGMA: nocover
            raise ValueError("Must set ``SEND_URL`` parameter for "
                             "transport: %s." % self.name)

        if '?' not in url:
            url += "?"

        query = {
            'to': message.connection.ident,
            'text': message.text,
            }

        if self.dlr_url is not None:
            query.update({
                'dlr-url': '%s?status=%%d&id=%d&timestamp=%%T' % (
                    self.dlr_url, message.id),
                'dlr-mask': '3'
                })

        request = Request(
            url+'&'+urlencode(query)
            )

        if self.fetch(request, timeout=self.timeout):
            message.time = datetime.now()
            message.save()
