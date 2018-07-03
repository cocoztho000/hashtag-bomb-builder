# Auto Open

Add this python script to your linux startup and it will open the desired windows and
their positions on your screen.

Note: Only Compatable with firefox.

# Install Instructions

### Setup Virtualenv
```
virtualenv .venv
. .venv/bin/activate
```

### Install Deps
```
pip install -U -r requirments.txt
```

### Download Driver
```
wget https://github.com/mozilla/geckodriver/releases/download/v0.19.1/geckodriver-v0.19.1-linux64.tar.gz
```

### Untar driver and add it to `/usr/local/bin`
