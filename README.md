# A simple chatbot

This is simple chatbot framework, but current only supported line with message api.
If you have any idea, please let me know.

# Support Inteface

- LINE (Base on LINE Message Api, https://developers.line.me/en/docs/messaging-api/overview/)

# Quick Start

## Requirement

- SQLite
- python-virtualenv
- python-pip

*Ubuntu*
```bash
apt install virtualenv
apt install python-pip
```

## Prepare

1. Generate config
```bash
cp config.yml.example config.yml
cp reply.yml.example reply.yml
```

2. Update Setting
Update your setting into config, and add some reply string into reply.yml
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

# Configure

## config.yml

we will check this file to generate chat api interface

### download_path
the image default donwload path

### interface

#### line

```yaml
interface:
    lineV2:
        config:
            channel_access_token: 'this is channel access token'
        url: '/callback_url'
        # admin:
        #     - 'admin line id'
```

## reply.yml

All of response table. We check this table to generate the response table.

### help
the defaule keyword of help string

### ldx
if bot didn't knew how to response, we will random choose one

### pattern
a pattern table, we check the request string and match it. 
