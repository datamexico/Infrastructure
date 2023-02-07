
# Custom foreign trade endpoint
## Overview
Transforma la respuesta de tesseract para quitar el valor no anonimizado:
```
{
    data: [
        {
            Year: 2018,
            Trade Value: 4665524636828
        },
        {
            Year: 2019,
            Trade Value: 4714364874509
        },
        {
            Year: 2020,
            Trade Value: 4124755857969
        }
    ],
    source: [
        {
            name: "economy_foreign_trade_ent",
            measures: [
                "Trade Value",
                "Number of Firms"
            ],
            annotations: {
                subtopic: "Foreign Trade",
                source_name: "Secretaría de Economía",
                topic: "Economy",
                source_name_en: "Secretary of Economy",
                source_link: "https://www.gob.mx/se"
                }
        }
    ]
}
```

Respuesta:
```
{
    data: [
        {
            Year: 2018
        },
        {
            Year: 2019
        },
        {
            Year: 2020
        }
    ],
    source: [
        {
            name: "economy_foreign_trade_ent",
            measures: [
                "Trade Value",
                "Number of Firms"
            ],
            annotations: {
                subtopic: "Foreign Trade",
                source_name: "Secretaría de Economía",
                topic: "Economy",
                source_name_en: "Secretary of Economy",
                source_link: "https://www.gob.mx/se"
                }
        }
    ]
}
```

## Como utilizar

1. Crea el servicio `custom-foreign-trade.service` en `/etc/systemd/system/`, hay un ejemplo en el repositorio, es necesario cambiar `/absolute/path`
2. Crea el ambiente de python: `source init.sh`
3. Configuracion de Nginx:
```
location /tesseract/custom/ {
    proxy_pass http://127.0.0.1:5000;

    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header X-Cache-Status $upstream_cache_status;
  }
```
4. Inicia el servicio: `sudo service custom-foreign-trade start`
5. Habilita el servicio en el inicio: `sudo systemctl enable custom-foreign-trade`
