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

``` bash
# for ubuntu, following are required to install
sudo apt-get install -y zlib1g-dev openssl libssl-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev
sudo apt-get install -y libpq-dev # for postgres
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

## Encrypt/Decrypt Files

``` bash
# oracle-cloud
APP=base python lation.py vault \
    --password p \
    encrypt \
        --src secrets/instance-keys/oracle-cloud \
        --dest secrets/instance-keys/oracle-cloud.encrypted
APP=base python lation.py vault \
    --password p \
    decrypt \
        --src secrets/instance-keys/oracle-cloud.encrypted \
        --dest secrets/instance-keys/oracle-cloud

# oracle-cloud.pub
APP=base python lation.py vault \
    --password p \
    encrypt \
        --src secrets/instance-keys/oracle-cloud.pub \
        --dest secrets/instance-keys/oracle-cloud.pub.encrypted
APP=base python lation.py vault \
    --password p \
    decrypt \
        --src secrets/instance-keys/oracle-cloud.pub.encrypted \
        --dest secrets/instance-keys/oracle-cloud.pub

# lation-drive.json
APP=base python lation.py vault \
    --password p \
    encrypt \
        --src secrets/google-api-keys/lation-drive.json \
        --dest secrets/google-api-keys/lation-drive.json.encrypted
APP=base python lation.py vault \
    --password p \
    decrypt \
        --src secrets/google-api-keys/lation-drive.json.encrypted \
        --dest secrets/google-api-keys/lation-drive.json

# lation-vpn-client.ovpn
APP=base python lation.py vault \
    --password p \
    encrypt \
        --src secrets/openvpn/lation-vpn-client.ovpn \
        --dest secrets/openvpn/lation-vpn-client.ovpn.encrypted
APP=base python lation.py vault \
    --password p \
    decrypt \
        --src secrets/openvpn/lation-vpn-client.ovpn.encrypted \
        --dest secrets/openvpn/lation-vpn-client.ovpn
```

## Connect to Instance

``` bash
chmod 400 ./secrets/instance-keys/oracle-cloud
ssh -i ./secrets/instance-keys/oracle-cloud ubuntu@lation-1.combo.live
ssh -i ./secrets/instance-keys/oracle-cloud ubuntu@lation-2.combo.live
```

## Postgres Sequence Issue when id exists

- <https://stackoverflow.com/a/40281835/2443984>
- <https://stackoverflow.com/a/37972960/2443984>
