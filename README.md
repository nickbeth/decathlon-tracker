# decathlon-tracker
A simple Decathlon product tracker in python. It is capable of tracking the availability of multiple products, but **it does not auto-buy them**!

## Setup
decathlon-tracker requires `requests`, `beautifulsoup4` and `notify.run` modules to be installed before use.
```
pip install requests
pip install bs4
pip install notify-run
```
Afterwards, create a `products.txt` file containing the URLs to watch, one per line, in the same dir of the program.

### Push notifications
The script allows for push notifications to be sent to a channel endpoint, for mobile and browser notifications. The functionality is provided via [notify.run](https://notify.run/). Currently, setup is manual: modify the `endpoint` variable in the source code with your channel id that you obtained from the notify.run website. Remember to subscribe any device you want to receive notifications on to the channel.

If and endpoint is not provided, a warning message will be displayed in the console and an internal flag will be set not to send notifications, but the program will execute just fine and only print to the console.

## Usage
`Usage: decathlon-tracker.py [-h] [-p PATH] [-r RELOAD] [-o] [-l {INFO,WARN,ERROR}]`

Optional arguments:
* -h, --help  Show this help message and exit
* -p PATH, --path PATH  Path of file containing URLs of products to track. Default: ./products.txt
* -r RELOAD, --reload RELOAD  Reload interval in seconds. Default: 30
* -o, --once  Iterate the tracker loop once and exit
* -l {INFO,WARN,ERROR}, --logger {INFO,WARN,ERROR}  Specify log level. Possible values are INFO, WARN, ERROR. Default: INFO