# Lation

## Setup Editor

Install `Remote - WSL` extension (so you can connect to WSL in windows)
Install `Python` extension (so you can select interpreter)

## Setup Environments

``` bash
# install pyenv
curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
```

Add following to `~/.bashrc`

```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Add following to `~/.zshrc`

```
export PYENV_VIRTUALENV_DISABLE_PROMPT=1
```

Install python:

``` bash
# for ubuntu, following are required to install
sudo apt-get install -y zlib1g-dev openssl libssl-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev build-essential
pyenv install 3.8.5
```

``` bash
# make default python to 3.8.5 and pip to pip3
pyenv global 3.8.5

# virtualenv
sudo apt install python3-venv
pyenv virtualenv lation

# activate venv
pyenv activate lation

# delete venv
# pyenv virtualenv-delete lation

# install required modules
pip3 install -r lation/requirements.txt
# pip freeze | xargs pip uninstall -y
```

## Launch Services in Local

``` sh
docker-compose -f ./deploy/stock/docker-compose.local.yml up
docker-compose -f ./deploy/coin/docker-compose.local.yml up
docker-compose -f ./deploy/spot_perp_bot/docker-compose.local.yml up
```

## Connect to Instance

``` bash
chmod 400 ./secrets/instance-keys/oracle-cloud
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-1.lation.app
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-2.lation.app
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-3.lation.app
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-4.lation.app
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-5.lation.app
sudo ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@instance-6.lation.app
```

## Debug Container

``` bash
$ winpty docker exec -it <container_id> bash # for windows
$ sudo docker exec spot_perp_bot_web_server_for_myself_1 bash -c 'cat "logs/$(ls logs | tail -n 1)"'
root@<container_id>:/app# cat deploy/logs/access.log
root@<container_id>:/app# cat deploy/logs/error.log
root@<container_id>:/app# cat "logs/$(ls logs | tail -n 1)"
```

## Postgres Sequence Issue when id exists

- <https://stackoverflow.com/a/40281835/2443984>
- <https://stackoverflow.com/a/37972960/2443984>

文字雲:
https://s12121296.wordpress.com/2020/03/29/python-ptt%E7%9C%8B%E6%9D%BF%E7%95%99%E8%A8%80%E7%88%AC%E8%9F%B2-%E4%B8%A6%E4%BE%9D%E6%93%9A%E5%AD%97%E8%A9%9E%E9%A0%BB%E7%8E%87%E8%A3%BD%E4%BD%9C%E6%88%90%E6%96%87%E5%AD%97%E9%9B%B2word-clode/
