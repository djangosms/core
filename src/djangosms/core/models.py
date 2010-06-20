from django.db import models

class User(models.Model):
    """An authenticated user.

    The device used to send and receive messages typically provide a
    means of authentication. Since users may use different devices, we
    record a set of :class:`Connection` objects that each authenticate
    a user.
    """

    connections = ()

    @classmethod
    def from_uri(cls, uri, **kwargs):
        user = cls(**kwargs)
        user.save()
        connection, created = Connection.objects.get_or_create(uri=uri)
        user.connections.add(connection)
        return user

class Connection(models.Model):
    """Mapping between device and user.

    The ``uri`` attribute identifies the device in terms of the
    transport used and the unique identifier within that transport::

      <transport>://<ident>

    Examples::

      gsm://256703945965
      http+sms://256703945965
      twitter://bob
      email://bob@host.com

    The transport token identifies a transport; this is configured in
    the Django settings module under the ``TRANSPORTS`` key.
    """

    uri = models.CharField(max_length=30, primary_key=True)
    user = models.ForeignKey(User, related_name="connections", null=True)

    def __unicode__(self):
        return self.ident

    @property
    def transport(self):
        """Return transport name."""

        return self.uri.split('://', 1)[0]

    @property
    def ident(self):
        """Return ident string."""

        return self.uri.split('://', 1)[1]

class CustomForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        self.column = kwargs.pop('column')
        kwargs.setdefault('db_column', self.column)
        super(CustomForeignKey, self).__init__(*args, **kwargs)

    def get_attname(self):
        return self.column

class Message(models.Model):
    """SMS message between a user and the system."""

    uri = None
    text = models.CharField(max_length=160*3)
    time = models.DateTimeField(null=True)
    connection = CustomForeignKey(
        Connection, column="uri", related_name="messages", null=True)

    class Meta:
        ordering = ['-time']

    def __unicode__(self):
        return self.text

    @classmethod
    def from_uri(cls, uri, **kwargs):
        message = cls(**kwargs)
        connection, created = Connection.objects.get_or_create(uri=uri)
        message.connection = connection
        message.save()
        return message

    @property
    def user(self):
        """Return :class:`User` object, or ``None`` if not available."""

        return self.connection.user

class Incoming(Message):
    """An incoming message."""

    parts = ()

class Outgoing(Message):
    """An outgoing message."""

    in_response_to = models.ForeignKey("Request", related_name="responses", null=True)
    delivery_id = models.IntegerField(null=True)
    delivery = models.DateTimeField(null=True)

    @property
    def delivered(self):
        """Return ``True`` if the message was confirmed delivered."""

        return self.delivery is not None

    @property
    def sent(self):
        """Return ``True`` if the message was sent."""

        return self.time is not None

    def is_reply(self):
        """Return ``True`` if this outgoing message was a reply (as
        opposed to an unsolicited response).
        """

        if self.in_response_to is not None:
            return self.uri == self.in_response_to.message.uri
        return False

class Route(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)

    def __unicode__(self):
        return self.name

class Request(models.Model):
    text = models.CharField(max_length=160*3)
    message = models.ForeignKey(Incoming, related_name="requests", null=True)
    route = models.ForeignKey(Route, related_name="requests", null=True)
    erroneous = models.NullBooleanField(default=False)

    def reply(self, text):
        """Reply to message."""

        self.respond(self.message.connection, text)

    def respond(self, connection, text):
        """Respond to this form.

        This method puts an outgoing message into the delivery queue.
        """

        assert self.id is not None

        if connection is None:
            uri = self.message.uri
        else:
            uri = connection.uri

        assert uri is not None

        message = Outgoing(text=text, uri=uri, in_response_to=self)
        message.save()
