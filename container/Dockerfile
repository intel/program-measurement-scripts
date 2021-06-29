# our local base image
FROM ubuntu:20.04 

LABEL description="Container for use with CapeScripts" 

#ENV http_proxy http://proxy-chain.intel.com:911
#ENV https_proxy http://proxy-chain.intel.com:912

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
 # Need pkg-config to csvkit
 pkg-config \
 python3-pip 

RUN python3 -m pip install sympy
RUN python3 -m pip install csvkit
RUN python3 -m pip install openpyxl
RUN python3 -m pip install et_xmlfile
RUN python3 -m pip install pandas


# configure SSH for communication with Visual Studio 
RUN mkdir -p /var/run/sshd

RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \ 
   ssh-keygen -A 

# expose port 22 
EXPOSE 22

ENV ROSE_HOME=/usr/rose
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

RUN groupadd -g 8088 appuser && \
   useradd -m -d /home/appuser -s /bin/bash -u 8088 -g appuser -G sudo appuser

RUN echo "appuser:appuser" | chpasswd

USER appuser
WORKDIR /home/appuser
COPY --chown=appuser rose-utils/ /home/appuser

WORKDIR /home/appuser/rose-utils
RUN ./build.sh