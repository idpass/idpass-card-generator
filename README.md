# Card Generator Backend

Automate creating of multiple IDs, badges and cards for different people. Just upload your template and start generating your cards with different information.


[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: Apache 2.0

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Setting Up Your Users

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

-   To create a **normal account**, please login as a superuser in `/admin`
  - Create new account in `/admin/users/user/add/`
- To access the card endpoints, you will need your authentication token for your authorization header
  - Get your access token in `api/v1/auth-token`

## Using the CARD API
This is the first version of the api, refer to this [documentation on its usage](card_generator/api/v1/cards/README.md).
For the API specification, run the django application and visit [OPENAPI documentation](http://localhost:8000/api/docs).

## Basic Commands

### Local Setup
To setup the local development environment, please refer to this [documentation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html).

To setup using docker, please refer to this [documentation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html).


### Type checks

Running type checks with mypy:

    $ mypy card_generator

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).
