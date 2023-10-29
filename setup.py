from __future__ import annotations

from setuptools import setup

try:
    long_description = open("README.rst").read()
except OSError:
    long_description = ""

setup(
    name="django-fsm",
    version="2.8.1",
    description="Django friendly finite state machine support.",
    author="Mikhail Podgurskiy",
    author_email="kmmbvnr@gmail.com",
    url="http://github.com/kmmbvnr/django-fsm",
    keywords="django",
    packages=["django_fsm", "django_fsm.management", "django_fsm.management.commands"],
    include_package_data=True,
    zip_safe=False,
    license="MIT License",
    platforms=["any"],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
