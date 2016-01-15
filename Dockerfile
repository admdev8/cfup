FROM resin/rpi-raspbian
MAINTAINER marpie@a12d404.net

# Install required applications
RUN apt-get update && apt-get install -y \
    ca-certificates \
    cron \
    python \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Create the cfup directory and data link
RUN mkdir /opt/cfup && mkdir /data && ln -s /data /opt/cfup/etc

ADD cfup.py /opt/cfup/cfup.py
RUN chmod 0755 /opt/cfup/cfup.py

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Add job to cron
RUN echo "*/5 * * * * /opt/cfup/cfup.py update-entries >> /var/log/cron.log 2>&1" >> /etc/crontab && echo "" >> /etc/crontab

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
