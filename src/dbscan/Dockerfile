ARG FUNCTION_DIR="/function"

FROM --platform=linux/amd64 osgeo/gdal:ubuntu-small-3.5.1

ARG FUNCTION_DIR

COPY requirements.txt ${FUNCTION_DIR}/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r ${FUNCTION_DIR}/requirements.txt && \
    pip install --no-cache-dir pygdal=="`gdal-config --version`.*" && \
    mkdir -p ${FUNCTION_DIR} && \
    curl -Lo /usr/bin/aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie && \
    chmod +x /usr/bin/aws-lambda-rie

COPY handler.py ${FUNCTION_DIR}/
COPY entrypoint.sh /entrypoint.sh

WORKDIR ${FUNCTION_DIR}

RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "handler.handler" ]
