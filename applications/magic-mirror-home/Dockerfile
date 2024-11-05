FROM registry.gitlab.com/khassel/magicmirror:v2.24.0
USER root
RUN apt-get update; apt-get install -y --no-install-recommends arp-scan python3 python3-pip git
RUN pip3 install pyyaml
COPY config /opt/magic_mirror/config
ADD install_modules.py .
ADD modules.yaml .
RUN python3 install_modules.py
RUN chown -R node:node /opt/magic_mirror/config


CMD ["npm","run", "server"]
