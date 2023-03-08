1. Create EC2 container instance
2. install git `sudo yum update -y; sudo yum install git -y`
2. Get streamlit project
3. Fill .streamlit/secrets.toml
4. Install Python3.9 https://computingforgeeks.com/how-to-install-python-on-amazon-linux/
5. Install requirements ` pip3.9 install -r requirements.txt`
6. In cognito add redirect URL `https://<IP>` and logout URL `https://<IP>/?logout=true`
7. install nginx
    ```
    sudo amazon-linux-extras enable epel
    sudo yum install epel-release
    sudo yum install nginx
    ```
8. Add this to `/etc/nginx/conf.d/*` or to `/etc/nginx/nginx.conf` and specify `<IP>`, `<streamlit_port>` and the paths to the `.crt` and the `.key`
    ```nginx
    server {
        listen 443 ssl;
        server_name <IP>;

        ssl_certificate     <path_to_.crt>;
        ssl_certificate_key <path_to_.key>;
        ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        client_max_body_size 100M; # It allows files below 100Mb, change it based on your use

        location / {

            proxy_pass http://127.0.0.1:<streamlit_port>;

            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

    }


    server {
        listen 80;
        server_name <IP>;
        return 301 https://<IP>;
    }
    ```
    for a self signed certificate use `openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes -keyout example.key -out example.crt`
6. Activate nginx `sudo systemctl start nginx`

7. Start `streamlit run main.py --server.address=127.0.0.1`


## TODO
- Ask for permission to access MASKING_RULE_DEFINITION