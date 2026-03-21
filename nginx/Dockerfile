FROM nginx:alpine

RUN apk add --no-cache gettext

COPY nginx.conf.http.template /etc/nginx/templates/nginx.conf.http.template
COPY nginx.conf.https.template /etc/nginx/templates/nginx.conf.https.template
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
