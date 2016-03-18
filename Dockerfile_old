# A base docker image that includes juptyerhub and IPython master
# build on top of a centos distrib

FROM centos:7

MAINTAINER Nicolas Duval <nicolas.duval@simplx.fr>

# install Python with conda, utf8 locale
RUN localedef -c -f UTF-8 -i en_US en_US.UTF-8 && \
    yum -y install wget bzip2 openssl openssl-devel git && \
    wget https://repo.continuum.io/miniconda/Miniconda3-3.9.1-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    chmod +x /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -f -b -p /opt/conda && \
    /opt/conda/bin/conda install --yes python=3.5 sqlalchemy tornado jinja2 traitlets requests pip && \
    /opt/conda/bin/pip install --upgrade pip

ENV PATH=/opt/conda/bin:$PATH
ENV LANG=en_US.UTF-8

# install npm, nodejs & js dependencies
RUN wget http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm -O /tmp/epel.rpm && \
    rpm -ivh /tmp/epel.rpm && \
    yum install -y npm.noarch && \
    npm install -g configurable-http-proxy && \
    rm -f /tmp/*

# Copy JupyterHub 
WORKDIR /srv/
ADD . /srv/jupyterhub
WORKDIR /srv/jupyterhub/

# Install jupyterhub 
RUN python setup.py js && pip install -r dev-requirements.txt -e . && \
    rm -rf node_modules ~/.cache ~/.npm

WORKDIR /srv/jupyterhub/

# Port 8000 to be mapped when run
EXPOSE 8000

LABEL org.jupyter.service="jupyterhub"

# Derivative containers should add jupyterhub config,
# which will be used when starting the application.
ONBUILD ADD jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

# Launch jupyterhub
CMD ["jupyterhub", "--no-ssl", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
