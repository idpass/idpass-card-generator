# Card Generator Backend

Automate creating of multiple IDs, badges and cards for different people. Just upload your template and start generating your cards with different information.


[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


### Getting Started

Clone this repo
```shell
git clone https://github.com/idpass/idpass-card-generator.git
```

*Requirements*
- Docker engine or Docker Desktop
- Docker compose
  - It works with both v1 and v2
  - For the sake of uniformity, we are using v2 in our examples

###### Build
```shell
docker compose -f local.yml build
```

###### Run Services
```shell
docker compose -f local.yml up
```

### Creating a user
-   To create a **superuser account**, use this command:

```shell
docker compose -f local.yml run --rm django python manage.py createsuperuser
```

-   To create a **normal account**, please login as a superuser in `/admin`
  - Create new account in `/admin/users/user/add/`
- To access the card endpoints, you will need your authentication token for your authorization header
  - Get your access token in `api/v1/auth-token`

## Documentation
Endpoints are documented using [OPENAPI specification](http://localhost:8000/api/docs). Visit this page to try and discover how this endpoints work.

For more in-depth explanation of card endpoints, please visit the [documentation on its usage](card_generator/api/v1/cards/README.md)

## Configuration
For config settings, environment variables are stored in `.envs/`.
Local values are already provided for quick setup of local environment.

Django configuration settings are divided into different environments following 12 factor app principle. You will see that under `config/settings` we have `local`, `production`, `test` and the `base` config.


## Development
Docker can help developers quickly set up the project environment with only a few commands. This project can be setup with or without Docker.
- [Local setup without Docker](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html)
- [Local setup with Docker](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html)

#### Type checks

Running type checks with mypy:
```shell
mypy card_generator
```

#### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

```shell
coverage run -m pytest
coverage html
open htmlcov/index.html
```

#### Running tests with pytest
```shell
pytest
```

## Deployment
This project expects you will have a production environment files located in `.envs/.production` with the same `.django` and `.postgres` files inside.


Deployment with Docker and Compose is easy and can be setup on any remote server.
Follow [this instructions](https://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html) to deploy this project to a production server.

## License
[Apache 2.0](./LICENSE)
