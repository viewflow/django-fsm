django-fsm
==========

Django-friendly finite state machine support.

``django-fsm`` adds simple, declarative state management for Django models
and plain Python objects.

Define states and transitions explicitly instead of spreading state
assignments across views and models. Transitions check source states and
business conditions before running a method. Permissions are checked
explicitly with ``has_transition_perm()`` or by UI/REST integrations.


Installation
------------

.. code-block:: console

    python -m pip install django-fsm

For plain Python classes, no other dependencies are required. To use with Django models, make sure Django is installed or specify the extra:

.. code-block:: console

    python -m pip install 'django-fsm[django]'



Quick start
-----------

Add an ``FSMField`` to your Django model and mark transition methods with
the ``@transition`` decorator:

.. code-block:: python

    from django.db import models
    from django_fsm import FSMField, transition, can_proceed

    class BlogPost(models.Model):
        state = FSMField(default='draft', protected=True)

        @transition(field=state, source='draft', target='published')
        def publish(self):
            """Side-effects when publishing a post (e.g. notify users, update cache)."""

The ``protected=True`` option prevents direct state modification:

.. code-block:: python

    post = BlogPost()
    post.state = 'published'  # Raises AttributeError

To invoke a transition and persist the change:

.. code-block:: python

    post = BlogPost.objects.get(pk=post_id)

    if can_proceed(post.publish):
        post.publish()
        post.save()


Conditions and Permissions
--------------------------

Conditions
~~~~~~~~~~

Use the ``conditions`` argument to enforce rules before a transition is
allowed. Conditions are callables that take the model instance and return
a boolean:

.. code-block:: python

    def can_publish(instance):
        return bool(instance.title and instance.body)

    class BlogPost(models.Model):
        state = FSMField(default='draft')

        @transition(field=state, source='draft', target='published', conditions=[can_publish])
        def publish(self):
            pass

Permissions
~~~~~~~~~~~

You can guard transitions with permissions and verify them using
``has_transition_perm``:

.. code-block:: python

    from django_fsm import transition, has_transition_perm

    class BlogPost(models.Model):
        state = FSMField(default='draft')

        @transition(field=state, source='draft', target='published', permission='blog.can_publish')
        def publish(self):
            pass

A direct call such as ``post.publish()`` does not check user permissions.
Use ``has_transition_perm()`` before calling it, as below, or use an
integration that performs the check.

In your view:

.. code-block:: python

    if not has_transition_perm(post.publish, request.user):
        raise PermissionDenied

    post.publish()
    post.save()


Dynamic Targets
---------------

When the target state depends on runtime logic or method results:

- ``RETURN_VALUE(*allowed_states)`` selects the target from the method's return value:

.. code-block:: python

    from django_fsm import FSMField, RETURN_VALUE, transition

    class Task(models.Model):
        status = FSMField(default='pending')

        @transition(field=status, source='pending', target=RETURN_VALUE('approved', 'rejected'))
        def review(self, score):
            return 'approved' if score >= 80 else 'rejected'

- ``GET_STATE(func, states=[...])`` calculates the target state before the
  transition runs, based on the instance and method arguments.


Plain Python State Machines
---------------------------

``State`` also works with plain Python classes without Django database models
or settings:

.. code-block:: python

    from django_fsm import State

    class Review:
        state = State(states=None, default='draft')

        @state.transition(source='draft', target='published')
        def publish(self):
            pass

    review = Review()
    review.publish()
    assert review.state == 'published'


Upgrading from django-fsm 3.x
-----------------------------

Version 5.0 uses the Viewflow transition engine. Ordinary targets are now
applied **before the method body runs**; django-fsm 3.x applied them after
the method returned. Code that reads ``self.state`` inside a transition
therefore observes the target state in 5.0.

``GET_STATE`` also computes and applies its target before the method runs.
``RETURN_VALUE`` applies the target after the method returns.

If the method raises, the adapter restores the source state in memory, or
applies ``on_error`` when specified. This does not undo database writes or
external side effects performed by the method. Use ``transaction.atomic()``
around the transition and ``save()`` when those database writes must roll
back together.


Viewflow Pro Integrations
-------------------------

``django-fsm`` integrates out of the box with Viewflow Pro and Django REST Framework:

- ``django_fsm.admin.FlowAdminMixin``: Viewflow Admin integration for state workflows.
- ``django_fsm.viewset.FlowViewsMixin``: Viewflow Viewset workflows.
- ``django_fsm.rest.FlowRESTMixin``: Optional Django REST Framework viewset integration (requires ``django-fsm[rest]``).


Documentation & Contributing
----------------------------

- Full documentation: https://docs.viewflow.io/fsm/index.html
- Contributing & development instructions: see `CONTRIBUTING.rst <https://github.com/viewflow/django-fsm/blob/master/CONTRIBUTING.rst>`_


License
-------

Django FSM is licensed under AGPL-3.0-or-later with the viewflow-library-exception.
See ``LICENSE`` and ``LICENSE_EXCEPTION`` for details.
