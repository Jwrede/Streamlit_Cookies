1. Create EC2 container instance
2. Get streamlit project
3. Fill .env and .streamlit/secrets.toml
4. install nginx
5. add this to `/etc/nginx/conf.d/*` or to `/etc/nginx/nginx.conf` 
    ```
    server {
        listen 443 ssl;
        server_name 18.192.197.22;

        ssl_certificate     <path_to_.crt>;
        ssl_certificate_key <path_to_.key>;
        ssl_protocols       TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        client_max_body_size 100M; # It allows files below 100Mb, change it based on your use

        location / {

            proxy_pass http://ws-backend;

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
        server_name 18.192.197.22;
        return 301 https://18.192.197.22;
    }
    ```
6. Install Python3.9 https://computingforgeeks.com/how-to-install-python-on-amazon-linux/
7. Create venv and install requirements
8. "/venv/lib/python3.9/site-packages/streamlit_cookies_manager/cookie_manager.py" change 
    ```python
        def save(self):
        if self._queue:
            self._run_component(save_only=True, key="CookieManager.sync_cookies.save")
    ```
    to
    ```python
        def save(self):
        if self._queue:
            import random
            self._run_component(save_only=True, key="CookieManager.sync_cookies.save" + str(random.random()))
    ```
9. Start `streamlit run app.py --server.address=127.0.0.1`
10. 