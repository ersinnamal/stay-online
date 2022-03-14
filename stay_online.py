import subprocess
from time import sleep, time
from datetime import datetime
from requests import get
from requests.exceptions import ConnectionError
from termcolor import colored


class StayOnline():

    def __init__(self, ssids, scan_cmd, connect_cmd, passwords={}, login_function=None, sleep_time=5):

        self.ssids = ssids
        self.scan_cmd = scan_cmd
        self.connect_cmd = connect_cmd
        self.passwords = passwords
        self.login_function = login_function
        self.sleep_time = sleep_time
        self.found_ssids = []
        self.ssid_index = -1

    def scan(self, depth=0):

        if depth >= 3:
            return False

        try:
            output = subprocess.check_output(self.scan_cmd, shell=True)
        except subprocess.CalledProcessError:
            return self.scan_networks(depth + 1)

        output = output.decode("utf-8").replace("\n\t", " ").strip().split(" ")

        self.found_ssids = [output[i] for i in range(
            1, len(output), 2) if output[i] in self.ssids]
        return True

    def connect(self, ssid):

        try:
            command = self.connect_cmd + ssid
            if self.passwords[ssid]:
                command += " password " + self.passwords[ssid]

            output = subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError:
            return False

        if output.strip()[0] == "E":
            return False

        return True

    def check_network(self, errors=0):

        try:
            start_time = time()
            get("https://www.google.com", timeout=3)
            return time() - start_time

        except Exception as e:
            print(e)

        if errors == 2: 
            return False 

        return self.check_network(errors + 1)

    def start(self):

        self.ssid_index = (self.ssid_index + 1) % len(self.found_ssids)

        if self.connect(self.found_ssids[self.ssid_index]):
            print(f"connected to {self.found_ssids[0]}")
        else:
            print(f"connection failed to {self.found_ssids[0]}")
            self.scan()
            return self.start()

        if not self.check_network():

            if self.login_function and self.login_function():
                print("Successfully logged in")
            else:
                return self.start()
        
        self.loop()

        return self.start()

    def loop(self): 

        term_colors = ["green", "yellow", "red"]

        while True:
            network_status = self.check_network()

            if not network_status:
                print(f"{self.get_now_str()} connection is", colored("down", "red"))
                break

            try:
                color = term_colors[int(network_status)]
            except IndexError:
                color = term_colors[-1]

            print(f"{self.get_now_str()} connection is", colored("up", "green"),
                  colored(str(int(network_status * 100) / 100), color))
            sleep(self.sleep_time)

    @staticmethod
    def get_now_str():
        now = datetime.now()
        return f"[{now.hour:02}:{now.minute:02}:{now.second:02}]" 


if __name__ == "__main__":

    s = StayOnline(["ROUTER"], scan_cmd="sudo iw wlo1 scan | grep SSID:",
                   connect_cmd="sudo nmcli -w 10 d wifi connect ", passwords={"ROUTER": "password123"})
    s.start()
