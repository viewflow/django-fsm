from setuptools import setup, find_packages

setup(
    name='django-fsm',
    version='1.0.0',
    description='Django friendly finite state machine support.',
    author='Mikhail Podgurskiy',
    author_email='kmmbvnr@gmail.com',
    url='http://github.com/kmmbvnr/djang-fsm',
    keywords = "django",
    packages=find_packages(),
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
        'Framework :: Django',
    ]
)
