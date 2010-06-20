Common
------

Name: ``"djangosms.apps.common"``

This application includes common utility forms::

  from djangosms.core.patterns import keyword

  ROUTES = (
      # from this route and down, users must be registered
      (r'^', 'djangosms.apps.common.forms.MustRegister'),

      # unknown keyword
      (keyword(r'\w+'), 'djangosms.apps.common.forms.NotUnderstood'),

      # free-form text input
      (r'^(?P<text>.*)$', 'djangosms.apps.common.forms.Input'),
  )

Forms
~~~~~

.. automodule:: djangosms.apps.common.forms
   :members: MustRegister, NotUnderstood, Input

Models
~~~~~~

.. automodule:: djangosms.apps.common.models
   :members: Query
