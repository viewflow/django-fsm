Django friendly finite state machine support
============================================

django-fsm adds declarative states managment for django models.
Instead of adding some state field to a django model, and manage it
values by hand, you could use FSMState field and mark model methods
with transition decorator that will perform checks and switch state
field value on succed model method call.

Installation
------------

    $ python setup.py install

Or, for the latest git version

    $ pip install -e git://github.com/kmmbvnr/django-fsm.git#egg=django-fsm


Usage
-----

Add FSMState field to you model
    from django_fsm.db.fields import FSMField, transition

    class BlogPost(models.Model):
        state = FSMField(default='new')


Use transition decorator to annotate model methods

    @transition(source='new', target='published')
    def publish(self):
            """
            Some additional code goes here
            """

`source` parameter accepts a list of states, or an individual state.
You can use '*' for source, to allow the switching to target from any state


Succeed call of the publish() method will change the state field

    from django_fsm.db.fields import can_proceed
    def publish_view(request, post_id):
        post = get_object__or_404(BlogPost, pk=post_id)
        if not can_proceed(post.publish):
             raise Http404;

        post.publish()
        post.save()
        return redirect('/')

If you store the states in the db table you could use FSMKeyField to
enshure Foreign Key database integrity.














