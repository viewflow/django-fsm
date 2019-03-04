from setuptools import setup

try:
    long_description = open('README.rst').read()
except IOError:
    long_description = ''

setup(
    name='django-fsa',
    version='2.7.0',
    description='Django friendly finite state machine support, forked from django-fsm',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Antoine Fontaine',
    author_email='antoine.fontaine@gmail.com',
    url='http://github.com/mdziwny/django-fsm',
    keywords="django",
    packages=['django_fsm', 'django_fsm.management', 'django_fsm.management.commands'],
    include_package_data=True,
    zip_safe=False,
    license='MIT License',
    platforms=['any'],
    install_requires=["django>=1.11"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
