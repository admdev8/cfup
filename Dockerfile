FROM resin/rpi-raspbian
MAINTAINER marpie@a12d404.net

# Create the cfup directory and data link
RUN mkdir /opt/cfup && mkdir /data && ln -s /data /opt/cfup/etc

ADD cfup.py /opt/cfup/cfup.py
RUN chmod 0755 /opt/cfup.py

# Add crontab file in the cron directory
ADD crontab /etc/cron.d/cfup-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cfup-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
