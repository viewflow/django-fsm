Django friendly finite state machine support
============================================

|Build Status| |Downloads| |Gitter|

django-fsm adds simple declarative states management for django models.

If you need parallel task execution, view and background task code reuse
over different flows - check my new project django-viewflow:

https://github.com/viewflow/viewflow


Instead of adding some state field to a django model, and managing its
values by hand, you could use FSMState field and mark model methods with
the ``transition`` decorator. Your method could contain the side-effects
of the state change.

Nice introduction is available here:
https://gist.github.com/Nagyman/9502133

You may also take a look at django-fsm-admin project containing a mixin
and template tags to integrate django-fsm state transitions into the
django admin.

https://github.com/gadventures/django-fsm-admin

Transition logging support could be achived with help of django-fsm-log
package

https://github.com/gizmag/django-fsm-log

FSM really helps to structure the code, especially when a new developer
comes to the project. FSM is most effective when you use it for some
sequential steps.


Installation
------------

.. code:: bash

    $ pip install django-fsm

Or, for the latest git version

.. code:: bash

    $ pip install -e git://github.com/kmmbvnr/django-fsm.git#egg=django-fsm

The library has full Python 3 support

Usage
-----

Add FSMState field to your model

.. code:: python

    from django_fsm import FSMField, transition

    class BlogPost(models.Model):
        state = FSMField(default='new')

Use the ``transition`` decorator to annotate model methods

.. code:: python

    @transition(field=state, source='new', target='published')
    def publish(self):
        """
        This function may contain side-effects,
        like updating caches, notifying users, etc.
        The return value will be discarded.
        """

``source`` parameter accepts a list of states, or an individual state.
You can use ``*`` for source, to allow switching to ``target`` from any
state. The ``field`` parameter accepts both a string attribute name or an
actual field instance.

If calling publish() succeeds without raising an exception, the state
field will be changed, but not written to the database.

.. code:: python

    from django_fsm import can_proceed

    def publish_view(request, post_id):
        post = get_object__or_404(BlogPost, pk=post_id)
        if not can_proceed(post.publish):
            raise PermissionDenied

        post.publish()
        post.save()
        return redirect('/')

If some conditions are required to be met before changing the state, use
the ``conditions`` argument to ``transition``. ``conditions`` must be a
list of functions taking one argument, the model instance. The function
must return either ``True`` or ``False`` or a value that evaluates to
``True`` or ``False``. If all functions return ``True``, all conditions
are considered to be met and the transition is allowed to happen. If one
of the functions returns ``False``, the transition will not happen.
These functions should not have any side effects.

You can use ordinary functions

.. code:: python

    def can_publish(instance):
        # No publishing after 17 hours
        if datetime.datetime.now().hour > 17:
            return False
        return True

Or model methods

.. code:: python

    def can_destroy(self):
        return self.is_under_investigation()

Use the conditions like this:

.. code:: python

    @transition(field=state, source='new', target='published', conditions=[can_publish])
        def publish(self):
        """
        Side effects galore
        """

    @transition(field=state, source='*', target='destroyed', conditions=[can_destroy])
        def destroy(self):
        """
        Side effects galore
        """

You could instantiate a field with protected=True option, that prevents
direct state field modification.

.. code:: python

    class BlogPost(models.Model):
        state = FSMField(default='new', protected=True)

    model = BlogPost()
    model.state = 'invalid' # Raises AttributeError

Note that calling
```refresh_from_db`` <https://docs.djangoproject.com/en/1.8/ref/models/instances/#django.db.models.Model.refresh_from_db>`__
on a model instance with a protected FSMField will cause an exception.

`target`
~~~~~~~~

`target` state parameter could points to the specific state or `django_fsm.State` implementation

.. code:: python
          
    from django_fsm import FSMField, transition, RETURN_VALUE, GET_STATE
    @transition(field=state,
                source='*',
                target=RETURN_VALUE('for_moderators', 'published'))
    def publish(self, is_public=False):
        return 'need_moderation' if is_public else 'published'

    @transition(
        field=state,
        source='for_moderators',
        target=GET_STATE(
            lambda self, allowed: 'published' if allowed else 'rejected',
            states=['published', 'rejected']))
    def moderate(self, allowed):
        self.allowed=allowed


``custom`` properties
~~~~~~~~~~~~~~~~~~~~~

Custom properties can be added by providing a dictionary to the
``custom`` keyword on the ``transition`` decorator.

.. code:: python

    @transition(field=state,
                source='*',
                target='onhold',
                custom=dict(verbose='Hold for legal reasons'))
    def legal_hold(self):
        """
        Side effects galore
        """

``on_error`` state
~~~~~~~~~~~~~~~~~~

In case of transition method would raise exception, you can provide
specific target state

.. code:: python

    @transition(field=state, source='new', target='published', on_error='failed')
    def publish(self):
       """
       Some exception could happen here
       """

``state_choices``
~~~~~~~~~~~~~~~~~

Instead of passing two elements list ``choices`` you could use three
elements ``state_choices``, the last element states for string reference
to model proxy class.

Base class instance would be dynamically changed to corresponding Proxy
class instance, depending on the state. Even for queryset results, you
will get Proxy class instances, even if QuerySet executed on base class.

Check the `test
case <https://github.com/kmmbvnr/django-fsm/blob/master/tests/testapp/tests/test_state_transitions.py>`__
for example usage. Or read about `implementation
internals <http://schinckel.net/2013/06/13/django-proxy-model-state-machine/>`__

Permissions
~~~~~~~~~~~

It is common to have permissions attached to each model transition.
``django-fsm`` handles this with ``permission`` keyword on the
``transition`` decorator. ``permission`` accepts a permission string, or
callable that expects ``user`` argument and returns True if user can
perform the transition

.. code:: python

    @transition(field=state, source='*', target='publish',
                permission=lambda instance, user: not user.has_perm('myapp.can_make_mistakes'))
    def publish(self):
        pass

    @transition(field=state, source='*', target='publish',
                permission='myapp.can_remove_post')
    def remove(self):
        pass

You can check permission with ``has_transition_permission`` method

.. code:: python

    from django_fsm import has_transition_perm
    def publish_view(request, post_id):
        post = get_object_or_404(BlogPost, pk=post_id)
        if not has_transition_perm(post.publish, request.user):
            raise PermissionDenied

        post.publish()
        post.save()
        return redirect('/')

Model methods
~~~~~~~~~~~~~

``get_all_FIELD_transitions`` Enumerates all declared transitions

``get_available_FIELD_transitions`` Returns all transitions data
available in current state

``get_available_user_FIELD_transitions`` Enumerates all transitions data
available in current state for provided user

Foreign Key constraints support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you store the states in the db table you could use FSMKeyField to
ensure Foreign Key database integrity.

In your model :

.. code:: python

    class DbState(models.Model):
        id = models.CharField(primary_key=True, max_length=50)
        label = models.CharField(max_length=255)

        def __unicode__(self):
            return self.label


    class BlogPost(models.Model):
        state = FSMKeyField(DbState, default='new')

        @transition(field=state, source='new', target='published')
        def publish(self):
            pass

In your fixtures/initial\_data.json :

.. code:: json

    [
        {
            "pk": "new",
            "model": "myapp.dbstate",
            "fields": {
                "label": "_NEW_"
            }
        },
        {
            "pk": "published",
            "model": "myapp.dbstate",
            "fields": {
                "label": "_PUBLISHED_"
            }
        }
    ]

Note : source and target parameters in @transition decorator use pk
values of DBState model as names, even if field "real" name is used,
without \_id postfix, as field parameter.

Integer Field support
~~~~~~~~~~~~~~~~~~~~~

You can also use ``FSMIntegerField``. This is handy when you want to use
enum style constants.

.. code:: python

    class BlogPostStateEnum(object):
        NEW = 10
        PUBLISHED = 20
        HIDDEN = 30

    class BlogPostWithIntegerField(models.Model):
        state = FSMIntegerField(default=BlogPostStateEnum.NEW)

        @transition(field=state, source=BlogPostStateEnum.NEW, target=BlogPostStateEnum.PUBLISHED)
        def publish(self):
            pass

Signals
~~~~~~~

``django_fsm.signals.pre_transition`` and
``django_fsm.signals.post_transition`` are called before and after
allowed transition. No signals on invalid transition are called.

Arguments sent with these signals:

**sender** The model class.

**instance** The actual instance being proceed

**name** Transition name

**source** Source model state

**target** Target model state

Optimistic locking
------------------

``django-fsm`` provides optimistic locking mixin, to avoid concurrent
model state changes. If model state was changed in database
``django_fsm.ConcurrentTransition`` exception would be raised on
model.save()

.. code:: python

    from django_fsm import FSMField, ConcurrentTransitionMixin

    class BlogPost(ConcurrentTransitionMixin, models.Model):
        state = FSMField(default='new')

For guaranteed protection against race conditions caused by concurrently
executed transitions, make sure: \* Your transitions do not have any
side effects except for changes in the database, \* You always run the
save() method on the object within ``django.db.transaction.atomic()``
block.

Following these recommendations, you can rely on
ConcurrentTransitionMixin to cause a rollback of all the changes that
have been executed in an inconsistent (out of sync) state, thus
practically negating their effect.

Drawing transitions
-------------------

Renders a graphical overview of your models states transitions

You need ``pip install graphviz>=0.4`` library and add ``django_fsm`` to
your ``INSTALLED_APPS``:

.. code:: python

    INSTALLED_APPS = (
        ...
        'django_fsm',
        ...
    )

.. code:: bash

    # Create a dot file
    $ ./manage.py graph_transitions > transitions.dot

    # Create a PNG image file only for specific model
    $ ./manage.py graph_transitions -o blog_transitions.png myapp.Blog

Changelog
---------

django-fsm 2.4.0 2016-05-14
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- graph_transition commnad now works with multiple  FSM's per model
- Add ability to set target state from transition return value or callable



.. |Build Status| image:: https://travis-ci.org/kmmbvnr/django-fsm.svg?branch=master
   :target: https://travis-ci.org/kmmbvnr/django-fsm
.. |Downloads| image:: https://img.shields.io/pypi/dm/django-fsm.svg
   :target: https://pypi.python.org/pypi/django-fsm
.. |Gitter| image:: https://badges.gitter.im/Join%20Chat.svg
   :target: https://gitter.im/kmmbvnr/django-fsm?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge
