# decathlon-tracker
A simple Decathlon product tracker in python. It is capable of tracking multiple products at the same time, splitting the work across multiple threads.

## Setup
decathlon-tracker requires `requests`, `beautifulsoup4` and `notify.run` packages to be installed before use.
```
pip install requests
pip install bs4
pip install notify-run
```
Afterwards, create a `products.txt` file containing the URLs to watch, one per line, in the same dir of the program.

### Push notifications
The script allows for push notifications to be sent to a channel endpoint, for mobile and browser notifications. The functionality is provided via [notify.run](https://notify.run/). Currently, setup is manual: modify the `endpoint` variable in the source code with your channel id that you obtained from the notify.run website. Remember to subscribe any device you want to receive notifications on to the channel.

If and endpoint is not provided, a warning message will be displayed in the console and an internal flag will be set not to send notifications, but the program will execute just fine.

## Usage
`Usage: decathlon-tracker.py [-h] [-p PATH] [-r RELOAD] [-t THREAD] [-o] [-l {INFO,WARN,ERROR}]`

Optional arguments:
* -h, --help  Show this help message and exit
* -p PATH, --path PATH  Path of file containing URLs of products to track. Default: ./products.txt
* -r RELOAD, --reload RELOAD  Reload interval in seconds. Default: 30
* -t THREAD, --thread THREAD  Max number of threads. Default: host logical cores
* -o, --once  Iterate the tracker loop once and exit
* -l {INFO,WARN,ERROR}, --logger {INFO,WARN,ERROR}  Specify log level. Possible values are INFO, WARN, ERROR. Default: INFO