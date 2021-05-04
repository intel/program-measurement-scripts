# our local base image
FROM ubuntu:18.04 

LABEL description="Container for use with CapeScripts" 


# install build dependencies 
RUN apt-get update && apt-get install -y g++ rsync zip openssh-server make \
 software-properties-common
# Following steps from ROSE website: https://github.com/rose-compiler/rose/wiki/Install-Using-apt-get
RUN add-apt-repository ppa:rosecompiler/rose-development
RUN apt-get update && apt-get install -y \
 rose \
 # Optional: Installs ROSE tools in addition to ROSE Core
 rose-tools \
# More utilities specified at https://gitlab.com/Wingpad/rose-utils
 default-jdk \
 git g++ wget \
# More basic utilities
 vim \
 sudo \
 python3-pip 

RUN python3 -m pip install sympy

# configure SSH for communication with Visual Studio 
RUN mkdir -p /var/run/sshd

RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \ 
   ssh-keygen -A 

# expose port 22 
EXPOSE 22

ENV ROSE_HOME=/usr/rose

RUN groupadd -g 8088 appuser && \
   useradd -m -d /home/appuser -s /bin/bash -u 8088 -g appuser -G sudo appuser

USER appuser
WORKDIR /home/appuser
COPY --chown=appuser rose-utils/ /home/appuser

RUN cd /home/appuser/rose-utils