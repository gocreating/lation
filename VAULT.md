This file lists common commands to encrypt/decrypt files.

## Encrypt/Decrypt Files

### oracle-cloud

``` bash
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
```

### oracle-cloud.pub

``` bash
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
```

### lation-drive.json

``` bash
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
```

### lation-cloud-dns-bot.json

``` bash
APP=base python lation.py vault \
    --password p \
    encrypt \
        --src secrets/google-api-keys/lation-cloud-dns-bot.json \
        --dest secrets/google-api-keys/lation-cloud-dns-bot.json.encrypted
APP=base python lation.py vault \
    --password p \
    decrypt \
        --src secrets/google-api-keys/lation-cloud-dns-bot.json.encrypted \
        --dest secrets/google-api-keys/lation-cloud-dns-bot.json
```

### lation-vpn-client.ovpn

``` bash
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