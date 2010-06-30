Registration
------------

Name: ``"djangosms.apps.registration"``

Allows users to register themselves by providing their name; it
includes a facility to require registration::

  from djangosms.core.patterns import keyword

  ROUTES = (
      # user registration
      (keyword('register|reg'), 'djangosms.apps.registration.forms.Register'),

      # from this route and down, users must be registered
      (r'^', 'djangosms.apps.registration.forms.MustRegister'),
  )

Forms
~~~~~

.. automodule:: djangosms.apps.registration.forms
   :members: Register, MustRegister
