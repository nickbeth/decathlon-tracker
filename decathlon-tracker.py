import argparse
import time
from datetime import datetime
import requests, bs4

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"}

# Return parsed file as a dict
def parse_file(filepath):
    try:
        f = open(filepath, mode="r")
    except FileNotFoundError:
        raise

    # Look for '#' at the beginning of the line. Equivalent to commenting, line will be discarded
    file_dict = {}
    for line in f:
        if not (line := line.strip()).startswith("#"):
            try:
                size, url = line.split()
            except:
                size, url = "", line
            file_dict[url] = size

    f.close()
    return file_dict

class Log:
    LOG_LEVEL_FATAL = 0
    LOG_LEVEL_ERROR = 1
    LOG_LEVEL_WARN  = 2
    LOG_LEVEL_INFO  = 3
    LOG_LEVEL_VERBOSE = 4
    LOG_LEVEL_DEBUG = 5

    def __init__(self, log_level):
        self._str_log_level = log_level
        if log_level == "FATAL":
            self._log_level = self.LOG_LEVEL_FATAL
        elif log_level == "ERROR":
            self._log_level = self.LOG_LEVEL_ERROR
        elif log_level == "WARN":
            self._log_level = self.LOG_LEVEL_WARN
        elif log_level == "INFO":
            self._log_level = self.LOG_LEVEL_INFO
        elif log_level == "VERBOSE":
            self._log_level = self.LOG_LEVEL_VERBOSE
        elif log_level == "DEBUG":
            self._log_level = self.LOG_LEVEL_DEBUG

    @property
    def get_log_level(self):
        return self._log_level

    @property
    def get_str_log_level(self):
        return self._str_log_level

    def fatal(self, message):
        if self._log_level >= self.LOG_LEVEL_FATAL:
            print(f"[FATAL] {message}")

    def error(self, message):
        if self._log_level >= self.LOG_LEVEL_ERROR:
            print(f"[ERROR] {message}")
    
    def warn(self, message):
        if self._log_level >= self.LOG_LEVEL_WARN:
            print(f"[WARNING] {message}")
    
    def info(self, message):
        if self._log_level >= self.LOG_LEVEL_INFO:
            print(f"[INFO] {message}")

    def verbose(self, message):
        if self._log_level >= self.LOG_LEVEL_VERBOSE:
            print(f"[VERBOSE] {message}")

    def debug(self, message):
        if self._log_level >= self.LOG_LEVEL_DEBUG:
            print(f"[DEBUG] {message}")

    def now(self, message):
        currentDate = datetime.now().strftime("%H:%M:%S")
        print(f"[{currentDate}] {message}")

class Product:
    LOADING_ERROR = -1
    NOT_AVAILABLE = 0
    AVAILABLE = 1
    LIMITED = 2

    STATUS_ERROR = "ERROR"
    STATUS_OK = "OK"

    send_push_notifications = True

    def __init__(self, item_url):
        self._url = item_url
        self.notified_available = False
        self.notified_limited = False
        self._available = self.NOT_AVAILABLE
        self._name = ""
        self._status = self.STATUS_ERROR
        if self._fetch_name():
            self._status = self.STATUS_OK

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
        return(f"{{{self._url}, {self._name}, {self._status}, {{{self.notified_available}, {self.notified_limited}}}}}")

    def __str__(self):
        return(f"[ITEM]\
               \nProduct name:          {self._name}\
               \nStatus:                {self._status}")

    def _fetch_page(self):
        try:
            raw_html = requests.get(self._url, headers=HEADERS)
        except KeyboardInterrupt:
            exit(0)
        except:
            return None

        soup = bs4.BeautifulSoup(raw_html.text, "html.parser")
        return soup

    def _fetch_name(self):
        try:
            self._name = self._fetch_page().select(".product-title-right")[0].get_text()
            return True
        except:
            self._name = ""
            return False

    def is_available(self):
        page = self._fetch_page()
        if not page:
            self._available = self.LOADING_ERROR
            return

        target = page.select(".info-green")
        if len(target):
            if target[0].get_text() == "Disponibile":
                self._available = self.AVAILABLE
        else:
            target = page.select(".info-orange")
            if len(target):
                self._available = self.LIMITED
            self._available = self.NOT_AVAILABLE

class SizedProduct(Product):
    def __init__(self, item_url, size):
        super().__init__(item_url)
        self._size = "Error"
        self._size_index = 0

        # find size index
        page = self._fetch_page()
        if self._status == self.STATUS_OK and len(list := page.select("li.sizes__size")):
            for entry in list:
                if entry.get_text().split()[0] == size:
                    self._size = size
                    break
                self._size_index += 1

    @property
    def name(self):
        return f"{self._name} ({self._size})"

    def __repr__(self):
        return(f"{{{self._url}, {self._name}, {self._size} {self._size_index}, {self._status}, {{{self.notified_available}, {self.notified_limited}}}}}")

    def __str__(self):
        return(f"[ITEM]\
               \nProduct name:          {self._name}\
               \nSize:                  {self._size}\
               \nStatus:                {self._status}")

    def is_available(self):
        page = self._fetch_page()
        try:
            target = page.select(f"li.sizes__size")[self._size_index]
        except:
            self._available = self.LOADING_ERROR
            return

        if int(target["data-available-quantity"]):
            if len(target.select(".sizes__stock__info--limitedstock")):
                self._available = self.LIMITED
            else:
                self._available = self.AVAILABLE
        else:
            self._available = self.NOT_AVAILABLE

def check_product(product):
    product.is_available()

    if product.available == Product.AVAILABLE:
        logger.now(f"{product.name} is available")
        if Product.send_push_notifications and not product.notified_available:
            notify.send(f"[Available] {product.name} available on decathlon.it!")
            product.notified_available = True
            logger.info("Available notification sent")
    elif product.available == Product.LIMITED:
        logger.now(f"{product.name} is available in limited quantities")
        if Product.send_push_notifications and not product.notified_limited:
            notify.send(f"[Limited] {product.name} available on decathlon.it!")
            product.notified_limited = True
            logger.info("Limited quantity notification sent")
    elif product.available == Product.NOT_AVAILABLE:
        logger.now(f"{product.name} is not available")
        if Product.send_push_notifications and (product.notified_available or product.notified_limited):
            notify.send(f"[Out of stock] {product.name} is not available anymore!")
            product.notified_available = False
            product.notified_limited = False
            logger.info("Notification status reset")
    elif product.available == Product.LOADING_ERROR:
        logger.error(f"Could not load {product.name}: 'returned empty page'")
    else:
        logger.error("Unhandled exception")

def main(path, reload_interval, run_once):
    logger.info("Loading items info...")
    try:
        products = []
        for url, size in parse_file(path).items():
            logger.verbose(f"Fetching {url}")
            if size:
                products.append(SizedProduct(url, size))
            else:
                products.append(Product(url))
    except FileNotFoundError as e:
        logger.fatal(e)
        exit(1)

    if l := len(products): 
        logger.info(f"N. of items: {l}")
        [print(product) for product in products]
    else:
        logger.fatal("Empty item list, aborting.")
        exit(0)

    # tracker loop
    logger.verbose("Entered tracking loop, break with CTRL+C.")
    while 1:
        try:
            for product in products:
                check_product(product)
                time.sleep(reload_interval/len(products))
            if run_once:
                break
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decathlon Bot. Gets URLs from a file and tracks availability on a set interval.")

    # Pass arguments to the program - default config
    parser.add_argument("-p", "--path", default="./products.txt", type=str, help="Path of file containing URLs of products to track. Default: ./products.txt")
    parser.add_argument("-r", "--reload", default=30, type=int, help="Reload interval in seconds. Default: 30")
    parser.add_argument("-o", "--once", action="store_const", const=True, help="Iterate the tracker loop once and exit")
    parser.add_argument("-l", "--logger", default="INFO", type=str, choices={"ERROR", "WARN", "INFO", "VERBOSE", "DEBUG"},
                        help="Specify log level. Default: INFO")

    args = parser.parse_args()
    logger = Log(args.logger)
    
    print(f"[CONFIG]\
          \nReload interval:       {args.reload} sec.\
          \nRun once:              {bool(args.once)}\
          \nPath:                  {args.path}\
          \nLog level:             {logger.get_str_log_level}")

    # Notify.run endpoint setup
    try:
        with open("notify_endpoint.txt", mode="r") as f:
            endpoint = f.read().strip()
    except:
        endpoint = ""
    if endpoint:
        from notify_run import Notify
        notify = Notify(endpoint=endpoint)
        logger.info(f"Notify.run endpoint found, push notifications will be sent to {notify.endpoint}")
    else:
        logger.warn("Notify.run endpoint not set, push notifications will not be sent.")
        Product.send_push_notifications = False

    main(args.path, args.reload, args.once)