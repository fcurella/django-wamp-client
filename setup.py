from setuptools import setup, find_packages

setup(
    name='django-wamp-client',
    version="0.0.3",
    description='Wamp Client for Django Channels',
    long_description='',
    author='Flavio Curella',
    author_email='flavio.curella@gmail.com',
    url='https://github.com/fcurella/django-wamp-client',
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
    install_requires=[
        'autobahn',
        'channels',
    ]
)
