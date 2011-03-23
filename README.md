============================================
Django friendly finite state machine support
============================================

django-fsm adds declarative states management for django models.
Instead of adding some state field to a django model, and manage it
values by hand, you could use FSMState field and mark model methods
with the `transition` decorator. Your method will contain the side-effects
of the state change.

The decorator also takes a list of conditions, all of which must be met
before a transition is allowed.

Installation
============

    $ pip install django-fsm

Or, for the latest git version

    $ pip install -e git://github.com/kmmbvnr/django-fsm.git#egg=django-fsm


Usage
=====

Add FSMState field to you model
    from django_fsm.db.fields import FSMField, transition

    class BlogPost(models.Model):
        state = FSMField(default='new')


Use the `transition` decorator to annotate model methods

    @transition(source='new', target='published')
    def publish(self):
        """
        This function may contain side-effects, 
        like updating caches, notifying users, etc.
        The return value will be discarded.
        """

`source` parameter accepts a list of states, or an individual state.
You can use `*` for source, to allow switching to `target` from any state.

If calling publish() succeeds without raising an exception, the state field
will be changed, but not written to the database.

    from django_fsm.db.fields import can_proceed

    def publish_view(request, post_id):
        post = get_object__or_404(BlogPost, pk=post_id)
        if not can_proceed(post.publish):
             raise Http404;

        post.publish()
        post.save()
        return redirect('/')

If you use the transition decorator with the `save` argument set to `True`,
the new state will be written to the database

    @transition(source='new', target='published', save=True)
    def publish(self):
        """
        Side effects other than changing state goes here
        """

If you require some conditions to be met before changing state, use the
`conditions` argument to `transition`. `conditions` must be a list of functions
that take one argument, the model instance.  The function must return either
`True` or `False` or a value that evaluates to `True` or `False`. If all
functions return `True`, all conditions are considered to be met and transition
is allowed to happen. If one of the functions return `False`, the transition
will not happen. These functions should not have any side effects.

You can use ordinary functions

    def can_publish(instance):
        # No publishing after 17 hours
        if datetime.datetime.now().hour > 17:
           return False
        return True

Or model methods

    def can_destroy(self):
        return self.is_under_investigation()

Use the conditions like this:

    @transition(source='new', target='published', conditions=[can_publish])
    def publish(self):
        """
        Side effects galore
        """

    @transition(source='*', target='destroyed', conditions=[can_destroy])
    def destroy(self):
        """
        Side effects galore
        """

get_available_FIELD_transitions
-------------------------------

You could specify FSMField explicitly in transition decorator.

    class BlogPost(models.Model):
        state = FSMField(default='new')

        @transition(field=state, source='new', target='published')
        def publish(self):
    	    pass

This allows django_fsm to contribute to model class get_available_FIELD_transitions method,
that returns list of (target_state, method) available from current model state

### Foreign Key constraints support 

If you store the states in the db table you could use FSMKeyField to
ensure Foreign Key database integrity.

Signals
-------

`django_fsm.signals.pre_transition` and `django_fsm.signals.pre_transition` called before 
and after allowed transition. No signals on invalid transition call.

Arguments sent with these signals:

**sender**
   The model class.

**instance**
   The actual instance being procceed

**name**
   Transition name

**source**
   Source model state

**target**
   Target model state


Changelog
---------

django-fsm 1.2.0 2011-03-23
    * Add pre_transition and post_transition signals

django-fsm 1.1.0 2011-02-22
    * Add support for transition conditions 
    * Allow multiple FSMField in one model
    * Contribute get_available_FIELD_transitions for model class

django-fsm 1.0.0 2010-10-12
    * Initial public release

