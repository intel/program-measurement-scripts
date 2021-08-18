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
 # Used in const.sh in Capescripts
 locales \
 # Used in Capescripts
 bc \
 time \
 python3-pip \
 cpufrequtils numactl

RUN chmod u+s /usr/bin/cpufreq-set

# For Locus
RUN apt-get install -y lib32readline8 lib32readline-dev \
 cproto ctags build-essential libreadline-dev libncurses5-dev \
 libncursesw5-dev \
 subversion python-is-python3 \
 indent swig
 #tex4ht
 #texlive-latex-base texlive-latex-extra 
 

 # Used in const.sh
RUN locale-gen en_US.utf8 && update-locale

RUN python3 -m pip install sympy \
  && python3 -m pip install csvkit \
  && python3 -m pip install openpyxl \
  && python3 -m pip install et_xmlfile \
  && python3 -m pip install pandas


# configure SSH for communication with Visual Studio 
RUN mkdir -p /var/run/sshd

RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \ 
   ssh-keygen -A 

# expose port 22 
EXPOSE 22

ENV ROSE_HOME=/usr/rose
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

RUN groupadd -g 8088 builder && \
   useradd -m -d /home/builder -s /bin/bash -u 8088 -g builder -G sudo builder

RUN echo "builder:builder" | chpasswd

RUN mkdir /share && chmod a+rwx /share && chmod +t /share

USER builder
ENV USER=builder
COPY --chown=builder rose-utils/ /share/rose-utils
COPY --chown=builder ice-locus-dev/ /share/ice-locus-dev
COPY --chown=builder pocc-1.1/ /share/pocc-1.1

WORKDIR /share/rose-utils
RUN ./build.sh

USER root
WORKDIR /share/ice-locus-dev
RUN python3 setup.py install

USER builder
# Setup for subversion proxy
# COPY foo /home/builder/.subversion/servers

RUN mkdir /share/pips
COPY --chown=builder gen_svn_servers.sh /share/pips
WORKDIR /share/pips
RUN alias g77=gfortran
RUN wget https://scm.cri.ensmp.fr/svn/nlpmake/trunk/makes/setup_pips.sh \
   && chmod +x setup_pips.sh \
   && ./gen_svn_servers.sh \
   && ./setup_pips.sh --dynamic --light --pyconf=python3-config


# Setting up following https://bitbucket.org/thiagotei/uiuc-compiler-opts/wiki/Home
USER root
# Need to install gcc-4.9 
# See https://askubuntu.com/questions/1235819/ubuntu-20-04-gcc-version-lower-than-gcc-7
RUN echo "deb http://dk.archive.ubuntu.com/ubuntu/ xenial main" >> /etc/apt/sources.list && echo "deb http://dk.archive.ubuntu.com/ubuntu/ xenial universe" >> /etc/apt/sources.list
RUN apt update && apt-get install -y gcc-4.9 g++-4.9 uuid-dev libswitch-perl

USER builder
ENV CC=gcc-4.9
ENV CXX=g++-4.9
WORKDIR /share/pocc-1.1
RUN ./install.sh && cd analyzers/candl && patch -p1 -i ../../pocc-1.1-candl-0.6.2.patch && make install