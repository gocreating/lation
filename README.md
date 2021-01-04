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

## Connect to Instance

``` bash
chmod 400 ./secrets/instance-keys/oracle-cloud
ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@dev.lation.app
ssh -o StrictHostKeyChecking=no -i ./secrets/instance-keys/oracle-cloud ubuntu@prod.lation.app
```

## Postgres Sequence Issue when id exists

- <https://stackoverflow.com/a/40281835/2443984>
- <https://stackoverflow.com/a/37972960/2443984>
