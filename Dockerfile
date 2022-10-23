# syntax=docker/dockerfile:1

FROM python:3.10.8-buster

WORKDIR /flaskr

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY flaskr ./
COPY run_cron.sh ./
RUN touch run_cron.log ./
COPY cron_job_tareas/app_cron.py ./
#COPY cron_job_tareas .
RUN mkdir ../archivos_audio

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN apt-get install -y cron

RUN crontab -l | { cat; echo "* * * * * bash /flaskr/run_cron.sh >> /flaskr/run_cron.log "; } | crontab -
RUN chmod +x run_cron.sh
RUN chmod u+x run_cron.log


# Add crontab file in the cron directory
ADD run-cron /etc/cron.d/run-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/run-cron

# Apply cron job
RUN crontab /etc/cron.d/run-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the command on container startup
#CMD /etc/init.d/cron start && tail -f /var/log/cron.log
CMD ["sh","-c","/etc/init.d/cron start"]

##custom entry point — needed by cron
COPY entrypoint /entrypoint
RUN chmod +x /entrypoint
ENTRYPOINT ["/entrypoint"]

#CMD [ "cron", "-f" ]

#EXPOSE 80

#CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]