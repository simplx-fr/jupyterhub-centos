#  jupyterhub-centos

JupyterHub: A multi-user server for Jupyter notebooks 
Source coming from https://github.com/jupyter/jupyterhub

## Getting started

See the [getting started document](docs/source/getting-started.md) for the
basics of configuring your JupyterHub deployment.

### Docker

There is a ready to go docker image build on top of CentOs 7.
https://hub.docker.com/r/simplx/jupyterhub-centos/

It can be started with the following command:

    docker run -p fwdport:8000 simplx/jupyterhub-centos

This command will create a container that you can stop and resume with `docker stop/start`.