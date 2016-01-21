FROM resin/rpi-raspbian
MAINTAINER marpie@a12d404.net

# Install required applications
RUN apt-get update && apt-get install -y \
    ca-certificates \
    python \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Create the cfup directory and data link
RUN mkdir /opt/cfup && mkdir /data && ln -s /data /opt/cfup/etc

ADD cfup.py /opt/cfup/cfup.py
RUN chmod 0755 /opt/cfup/cfup.py

# Add job to cron
RUN \
    echo -e "#!/bin/sh\ntouch /var/log/cfup.log\nwhile true; do /opt/cfup/cfup.py update-entries &> /var/log/cfup.log; sleep 5m; done" > /opt/cfup/start.sh && \
    echo 0755 /opt/cfup/start.sh

# Run the command on container startup
CMD /opt/cfup/start.sh && tail -f /var/log/cfup.log
