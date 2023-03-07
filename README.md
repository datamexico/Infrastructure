
# Infraestructura

A continuacion se describen los pasos para instalar y configurar los servidores, estos se dividen en Backend y Frontend, dos servidores separados cuyas funciones son almacenar y disponibilizar los datos procesados, en el caso del Backend y la plataforma que es con lo que interactua el usuario que es el Frontend.

<p align=center>
<img title="Infrastructure schema" alt="Infrastructure schema" src="schema.png" width="709.5" height="456.75">
</p>

<p align=center>Imagen 1: Diagrama de infraestructura</p>

# Instalacion Backend

El servidor backend tiene las siguientes aplicaciones instaladas:
- Rust
- Python
- NodeJS, PM2
- Clickhouse
- Postgresql
- Tesseract-OLAP
- Tesseract-UI
- Geoservice
- Redis
- Nginx

## Requerimientos
Considerando que la infraestructura objetivo es Centos 7, se tienen los siguientes requerimientos:
```
# requirements
sudo yum install -y epel-release
sudo yum install -y wget nano git nginx gcc gcc-c++ kernel-devel openssl-devel yum yum-utils python3 python-pip python3-devel gdal gdal-devel
sudo yum group install -y 'Development Tools'

# node
curl -sL https://rpm.nodesource.com/setup_12.x | sudo bash -

sudo yum clean all
sudo yum install -y nodejs
```

## Rust
Rust es el lenguaje de programacion en el que esta escrito Tesseract-OLAP, se utiliza para compilar la aplicacion en el servidor, para instalar:
```
# install rust
curl https://sh.rustup.rs -sSf | sh -s -- -y

# activate current shell
source "$HOME/.cargo/env"
```

## Python
Python es el lenguaje de programacion que se utiliza para realizar ETL (extract, transform and load), existen diversas alternativas para instalar Python, pero se destaca Docker para crear el ambiente de ETL, el sitio https://docs.docker.com/engine/install/ tiene instrucciones en como instalar Docker, el repositorio [data-etl](https://github.com/datamexico/data-etl) contiene todos los scripts del ETL y dentro se encuentra el archivo Dockerfile para crear el ambiente:
```
# Docker
sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine

sudo yum install -y yum-utils

sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl start docker

# Repositorio ETL
git clone https://github.com/datamexico/data-etl && cd data-etl

# Crear ambiente
sudo docker build -t dmx-etl:latest .
```
- Solo es necesario crear el ambiente una unica vez, en sesiones posteriores solo hay que activarlo
- el archivo **.env** contiene las variables de entorno de la base de datos, deben ser reemplazadas segun el ambiente (dev, staging, prod):
```
CLICKHOUSE_URL=127.0.0.1
CLICKHOUSE_DATABASE=default
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=
PYTHONPATH=/data-etl
BASE_URL=http://localhost:7777
BACKEND_DOMAIN=api.datamexico.org
FRONTEND_DOMAIN=datamexico.org
```
- el archivo `.env` se crea dentro del repositorio del ETL `/data-etl/.env`, misma ruta desde donde se activa el ambiente de docker con el siguiente comando:
```
# Activar ambiente
sudo docker run -it --rm -p 8888:8888 --network="host" -v $(pwd):/data-etl -v /home/datamexico-data:/data-etl/etl/datamexico-data --workdir /data-etl --env-file $(pwd)/.env --name=dmx-etl dmx-etl:latest bash
```

## NodeJS, PM2

NodeJS se utiliza para compilar Tesseract-UI (explorador de datos), mientras que PM2 se utiliza para crear servicios de aplicaciones, en particular el sitio **datamexico-site** y Geoservice, particularmente se utiliza la version 12 LTS de NodeJS. NodeJS es parte de los requerimientos, PM2 se debe instalar posteriormente:
```
sudo npm install pm2@latest -g
```

## Clickhouse
Principal base de datos y destino del ETL, la version utilizada es `22.2.2.1-2`, la documentacion esta disponible en https://clickhouse.com/docs/en/home/ y los pasos para instalarla son:
```
# install
sudo yum localinstall -y https://packages.clickhouse.com/rpm/stable/clickhouse-common-static-22.2.2.1-2.x86_64.rpm
sudo yum localinstall -y https://packages.clickhouse.com/rpm/stable/clickhouse-client-22.2.2.1-2.noarch.rpm
sudo yum localinstall -y https://packages.clickhouse.com/rpm/stable/clickhouse-server-22.2.2.1-2.noarch.rpm

# start service
sudo /etc/init.d/clickhouse-server start

# enabling service on boot
sudo systemctl enable clickhouse-server
```

## Postgresql
Base de datos que contiene la logica de la plataforma y datos geograficos de Mexico (Geoservice), adicionalmente se utiliza la extension `Postgis`, los pasos para instalar Postgresql son:
```
# Install the repository RPM:
sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL:
sudo yum install -y postgresql12-server

# Optionally initialize the database and enable automatic start:
sudo /usr/pgsql-12/bin/postgresql-12-setup initdb
sudo systemctl enable postgresql-12
sudo systemctl start postgresql-12

# Postgis
sudo yum install -y postgis.x86_64 0:2.0.7-2.el7 postgis25_12
```

## Tesseract-OLAP
Tesseract-OLAP es la aplicacion que permite hacer consultas a la base de datos, requiere tener **Rust** instalado y el archivo `schema.xml` que se encuentra en el repositorio **datamexico-tesseract**, las instrucciones para compilar la aplicacion son las siguientes:

```
# clone repo
git clone https://github.com/tesseract-olap/tesseract && cd tesseract

# build
cargo build --release

# symbolic link to bin directory
cd /usr/bin && sudo ln -s /absolute/path/tesseract/target/release/tesseract-olap tesseract-olap
```

## Tesseract-UI
Explorador de datos, requiere que Tesseract-OLAP se encuentre funcionando, a modo de ejemplo se utiliza https://api.datamexico.org/tesseract/, la instalacion se realiza con el siguiente comando:
```
npm init @datawheel/tesseract-ui explorer-ui
✔ Enter the full URL for the OLAP server … https://api.datamexico.org/tesseract/
✔ Where will this instance run? › A production server
✔ What locales is the server configured to use? Comma-separated, first will be the default … es,en
Creating a new tesseract-ui instance
Target directory: /absolute/path/explorer-ui
```

## Geoservice
Geoservice es una aplicacion que permite hacer consultas geograficas, por ejemplo conocer los vecinos del estado X, requiere de postgres para almacenar los datos y NodeJS para compilar, para instalarlo se tiene:
```
git clone https://github.com/Datawheel/geoservice-api && cd geoservice-api
git checkout datamexico-refactor
npm i
npm run build
```

## Redis
Redis es utilizado por Tesseract-OLAP como cache para las queries generadas, documentacion https://redis.io/docs/, instalacion:
```
sudo yum install -y redis
sudo systemctl start redis
sudo systemctl enable redis
```
La unica configuracion requerdia es `maxmemory 10737418240`:
```
> sudo nano /etc/redis.conf
maxmemory 10737418240
```
Reiniciar luego actualizar el archivo de configuracion `sudo service redis restart`

## Nginx
Servicio que expone las aplicaciones internas del servidor, Tesseract-OLAP, Tesseract-UI y datamexico-site, tambien se utiliza como **cache** reduciendo el tiempo de respuesta de la plataforma, la instalacion es parte de los requerimientos, pero es necesario inicializar el servicio:
```
sudo service nginx start
sudo systemctl enable nginx
```

# Configuracion Backend

## Clickhouse
- Generar contraseña: [documentacion](https://github.com/ClickHouse/ClickHouse/blob/master/programs/server/users.xml#L47), donde la variable de entorno `CLICKHOUSE_PASSWORD` es el primer resultado y `sha256` es el segundo que debe ser almacenado en `users.xml`:
```
PASSWORD=$(base64 < /dev/urandom | head -c8); echo "$PASSWORD"; echo -n "$PASSWORD" | sha256sum | tr -d '-'
Lybgow8C
621b666a24d928b2d40d418315c367e6320a4702179beaf4f97b3c9f89313d2e
```
- Agregar usuarios: dentro de `<users>` tag, [documentation](https://github.com/ClickHouse/ClickHouse/blob/master/programs/server/users.xml#L17), mismo usuario que se utiliza en `CLICKHOUSE_USERNAME`:
```
sudo nano /etc/clickhouse-server/users.xml

    <users>
        <!-- ETL user -->
        <etl>
            <password_sha256_hex>621b666a24d928b2d40d418315c367e6320a4702179beaf4f97b3c9f89313d2e</password_sha256_hex>

            <!-- To open access from everywhere, specify: -->
            <networks incl="networks" replace="replace">
                <ip>::/0</ip>
            </networks>
            <!-- To open access from ip, specify: 
                <ip>213.180.204.3</ip>
            -->

            <!-- To open access only from localhost, specify: 
                <ip>::1</ip>
                <ip>127.0.0.1</ip>
            -->

            <profile>default</profile>

            <quota>default</quota>

        </etl>

        <!-- Tesseract-OLAP user -->
        <readonly>

            <password></password>
    
            <networks incl="networks" replace="replace">
                <ip>::/0</ip>
            </networks>

            <profile>readonly</profile>

            <quota>default</quota>
        </readonly>
    </users>
```

- Backups: para crear backups en el disco local se utilizan los siguientes comandos, en caso de requerir mas opciones se tiene la [documentacion](https://clickhouse.com/docs/en/interfaces/cli/#command-line-options):
```
# create table backup
clickhouse-client --database=default --user=default --query="SELECT * FROM table_name FORMAT Native" > table_name.native
clickhouse-client --database=default --user=default --query="SHOW CREATE TABLE table_name" --format=TabSeparatedRaw > table_name.sql

# restore table
clickhouse-client < table_name.sql
clickhouse-client --query="INSERT INTO table_name FORMAT Native" < table_name.native
```

- Conexiones externas: para permitir conexiones externas a clickhouse (servicio en el puerto 9000) se debe editar el archivo `/etc/clickhouse-server/config.xml`, documentacion adicional se puede encontrar [aqui](https://github.com/ClickHouse/ClickHouse/blob/master/programs/server/config.xml#L198):
```
sudo nano /etc/clickhouse-server/config.xml

<clickhouse>
    <listen_host>::</listen_host>

    ...

</clickhouse>
```
- Recalcar que cualquier modificacion a los archivos de configuracion requiere reiniciar el servicio de `clickhouse-server`:
```
sudo service clickhouse-server restart
```

## Postgres
La configuracion de postgresql consiste en la creacion de un usuario, 2 bases de datos y permitir conexiones externas en el puerto `5432`, requerido por la plataforma:

```
# Create user
sudo -u postgres psql -c "CREATE USER <user-name> WITH LOGIN SUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION ENCRYPTED PASSWORD '<password>'"

# PG Config
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /var/lib/pgsql/12/data/postgresql.conf
sudo sed -i "s/#port = 5432/port = 5432/" /var/lib/pgsql/12/data/postgresql.conf

# PG External Connection
sudo su - postgres -c "echo 'host    mexico_cms      <user-name>           0.0.0.0/0               md5' >> /var/lib/pgsql/12/data/pg_hba.conf"
sudo su - postgres -c "echo 'host    mexico_shapes   <user-name>           ::/0                    md5' >> /var/lib/pgsql/12/data/pg_hba.conf"

# Restart
sudo service postgresql-12 restart
```

## Tesseract-OLAP
- Creacion de servicio en la ruta `sudo nano /etc/systemd/system/tesseract-olap.service`, es necesario reemplazar `TESSERACT_SCHEMA_FILEPATH`, `TESSERACT_LOGIC_LAYER_CONFIG_FILEPATH`, con el contenido del repositorio [datamexico-tesseract](https://github.com/datamexico/datamexico-tesseract) y modificar los secretos `<secret>`:
```
[Unit]
Description=Tesseract OLAP server for DataMexico
After=network.target
Wants=clickhouse-server.service
After=clickhouse-server.service

[Service]
User=root
Group=root
Type=simple
RemainAfterExit=yes
Environment=RUST_LOG=info
Environment="TESSERACT_DATABASE_URL=clickhouse://readonly:@127.0.0.1:9000/default?pool_max=150&keepalive=300s"
Environment=TESSERACT_SCHEMA_FILEPATH=/absolute/path/datamexico-tesseract/schema.xml
Environment=TESSERACT_FLUSH_SECRET=<secret>
Environment="TESSERACT_DEBUG=true"
Environment="TESSERACT_GEOSERVICE_URL=http://<backend-ip>/geoservice/"
Environment="TESSERACT_LOGIC_LAYER_CONFIG_FILEPATH=/absolute/path/datamexico-tesseract/logic-layer-config.json"
Environment="TESSERACT_JWT_SECRET=<secret>"
Environment="TESSERACT_REDIS_URL=redis://localhost:6379"
ExecStart=/usr/bin/tesseract-olap --debug -a 0.0.0.0:7777
TimeoutSec=5000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
- Habilitar el servicio en el inicio del sistema
```
sudo systemctl enable tesseract-olap.service
```

## Tesseract-UI
Una vez instalado la aplicacion necesita ser expuesta por Nginx, dentro de `/etc/nginx/conf.d/backend.conf` existe un bloque `location` que requiere de la ruta donde se instalo Tesseract-UI `/explorer-ui/dist`. La ruta `/absolute/path/public_html/ui` es un link simbólico de `/home/<user>/explorer-ui/dist`, suponiendo que estamos en la carpeta `public_html`, entonces: `ln -s /home/<user>/explorer-ui/dist ui`
```
  location /ui {
    alias      /absolute/path/public_html/ui;
    try_files  $uri $uri/ /index.html;
  }
```

## Nginx
Es necesario modificar las lineas donde exista `/absolute/path` y crear los directorios de ser necesario, luego copiar la configuracion `/config/backend.conf` hacia `/etc/nginx/conf.d/backend.conf` y reiniciar el servicio:
```
sudo nginx -t
sudo service nginx restart
```

## Restaurar Bases de datos - Postgres
```
# Create user
sudo -u postgres psql -c "CREATE USER <pg-user> WITH LOGIN SUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION ENCRYPTED PASSWORD '<pg-password>'"

# Create tables
sudo -u postgres psql <<EOF
CREATE DATABASE mexico_cms OWNER <pg-user> TABLESPACE pg_default;
CREATE DATABASE mexico_shapes OWNER <pg-user> TABLESPACE pg_default;
EOF

# Restore DB
sudo su - postgres -c "psql -d mexico_cms -f /tmp/mexico_cms.sql"
sudo su - postgres -c "psql -d mexico_shapes -f /tmp/mexico_shapes.sql"
```

## Restaurar Bases de datos - Clickhouse
Dentro del archivo comprimido de backup existen 2 scripts para realizar operaciones de backup, `create.sh` y `restore.sh`, solo es necesario utilizar los scripts para realizar dichas operaciones backups. Actualmente el backup pesa 81 GB, por lo que se debe considerar el espacio disponible antes de descomprimir:
```
bash create.sh
bash restore.sh
```

## Geoservice
- Geoservice requiere de dos archivos de configuracion `ecosystem.config.js` que contiene la conexion a la base de datos:
```
module.exports =  {
    apps : [{
      name   : "Geoservice",
      script : "./dist/index.js",
      env: {
	      NODE_ENV: "production",
        GSA_DB_NAME: "mexico_shapes",
        GSA_DB_PW: "<postgres-db-password>",
        GSA_DB_USER: "<postgres-db-user>",
        GSA_DB_HOST: "<api-domain>",
        GSA_DB_PORT: "5432",
        GSA_USER_CONFIG_FILE: "/absolute/path/geoservice-api/mexico_levels.json",
        PORT: 8080
      }
    }]
  }
```
- y `mexico_levels.json` que contiene el esquema de la base de datos, es necesario que ambos arhivos esten en la carpeta principal del repositorio `geoservice-api`
```
{
    "shapes": {
        "nation": {"schema": "public", "table": "inegi_geo_nat", "idColumn": "nat_id", "nameColumn": "nat_id"},
        "entity": {"schema": "public", "table": "inegi_geo_ent", "idColumn": "ent_id", "parent": ["nation"], "nameColumn": "ent_id"},
        "municipality": {"schema": "public", "table": "inegi_geo_mun", "idColumn": "mun_id", "parent": ["entity"], "nameColumn": "mun_id"}
    },
    "idMapping" : {
        "entity": {"maxLength": 2},
        "nation": {"maxLength": 3},
        "municipality": {"maxLength": 5}
    }
}
```
- con ambos archivos y la base de datos restaurada en postgres se inicia la aplicacion:
```
# start service
pm2 start ecosystem.config.js

# check status
pm2 list
```

# Instalacion Frontend

El servidor frontend tiene las siguientes aplicaciones instaladas:
- Python (Canon-Stats)
- NodeJS, PM2
- Nginx

```
# requirements
sudo yum install -y epel-release python3 python-pip python3-devel

# node
curl -sL https://rpm.nodesource.com/setup_12.x | sudo bash -

sudo yum clean all
sudo yum install -y gcc-c++ make
sudo yum install -y nodejs git nano nginx

# pm2
sudo npm install pm2@latest -g
```

# Configuracion Frontend

## FDI pipelines
Los datos del FDI estan anonimizados, pero se entregan datos agregados al cliente, los archivos `*.json` se crean en el ETL y deben ser movidos al directorio `datamexico-site/static/api/`, los archivos son los siguientes y los pasos para crearlos son https://github.com/datamexico/data-etl/tree/master/etl/foreign_direct_investment:
```
- accumulated_value.json
- country_ent.json
- geo_investment_type.json
- investment_type.json
- top3_country.json
- top3_country_nation.json
- top3_ent.json
- top3_ent_country.json
- top3_investment_country.json
```

## Python (Canon-Stats)
dentro del repositorio `datamexico-site/` instalar los requerimientos:
```
git clone https://github.com/datamexico/datamexico-site && cd datamexico-site
sudo pip3 install requests
sudo pip3 install -r requirements.txt
git config --global url."https://a164d0033398f6a1db0be16428b955e83b16b48b:x-oauth-basic@github.com/".insteadOf https://x-oauth-basic@github.com/
```

## Ecosystem
- crear el archivo `ecosystem.config.js` dentro del repositorio `datamexico-site/` con la siguiente configuracion:
```
module.exports = {
  apps: [
    {
       name: "datamexico-site",
      script: "./index.js",
      cwd: "/absolute/path/datamexico-site/",
      watch: false,
      wait_ready: true,
      listen_timeout: 300000,
      max_memory_restart: "700M",
      instances: "max",
      exec_mode: "cluster",
      env: {
        NODE_ENV: "deployment",
        CANON_API: "https://<frontend-domain>",
        CANON_STATS_API: "https://<api-domain>/tesseract",
        CANON_STATS_LOGGING: "true",
        CANON_CONST_BASE: "https://<api-domain>/tesseract/",
        CANON_CONST_PROFILE_COMPARISON: true,
        CANON_LANGUAGES: "en,es",
        CANON_LANGUAGE_DEFAULT: "es",
        CANON_LOGINS: "true",
        CANON_CMS_CUBES: "https://<api-domain>/tesseract/",
        CANON_CMS_LOGGING: "true",
        CANON_CMS_ENABLE: true,
        CANON_CMS_GENERATOR_TIMEOUT: 300000,
        CANON_DB_USER: "<postgres-db-user>",
        CANON_DB_PW: "<postgres-db-password>",
        CANON_DB_NAME: "mexico_cms",
        CANON_DB_HOST: "<api-domain>",
	CANON_CONST_STORAGE_BUCKET: "local",
        //CANON_GOOGLE_ANALYTICS: "",
        CANON_CMS_REQUESTS_PER_SECOND: 60
      }
    }
  ]
};
```
- reemplazar con ips/dominios/path/credenciales dentro de `ecosystem.config.js`:
```
- cwd: "/absolute/path/datamexico-site/"
- <frontend-domain>
- <api-domain>
- <postgres-db-user>
- <postgres-db-password>
```
- inicializar la aplicacion:
```
bash init.sh develop
```

## Nginx
La ultima configuracion corresponde a Nginx, es necesario modificar las lineas donde exista `/absolute/path`, luego copiar la configuracion `/config/frontend.conf` hacia `/etc/nginx/conf.d/frontend.conf` y reiniciar el servicio:
```
sudo nginx -t
sudo service nginx restart
```

# Configuracion adicional

Configuracion adicional para permitir Nginx en el firewall, leer archivos estaticos del sitio `datamexico-site` y permitir conexiones externas en postgres:
```
# Allow external connections Nginx
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo yum install -y policycoreutils libselinux selinux-policy
sudo setsebool -P httpd_can_network_connect 1

# Read static files datamexico-site
sudo setsebool -P httpd_enable_homedirs 1
sudo setsebool -P httpd_read_user_content 1

# Postgres external connection
sudo iptables -A IN_public_allow -p tcp -m tcp --dport 5432 -m conntrack --ctstate NEW -j ACCEPT

# Clickhouse external connection
sudo iptables -A IN_public_allow -p tcp -m tcp --dport 9000 -m conntrack --ctstate NEW -j ACCEPT
```

# Troubleshooting
- La aplicacion tiene dependencia de recursos por lo que el Frontend no se ejecutara si la API no se encuentra activa y esta tampoco funcionara si la base de datos no se encuentra activa, con todos los cubos de datos y datos en esos cubos. En orden seria:
1. para el frontend: `pm2 logs`
2. backend: `sudo journalctl -u tesseract-datamexico.service -f -n 200`
3. backend: `sudo service clickhouse-server status`

## Clickhouse
- service: `sudo service clickhouse-server restart/start/stop/status`
- service file: `/etc/systemd/system/clickhouse-server.service`
- config: `/etc/clickhouse-server/config.xml` o `/etc/clickhouse-server/config.d/*.xml`
- users: `/etc/clickhouse-server/users.xml` o `/etc/clickhouse-server/users.d/*.xml`
- logs: `/var/log/clickhouse-server/clickhouse-server.err.log`
- check: `clickhouse-client`
- docs: https://clickhouse.com/docs/en/home/

## Tesseract
- service: `sudo service tesseract-datamexico restart/start/stop/status`
- service file: `/etc/systemd/system/tesseract-datamexico.service`
- logs: `sudo journalctl -u tesseract-datamexico.service -f -n 200`
- check: `curl localhost:7777`

## Postgres
- service: `sudo service postgresql restart/start/stop/status`
- config file: `/var/lib/pgsql/12/data/postgresql.conf` y `/var/lib/pgsql/12/data/pg_hba.conf`

## Frontend
- service: `pm2 status`
- config file: `datamexico-site/ecosystem.config.js`

# Notas

- Actualemente se ejecutan cronjobs los cuales pueden encontrarse en el directorio `cronjobs/` de este repositorio
