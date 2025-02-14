FROM ubuntu:24.10
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
  apt-get install -y gcc python3-dev libkrb5-dev sshpass git openssh-client curl wget && \
  apt-get install python3-pip -y && \
  pip3 install --upgrade virtualenv --break-system-packages && \
  apt install krb5-user -y 
  
ADD requirements.txt /ansible/

WORKDIR /ansible
RUN mkdir ~/.ssh
RUN touch ~/.ssh/authorized_keys
RUN touch ~/.ssh/known_hosts
RUN chmod 700 ~/.ssh
RUN chmod 600 ~/.ssh/authorized_keys
RUN chmod 600 ~/.ssh/known_hosts


RUN   pip3 install --break-system-packages -r requirements.txt
ADD . /ansible
RUN ansible-galaxy install -r requirements.yml
ENV ANSIBLE_HOST_KEY_CHECKING=False
CMD [ "ansible-playbook", "./playbooks/site.yml"]