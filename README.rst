Django FSM 5.0
==============

State machines for Python objects and Django models.

Version 5.0 brings the ``viewflow.fsm`` implementation back into the standalone
``django-fsm`` package. It provides the ``State`` API and model-backed
``FSMField``, ``FSMIntegerField`` and ``FSMKeyField`` adapters. Viewflow Pro
uses this package and keeps the ``viewflow.fsm`` import paths as re-exports.

The core depends on Django, not on Viewflow or Django REST Framework. Python
3.10+ and Django 5.2+ are required. Django 6.0+ requires Python 3.12+.

Installation
------------

.. code-block:: console

    python -m pip install 'django-fsm>=5,<6'

Add ``django_fsm`` to ``INSTALLED_APPS`` to use the ``graph_transitions``
management command. State machines and model fields do not require app
registration. Install ``django-fsm[graphviz]`` for the optional graph command.

Python state machines
---------------------

``State`` stores state on a Python object and guards its transition methods.
It can be used without configuring Django settings.

.. code-block:: python

    from django_fsm import State

    class Review:
        state = State(states=None, default='new')

        @state.transition(source='new', target='published')
        def publish(self):
            return self.state

    review = Review()
    assert review.publish() == 'published'
    # review.state = 'new' raises AttributeError.
    # A second review.publish() raises NoTransition.

An ordinary target is applied before the method runs. If the method raises,
the source state is restored in memory. ``conditions`` validate the transition;
``permission`` is checked by ``has_perm(user)`` and UI/REST integrations, not
implicitly by a direct method call. The native ``State.transition`` API denies
permission checks by default; set ``permission=None`` to allow any user.

Use ``this`` for forward references to conditions or permission methods:

.. code-block:: python

    from django_fsm import State, this

    class Review:
        state = State(states=None, default='new')

        @state.transition('new', 'published', conditions=[this.is_ready])
        def publish(self):
            pass

        def is_ready(self):
            return True

Django model fields
-------------------

The model adapters store state in a normal database column. No separate flow
class, getter or setter is needed.

.. code-block:: python

    from django.db import models
    from django_fsm import FSMField, can_proceed, transition

    class Job(models.Model):
        status = FSMField(default='new', protected=True)

        @transition(field=status, source='new', target='running', on_error='failed')
        def start(self):
            pass

    job = Job.objects.create()
    if can_proceed(job.start):
        job.start()
        job.save()

``FSMField`` defaults to ``max_length=50``. ``FSMIntegerField`` stores integer
states. ``FSMKeyField`` stores a foreign key: both ``job.status`` and
``job.status_id`` expose its raw key, rather than a related model object.
Foreign-key joins, ``to_field``, forms and deferred loading are supported.

The standalone ``transition`` decorator accepts a field object or its name,
such as ``field='status'`` in a Python mixin. ``source='*'`` (the default)
accepts any source; ``source='+'`` accepts any source except the target.
``target=None`` leaves the state unchanged. Calling ``status.transition(...)``
directly follows the native API: use ``State.ANY`` and omit the target for a
guard. Set ``permission`` explicitly for native permission checks.

The standalone decorator allows any user by default. A permission string
checks ``user.has_perm(name, instance)`` and then global permission. Call
``has_transition_perm(job.start, user)`` to check state, conditions and
permission together. Models also provide ``get_all_status_transitions()``,
``get_available_status_transitions()`` and
``get_available_user_status_transitions(user)``. Their metadata preserves the
legacy ``'*'`` and ``None`` values and supports lookup by transition name.

``protected=True`` blocks direct assignment after initialization.
``FSMModelMixin`` lets ``refresh_from_db()`` refresh other fields while
skipping protected and deferred fields by default. It does not reload the
protected state. Both ``protected`` and ``enforce_initial`` default to false.
``enforce_initial=True`` validates inserted rows, including ``bulk_create()``,
against the default state; raw SQL and fixture loading bypass it.

Signals, errors and dynamic targets
-----------------------------------

Model transitions emit ``pre_transition`` and ``post_transition`` from
``django_fsm.signals``. Plain ``State`` transitions do not emit them.
The pre signal runs after validation, before target resolution and assignment.
Both signals receive ``instance``, ``name``, ``field``, ``source``, ``target``,
``method_args`` and ``method_kwargs``. The sender is the source model class,
including for transitions that switch proxy classes.

``on_error`` selects an error state, emits the post signal with ``exception``,
and re-raises the original exception. Without an error target, failure
restores the source state and proxy class without a post signal. Rejected
sources and conditions do not emit signals or apply an error target.

``RETURN_VALUE(*allowed_states)`` selects the target from the method's return
value. ``GET_STATE(func, states=[...])`` computes it from the instance and call
arguments before the method runs. Both are also available on ``State`` and
raise ``InvalidTargetState`` for an invalid result.

``state_choices`` entries ``(value, label, 'app.ProxyModel')`` select a proxy
class on assignment, loading and transition. An unqualified name resolves in
the field's app. The referenced class must be a proxy of the same concrete
model. Migrations preserve the mapping.

Concurrent transitions
----------------------

Add ``ConcurrentTransitionMixin`` to compare observed FSM state values in the
SQL ``UPDATE`` predicate. A stale save raises ``ConcurrentTransition``.

.. code-block:: python

    from django.db import models, transaction
    from django_fsm import ConcurrentTransitionMixin, FSMField

    class Job(ConcurrentTransitionMixin, models.Model):
        status = FSMField(default='new')

        @status.transition('new', 'running')
        def start(self):
            pass

    with transaction.atomic():
        job = Job.objects.get(pk=job_id)
        job.start()
        job.save()

Catch ``ConcurrentTransition`` outside the transaction to roll back other
database writes. The mixin does not undo external side effects or restore
Python attributes after rollback. It versions state values, not other fields,
and cannot detect a state that changed and returned to the same value.
Queryset updates, bulk writes and raw SQL bypass the check.

Partial saves only advance the baseline for persisted state fields. Partial
refreshes only reset refreshed fields. Deferred states acquire a baseline
when first observed; an otherwise unloaded state is read at save time.

Charts and integrations
-----------------------

``chart(Review.state)`` returns DOT text without Graphviz or Viewflow.
For model fields, install the Graphviz extra and run:

.. code-block:: console

    python manage.py graph_transitions myapp.Job

``django_fsm.admin.FlowAdminMixin`` and
``django_fsm.viewset.FlowViewsMixin`` provide the Viewflow admin and viewset
integrations. They use Viewflow Pro templates and assets. Install a Viewflow
Pro release that re-exports Django FSM 5.0 to use them. The core package does
not install Viewflow as a dependency.

``django_fsm.rest.FlowRESTMixin`` provides the optional DRF integration;
install ``django-fsm[rest]``. These integrations are imported only when used.
Existing ``viewflow.fsm`` module paths remain available through Viewflow Pro.

Upgrading from django-fsm 3.x
-----------------------------

Existing model-field imports and decorators remain available. Historical
migration paths such as ``django_fsm.FSMField`` still resolve. State stays in
the same database columns; inspect generated ``AlterField`` operations before
applying migrations.

The execution engine has changed: ordinary targets and ``GET_STATE`` apply
before the method runs. Code that reads state inside a transition observes
the target. ``RETURN_VALUE`` applies after the method returns. Native
exceptions include ``NoTransition`` and ``TransitionConditionsUnmet``, both
subclasses of ``TransitionNotAllowed``. Invalid dynamic targets raise
``InvalidTargetState``. Private ``_django_fsm`` metadata is not recreated.
Integrations that inspect it need changes.

Development
-----------

.. code-block:: console

    python -m pip install -e '.[test]'
    python tests/manage.py test testapp django_fsm.tests
    python -m pip install build twine
    python -m build
    python -m twine check dist/*

The original test files are retained in ``django_fsm/tests`` and
``tests/testapp/tests``. New tests cover the extracted State API and model
adapters. ``tox`` runs the supported Python/Django combinations.

Typing
------

The wheel includes ``py.typed``. The core and consumer examples are checked
with mypy and pyright in basic mode. Dynamic decorators, model helpers and
state values use permissive types, including ``Any`` where needed; these
annotations do not validate the set of allowed states.

.. code-block:: console

    python -m pip install -e '.[test,typing]'
    python -m mypy
    pyright
    PYTHONPATH=.:tests python -m mypy --config-file tests/typing/mypy-plugin.ini tests/typing/usage.py

The last command also checks the examples with the django-stubs plugin.
Field-name-specific methods are attached at runtime. On a model that does
not use either FSM model mixin, access these generated helpers with
``getattr`` or annotate the helper as ``Any`` if the checker cannot resolve it.

License
-------

Django FSM 5.0 uses AGPL-3.0-or-later with the additional permissions in
``LICENSE_EXCEPTION``, matching django-jsonstore. See ``LICENSE`` and
``LICENSE_EXCEPTION`` for the terms. The MIT notice for retained legacy code
and tests is preserved in ``LICENSE_LEGACY``.
