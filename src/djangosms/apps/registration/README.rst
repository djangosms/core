Registration
------------

Name: ``"djangosms.apps.registration"``

Allows users to register themselves by providing their name::

  from djangosms.core.patterns import keyword

  ROUTES = (
      (keyword('reg', 'register'), 'djangosms.apps.registration.forms.Register'),
  )

Forms
~~~~~

.. automodule:: djangosms.apps.registration.forms
   :members: Register
