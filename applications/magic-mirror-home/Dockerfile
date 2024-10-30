FROM karsten13/magicmirror:latest
USER root
RUN apt-get update; apt-get install -y --no-install-recommends arp-scan python3 python3-pip git
USER node
RUN pip3 install --break-system-packages pyyaml
ADD config /opt/magic_mirror/config
ADD install_modules.py .
ADD modules.yaml .
RUN python3 install_modules.py


CMD ["npm","run", "server"]
