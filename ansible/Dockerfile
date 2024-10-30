FROM ubuntu:24.10
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get install -y gcc python3-dev libkrb5-dev && \
  apt-get install python3-pip -y && \
  pip3 install --upgrade virtualenv --break-system-packages && \
  apt install krb5-user -y && \ 
  pip3 install --break-system-packages pywinrm[kerberos] pywinrm ansible

ADD . /ansible
WORKDIR /ansible
ENTRYPOINT [ "ansible-playbook" ]