import argparse
import threading, sys, os, signal
from datetime import datetime
import requests, bs4
from notify_run import Notify

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"}

def get_thread_count():
    if sys.platform == "win32":
        return (int)(os.environ["NUMBER_OF_PROCESSORS"])
    else:
        return (int)(os.popen("grep -c cores /proc/cpuinfo").read())

def SIGSTOP(signal=None, frame=None):
    log.info("Closing threads and exiting...")
    stop_event.set()

def parse_file(filepath):
    try:
        f = open(filepath, mode="r")
    except:
        log.error(f"Could not open '{filepath}', exiting.")
        sys.exit(1)
    
    # Look for '#' in front of URLs. Equivalent to commenting, line will be discarded
    url_list = [line.strip() for line in f if line.strip()[0] != "#"]
    f.close()
    
    return url_list

class Log:
    LOG_LEVEL_INFO  = 0
    LOG_LEVEL_WARN  = 1
    LOG_LEVEL_ERROR = 2
    
    def __init__(self, log_level):
        self._str_log_level = log_level
        if log_level == "INFO":
            self._log_level = 0
        if log_level == "WARN":
            self._log_level = 1
        if log_level == "ERROR":
            self._log_level = 2
    
    @property
    def log_level(self):
        return self._log_level
    
    @property
    def get_log_level(self):
        return self._log_level
    
    @property
    def get_str_log_level(self):
        return self._str_log_level
    
    def info(self, message):
        if self._log_level <= self.LOG_LEVEL_INFO:
            print(f"[INFO] {message}")
    
    def warn(self, message):
        if self._log_level <= self.LOG_LEVEL_WARN:
            print(f"[WARNING] {message}")
    
    def error(self, message):
        if self._log_level <= self.LOG_LEVEL_ERROR:
            print(f"[ERROR] {message}")

class Product:
    send_push_notifications = True

    def __init__(self, item_url):
        self._url = item_url
        self.notify_available = False
        self.notify_limited = False
        self._available = 0
        
        if not self._fetch_page():
            self._status = "ERROR!"
            self._name = ""
        else:
            self._status = "OK!"
            self._name = self._fetch_name()
    
    @property
    def name(self):
        return self._name
    
    @property
    def url(self):
        return self._url
    
    @property
    def available(self):
        return self._available
    
    def __repr__(self):
        return(f"Url:                   {self._url}\
               \nProduct name:          {self._name}\
               \nThread:                {threading.current_thread().name}:{threading.get_ident()}\
               \nStatus:                {self._status}\
               \nNotify:                ({self.notify_available},{self.notify_limited})")
    
    def __str__(self):
        return(f"[{threading.current_thread().name}]\
               \nProduct name:          {self._name}\
               \nStatus:                {self._status}")
    
    def _fetch_page(self):
        try:
            raw_html = requests.get(self._url, HEADERS)
        except:
            return None
        
        product_page = bs4.BeautifulSoup(raw_html.text, "html.parser")
        return product_page
    
    def _fetch_name(self):
        return self._fetch_page().select(".product-title-right")[0].get_text()
    
    # 0=not available  1=available  2=limited  -1=error
    def is_available(self):
        page = self._fetch_page()
        
        if not page:
            self._available = -1
            return
        
        target = page.select(".info-green")
        
        if len(target):
            if target[0].getText() == "Disponibile":
                self._available = 1
        else:
            target = page.select(".info-orange")
            if len(target):
                self._available = 2
            self._available = 0
        return

def track_product(product):
    currentDate = datetime.now().strftime("%H:%M:%S")
    product.is_available()
    
    if product.available == 1:
        print(f"[{currentDate}] {product.name} is available")
        if Product.send_push_notifications and not product.notify_available:
            notify.send(f"{product.name} è disponibile su decathlon.it!")
            product.notify_available = True
            log.info("Available notification sent")
    elif product.available == 2:
        print(f"[{currentDate}] {product.name} is available in limited quantities")
        if Product.send_push_notifications and not product.notify_limited:
            notify.send(f"[Limitato] {product.name} è disponibile su decathlon.it!")
            product.notify_limited = True
            log.info("Limited quantity notification sent")
    elif product.available == 0:
        print(f"[{currentDate}] {product.name} is not available")
        if Product.send_push_notifications and (product.notify_available or product.notify_limited):
            notify.send(f"[Esaurito] {product.name} non è più disponibile!")
            product.notify_available = False
            product.notify_limited = False
            log.info("Notification status reset")
    elif product.available == -1:
        log.error("Could not load webpage: 'returned empty page'")

def tracker_thread(item_url, reload_interval, run_once):
    product = Product(item_url)
    print(product)
    
    # tracker loop
    while not stop_event.is_set():
        track_product(product)
        if run_once:
            SIGSTOP()
        stop_event.wait(reload_interval)
    
    log.info(f"{threading.current_thread().name} closed.")
    return

def main(path, reload_interval, run_once, thread_count):
    product_URLs = parse_file(path)
    log.info(f"N. of items: {len(product_URLs)}")
    
    # Register stop signal handlers (unix only)
    if sys.platform != "win32":
        for sig in ("TERM", "HUP", "INT"):
            signal.signal(getattr(signal, "SIG" + sig), SIGSTOP)
    
    # Start threads
    threads = []
    for url in product_URLs:
        t = threading.Thread(target=tracker_thread, args=(url, reload_interval, run_once,))
        threads.append(t)
        t.start()
    
    # Signals are better (non-polling), but only work on unix systems.
    # A workaround is needed for windows (poll every 5 seconds).
    if sys.platform == "win32":
        while not stop_event.is_set():
            try:
                stop_event.wait(1)
            except KeyboardInterrupt:
                SIGSTOP()
    else:
        signal.pause()
    
    # Cleanup before exit: join threads
    [t.join() for t in threads if t is not None and t.is_alive()]
    log.info("Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decathlon Bot. Gets URLs from a file and tracks them multithreaded.")
    
    # Pass arguments to the program - default config
    parser.add_argument("-p", "--path", default="products.txt", type=str, help="Path of file containing URLs of products to track. Default: products.txt")
    parser.add_argument("-r", "--reload", default=30, type=int, help="Reload interval in seconds. Default: 30")
    parser.add_argument("-t", "--thread", default=get_thread_count(), type=int, help="Max number of threads. Default: host logical cores")
    parser.add_argument("-o", "--once", action="store_const", const=True, help="Iterate the tracker loop once.")
    parser.add_argument("-l", "--logger", default="INFO", type=str, choices={"INFO", "WARN", "ERROR"},
                            help="Specify log level. Possible values are INFO, WARN, ERROR. Default: INFO")
    
    args = parser.parse_args()
    stop_event = threading.Event()
    log = Log(args.logger)
    
    print(f"[CONFIG]\
          \nReload interval:       {args.reload} sec.\
          \nRun once:              {args.once}\
          \nPath:                  {args.path}\
          \nLog level:             {log.get_str_log_level}\
          \nMax threads:           {args.thread}")
    
    endpoint = ""
    if endpoint:
        notify = Notify(endpoint=endpoint)
    else:
        log.warn("Notify.run endpoint not set, push notifications will not be sent.")
        Product.send_push_notifications = False
    
    main(args.path, args.reload, args.once, args.thread)