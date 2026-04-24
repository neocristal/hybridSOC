# Naudojame oficialų Ubuntu atvaizdą
FROM ubuntu:22.04

# Išvengiame interaktyvių klausimų instaliacijos metu
ENV DEBIAN_FRONTEND=noninteractive

# Atnaujiname paketus ir įdiegiame Ansible bei reikalingus priedus
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    python3-pip \
    ssh \
    git && \
    add-apt-repository --yes --update ppa:ansible/ansible && \
    apt-get install -y ansible && \
    apt-get clean

# Nustatome darbinį katalogą
WORKDIR /ansible

# Pagal nutylėjimą paleidžiame Ansible versijos patikrą
CMD ["ansible", "--version"]