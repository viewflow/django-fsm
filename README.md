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
------------
```bash
$ pip install django-fsm
```
Or, for the latest git version
```bash
$ pip install -e git://github.com/kmmbvnr/django-fsm.git#egg=django-fsm
```

Library has full Python 3 support, for the graph transition drawing
you should install python3 compatible graphviz version
from git+https://github.com/philipaxer/pygraphviz

Usage
-----

Add FSMState field to your model
```python
from django_fsm import FSMField, transition

class BlogPost(models.Model):
	state = FSMField(default='new')
```

Use the `transition` decorator to annotate model methods
```python
@transition(field=state, source='new', target='published')
def publish(self):
	"""
	This function may contain side-effects, 
	like updating caches, notifying users, etc.
	The return value will be discarded.
	"""
```

`source` parameter accepts a list of states, or an individual state.
You can use `*` for source, to allow switching to `target` from any state.

If calling publish() succeeds without raising an exception, the state field
will be changed, but not written to the database.
```python
from django_fsm import can_proceed

def publish_view(request, post_id):
    post = get_object__or_404(BlogPost, pk=post_id)
    if not can_proceed(post.publish):
        raise Http404;
	
    post.publish()
    post.save()
    return redirect('/')
```

If some conditions are required to be met before the changing state, use the
`conditions` argument to `transition`. `conditions` must be a list of functions
that takes one argument, the model instance.  The function must return either
`True` or `False` or a value that evaluates to `True` or `False`. If all
functions return `True`, all conditions are considered to be met and transition
is allowed to happen. If one of the functions return `False`, the transition
will not happen. These functions should not have any side effects.

You can use ordinary functions
```python
def can_publish(instance):
    # No publishing after 17 hours
    if datetime.datetime.now().hour > 17:
        return False
    return True
```

Or model methods
```python
def can_destroy(self):
	return self.is_under_investigation()
```

Use the conditions like this:
```python
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
```

You could instantiate field with protected=True option, that prevents direct state field modification
```python
class BlogPost(models.Model):
    state = FSMField(default='new', protected=True)

model = BlogPost()
model.state = 'invalid' # Raises AttributeError
```

Custom properties can be added by providing a dictionary to the `custom` keyword on the `transition` decorator.
```python
@transition(field=state,
            source='*',
            target='onhold',
            custom=dict(verbose='Hold for legal reasons'), transition_type='manual')
def legal_hold(self):
    """
    Side effects galore
    """
```

### get_available_FIELD_transitions
Returns all transitions data available in current state

### get_all_FIELD_transitions
Enumerates all declared transitions


### Foreign Key constraints support 

If you store the states in the db table you could use FSMKeyField to
ensure Foreign Key database integrity.

In your model : 
```python
class DbState(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    label = models.CharField(max_length=255)

    def __unicode__(self);
        return self.label


class BlogPost(models.Model):
    state = FSMKeyField(DbState, default='new')

@transition(field=state, source='new', target='published')
    def publish(self):
        pass
```

In your fixtures/initial_data.json :
```json
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
```

Note : source and target parameters in @transition decorator use pk values of DBState model
as names, even if field "real" name is used, without _id postfix, as field parameter.


### Integer Field support 

You can also use `FSMIntegerField`. This is handy when you want to use enum style constants. This field is also `db_index=True` by default for speedy db loookups.
```python
class BlogPostStateEnum(object):
    NEW = 10
    PUBLISHED = 20
    HIDDEN = 30

class BlogPostWithIntegerField(models.Model):
    state = FSMIntegerField(default=BlogPostStateEnum.NEW)

    @transition(source=BlogPostStateEnum.NEW, target=BlogPostStateEnum.PUBLISHED)
    def publish(self):
        pass
```

### Signals

`django_fsm.signals.pre_transition` and `django_fsm.signals.post_transition` are called before 
and after allowed transition. No signals on invalid transition are called.

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


### Drawing transitions

Renders a graphical overview of your models states transitions
```bash
# Create a dot file
$ ./manage.py graph_transitions > transitions.dot

# Create a PNG image file only for specific model
$ ./manage.py graph_transitions -o blog_transitions.png myapp.Blog
```

Changelog
---------
    
<img src="https://f.cloud.github.com/assets/41479/2227946/a9e77760-9ad0-11e3-804f-301d075470fe.png" alt="django-fsm" width="100px"/>

### django-fsm 2.0.0 2014-03-15
* Backward incompatible release
* All public code import moved directly to django_fsm package
* Correct support for several @transitions decorator with different source states and conditions on same method
* save parameter from transition decorator removed
* get_available_FIELD_transitions return Transition data object instead of tuple
* Models got get_available_FIELD_transitions, even if field specified as string reference
* New get_all_FIELD_transitions method contributed to class

### django-fsm 1.6.0 2014-03-15
* FSMIntegerField and FSMKeyField support

### django-fsm 1.5.1 2014-01-04

* Ad-hoc support for state fields from proxy and inherited models

### django-fsm 1.5.0 2013-09-17

* Python 3 compatibility

### django-fsm 1.4.0 2011-12-21

* Add graph_transition command for drawing state transition picture

### django-fsm 1.3.0 2011-07-28

* Add direct field modification protection

### django-fsm 1.2.0 2011-03-23

* Add pre_transition and post_transition signals

### django-fsm 1.1.0 2011-02-22

* Add support for transition conditions 
* Allow multiple FSMField in one model
* Contribute get_available_FIELD_transitions for model class

### django-fsm 1.0.0 2010-10-12

* Initial public release
