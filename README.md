# Simple Line bot

use line message api
https://developers.line.me/en/docs/messaging-api/overview/

# Get Start

## Requirement

- python-virtualenv
- python-pip


*Ubuntu*
```bash
apt install virtualenv
apt install python-pip
```

## Prepare

1. Gen config
```bash
cp config.yml.example config.yml
cp  reply.yml.example reply.yml

```

2. Update Setting
update your setting into config, and add some reply string into reply.yml
```bash
vi config.yml
vi reply.yml
```

3. Setup enviroment
```bash
virtualenv --python=python3 env
source env/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run.py
```
