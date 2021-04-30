# our local base image
FROM ubuntu:18.04 

LABEL description="Container for use with CapeScripts" 

# install build dependencies 
RUN apt-get update && apt-get install -y g++ rsync zip openssh-server make 

# configure SSH for communication with Visual Studio 
RUN mkdir -p /var/run/sshd

RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \ 
   ssh-keygen -A 

# expose port 22 
EXPOSE 22

# Following steps from ROSE website: https://github.com/rose-compiler/rose/wiki/Install-Using-apt-get
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:rosecompiler/rose-development
RUN apt-get install -y rose
RUN apt-get install -y rose-tools # Optional: Installs ROSE tools in addition to ROSE Core

# More basic utilities
RUN apt-get install -y git
RUN apt-get install -y vim
