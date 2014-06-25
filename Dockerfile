FROM ubuntu:trusty
MAINTAINER George Lewis <schvin@schvin.net>
RUN apt-get update --fix-missing

RUN apt-get install -y python-pip
RUN pip install --upgrade httpie

RUN groupadd httpie
RUN useradd httpie -g httpie -d /home/httpie
RUN mkdir /home/httpie
RUN chown -R httpie:httpie /home/httpie

ENV HOME /home/httpie
USER httpie
WORKDIR /home/httpie

CMD ["--help"]
ENTRYPOINT ["/usr/local/bin/http"]
