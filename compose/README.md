## Docker

### Setting up local environment

*Requirements*
- Docker engine or Docker Desktop
- Docker compose
  - It works with both v1 and v2
  - For the sake of uniformity, we are using v2 in our examples

###### Build
```bash
$ docker compose -f local.yml build
```

###### Run Services
```bash
$ docker compose -f local.yml up
```
For specific service, you may specify the service name
```bash
$ docker compose -f local.yml up django
```
To force rebuilding of images
```bash
$ docker compose -f local.yml up --build
```
