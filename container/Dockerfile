# our local base image
FROM ubuntu:20.04 

LABEL description="Container for use with CapeScripts" 

#ENV http_proxy http://proxy-chain.intel.com:911
#ENV https_proxy http://proxy-chain.intel.com:912

# install build dependencies 

# Need to install gcc-4.9 
# See https://askubuntu.com/questions/1235819/ubuntu-20-04-gcc-version-lower-than-gcc-7
RUN echo "deb http://dk.archive.ubuntu.com/ubuntu/ xenial main" >> /etc/apt/sources.list && echo "deb http://dk.archive.ubuntu.com/ubuntu/ xenial universe" >> /etc/apt/sources.list

RUN apt-get update && apt-get install --no-install-recommends -y make \
 software-properties-common && \
 add-apt-repository ppa:rosecompiler/rose-development && \
 apt-get update && apt-get install --no-install-recommends -y g++ rsync zip openssh-server \
# Following steps from ROSE website: https://github.com/rose-compiler/rose/wiki/Install-Using-apt-get
   rose \
 # Optional: Installs ROSE tools in addition to ROSE Core
   rose-tools \
# More utilities specified at https://gitlab.com/Wingpad/rose-utils
   default-jdk \
   git git-lfs g++ wget \
# More basic utilities
   vim \
   less \
   sudo \
 # Need pkg-config to csvkit
   pkg-config \
 # Used in const.sh in Capescripts
   locales \
 # Used in Capescripts
   bc \
   time \
   python3-pip \
   cpufrequtils numactl \
# For Locus
   lib32readline8 lib32readline-dev \
   cproto ctags build-essential libreadline-dev libncurses5-dev \
   libncursesw5-dev \
   subversion python-is-python3 \
   indent swig \
   # for pocc, need to install gcc-4.9 
   gcc-4.9 g++-4.9 uuid-dev libswitch-perl \
   # for hugeadm
   libhugetlbfs-bin \
   # for new build of cmake
   libssl-dev \
   # for UIUC Compiler Optimizations
   libgmp-dev \
   # for LORE mutator in UIUC Compiler Optimizations
   gcc-8 g++-8 \
   # for PROMPT
   binutils-dev libiberty-dev \
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/*

 #tex4ht
 #texlive-latex-base texlive-latex-extra 


RUN chmod u+s /usr/bin/cpufreq-set
 

 # Used in const.sh
RUN locale-gen en_US.utf8 && update-locale

RUN python3 -m pip install --no-cache-dir sympy \
  && python3 -m pip install --no-cache-dir csvkit \
  && python3 -m pip install --no-cache-dir openpyxl \
  && python3 -m pip install --no-cache-dir et_xmlfile \
  && python3 -m pip install --no-cache-dir Cheetah3 \
  && python3 -m pip install --no-cache-dir parse \
  && python3 -m pip install --no-cache-dir pandas


# configure SSH for communication with Visual Studio 
RUN mkdir -p /var/run/sshd

RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \ 
   ssh-keygen -A 

# expose port 22 
EXPOSE 22

# Build cmake
WORKDIR /root
RUN wget -q https://github.com/Kitware/CMake/releases/download/v3.21.1/cmake-3.21.1.tar.gz \
  && tar xvf cmake-3.21.1.tar.gz
WORKDIR /root/cmake-3.21.1
RUN ./bootstrap \
  && make \
  && make install


ENV ROSE_HOME=/usr/rose
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

RUN groupadd -g 8088 builder && \
   useradd -m -d /home/builder -s /bin/bash -u 8088 -g builder -G sudo builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN echo "builder:builder" | chpasswd

RUN mkdir /share && chmod a+rwx /share && chmod +t /share


COPY sep_eng/ /opt/intel/sep_eng
USER builder
ENV USER=builder
COPY --chown=builder rose-utils/ /share/rose-utils
COPY --chown=builder ice-locus-dev/ /share/ice-locus-dev
COPY --chown=builder pocc-1.1/ /share/pocc-1.1
RUN mkdir /share/uiuc-compiler-opts
COPY --chown=builder uiuc-compiler-opts/ /share/uiuc-compiler-opts/src-git

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
RUN wget -q https://scm.cri.ensmp.fr/svn/nlpmake/trunk/makes/setup_pips.sh \
   && chmod +x setup_pips.sh \
   && ./gen_svn_servers.sh \
   && ./setup_pips.sh --dynamic --light --pyconf=python3-config


# Setting up following https://bitbucket.org/thiagotei/uiuc-compiler-opts/wiki/Home

USER builder
ENV CC=gcc-4.9
ENV CXX=g++-4.9
WORKDIR /share/pocc-1.1
RUN ./install.sh 
WORKDIR /share/pocc-1.1/analyzers/candl
RUN patch -p1 -i ../../pocc-1.1-candl-0.6.2.patch && make install

# Build UIUC Compiler Optimizations
# Ensure using new version of GCC/G++ (should be 9.3.0 for this container)
# Updated: use GCC/G++ (version 8.4.0) to ensure all tools build (incl Locus-Lore)
ENV CC=gcc-8
ENV CXX=g++-8
WORKDIR /share/uiuc-compiler-opts
# Comment out a line in CMakeLists.txt to use system boost
RUN mkdir build && mkdir install 
WORKDIR /share/uiuc-compiler-opts/build
RUN sed -i '/^set(Boost_NO_SYSTEM_PATHS ON)/ s/^/#/' ../src-git/CMakeLists.txt \
   && sed -i 's|#set(POCC_ROOT "/shared/pocc/pocc-1.1")|set(POCC_ROOT "/share/pocc-1.1")|g' ../src-git/CMakeLists.txt \
   && cmake -DROSE_PATH=/usr/rose -DCMAKE_CXX_FLAGS=-std=c++11 -DCMAKE_INSTALL_PREFIX=/share/uiuc-compiler-opts/install ../src-git \
   && make install
