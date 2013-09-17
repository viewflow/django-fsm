from setuptools import setup

try:
    long_description = open('README.md').read()
except IOError:
    long_description = ''

setup(
    name='django-fsm',
    version='1.5.0',
    description='Django friendly finite state machine support.',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    url='http://github.com/kmmbvnr/django-fsm',
    keywords = "django",
    packages=['django_fsm', 'django_fsm.db', 'django_fsm.db.fields', 'django_fsm.management', 'django_fsm.management.commands'],
    include_package_data=True,
    zip_safe=False,
    license='MIT License',
    platforms = ['any'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ]
)
