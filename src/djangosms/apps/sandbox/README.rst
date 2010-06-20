Sandbox
-------

Name: ``"djangosms.apps.sandbox"``

Deployments that involve user training often require two separation
systems such that training sessions do not interfere with real-world
usage.

The ``"djangosms.apps.sandbox"`` application allows you to forward
messages from the default *sandbox* system to a *production* system::

  from djangosms.core.patterns import keyword

  ROUTES = (
      # enable/disable
      (keyword('sandbox'), 'djangosms.apps.sandbox.forms.Sandbox'),

      # match text without capturing
      (r'(?=(?P<text>.*))', 'djangosms.apps.sandbox.forms.Forward'),
  )

The production system must have an :class:`HTTP
<djangosms.core.transports.HTTP>` transport configured to serve on the
URL defined in the ``SANDBOX_FORWARD_URL`` setting, e.g.::

  SANDBOX_FORWARD_URL = "http://nohost"

Forms
~~~~~

.. automodule:: djangosms.apps.sandbox.forms
   :members: Forward, Sandbox

Models
~~~~~~

.. automodule:: djangosms.apps.sandbox.models
   :members: Policy
