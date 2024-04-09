Changelog
=========

django-fsm 2.8.2 2024-04-09
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fix graph_transitions commnad for Django>=4.0
- Preserve chosen "using" DB in ConcurentTransitionMixin
- Fix error message in GET_STATE
- Implement Transition __hash__ and __eq__ for 'in' operator


django-fsm 2.8.1 2022-08-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Improve fix for get_available_FIELD_transition


django-fsm 2.8.0 2021-11-05
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fix get_available_FIELD_transition on django>=3.2
- Fix refresh_from_db for ConcurrentTransitionMixin


django-fsm 2.7.1 2020-10-13
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fix warnings on Django 3.1+


django-fsm 2.7.0 2019-12-03
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Django 3.0 support
- Test on Python 3.8


django-fsm 2.6.1 2019-04-19
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Update pypi classifiers to latest django/python supported versions
- Several fixes for graph_transition command


django-fsm 2.6.0 2017-06-08
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fix django 1.11 compatibility
- Fix TypeError in `graph_transitions` command when using django's lazy translations


django-fsm 2.5.0 2017-03-04
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- graph_transition command fix for django 1.10
- graph_transition command supports GET_STATE targets
- signal data extended with method args/kwargs and field
- sets allowed to be passed to the transition decorator


django-fsm 2.4.0 2016-05-14
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- graph_transition commnad now works with multiple  FSM's per model
- Add ability to set target state from transition return value or callable


django-fsm 2.3.0 2015-10-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add source state shortcut '+' to specify transitions from all states except the target
- Add object-level permission checks
- Fix translated labels for graph of FSMIntegerField
- Fix multiple signals for several transition decorators


django-fsm 2.2.1 2015-04-27
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Improved exception message for unmet transition conditions.
- Don't send post transition signal in case of no state changes on
  exception
- Allow empty string as correct state value
- Improved graphviz fsm visualisation
- Clean django 1.8 warnings

django-fsm 2.2.0 2014-09-03
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Support for `class
  substitution <http://schinckel.net/2013/06/13/django-proxy-model-state-machine/>`__
  to proxy classes depending on the state
- Added ConcurrentTransitionMixin with optimistic locking support
- Default db\_index=True for FSMIntegerField removed
- Graph transition code migrated to new graphviz library with python 3
  support
- Ability to change state on transition exception

django-fsm 2.1.0 2014-05-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Support for attaching permission checks on model transitions

django-fsm 2.0.0 2014-03-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Backward incompatible release
- All public code import moved directly to django\_fsm package
- Correct support for several @transitions decorator with different
  source states and conditions on same method
- save parameter from transition decorator removed
- get\_available\_FIELD\_transitions return Transition data object
  instead of tuple
- Models got get\_available\_FIELD\_transitions, even if field
  specified as string reference
- New get\_all\_FIELD\_transitions method contributed to class

django-fsm 1.6.0 2014-03-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- FSMIntegerField and FSMKeyField support

django-fsm 1.5.1 2014-01-04
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Ad-hoc support for state fields from proxy and inherited models

django-fsm 1.5.0 2013-09-17
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Python 3 compatibility

django-fsm 1.4.0 2011-12-21
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add graph\_transition command for drawing state transition picture

django-fsm 1.3.0 2011-07-28
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add direct field modification protection

django-fsm 1.2.0 2011-03-23
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add pre\_transition and post\_transition signals

django-fsm 1.1.0 2011-02-22
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add support for transition conditions
- Allow multiple FSMField in one model
- Contribute get\_available\_FIELD\_transitions for model class

django-fsm 1.0.0 2010-10-12
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Initial public release
