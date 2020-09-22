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
```

## Encrypt/Decrypt Files

``` bash
# oracle-cloud
python lation.py encrypt \
    --src secrets/instance-keys/oracle-cloud \
    --dest secrets/instance-keys/oracle-cloud.encrypted \
    --password p
python lation.py decrypt \
    --src secrets/instance-keys/oracle-cloud.encrypted \
    --dest secrets/instance-keys/oracle-cloud \
    --password p

# oracle-cloud.pub
python lation.py encrypt \
    --src secrets/instance-keys/oracle-cloud.pub \
    --dest secrets/instance-keys/oracle-cloud.pub.encrypted \
    --password p
python lation.py decrypt \
    --src secrets/instance-keys/oracle-cloud.pub.encrypted \
    --dest secrets/instance-keys/oracle-cloud.pub \
    --password p

# lation-vpn-client.ovpn
python lation.py encrypt \
    --src secrets/openvpn/lation-vpn-client.ovpn \
    --dest secrets/openvpn/lation-vpn-client.ovpn.encrypted \
    --password p
python lation.py decrypt \
    --src secrets/openvpn/lation-vpn-client.ovpn.encrypted \
    --dest secrets/openvpn/lation-vpn-client.ovpn \
    --password p
```
