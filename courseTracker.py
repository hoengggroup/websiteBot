import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import sys

THRESH_ERROR_COUNT_MAX = 50
firefoxProfile = FirefoxProfile()
firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
driver = webdriver.Firefox(executable_path="/Users/black/programming/python/driversSelenium/geckodriver_mac",firefox_profile=firefoxProfile)
driver.set_page_load_timeout(3)
print("getting")
try:
    driver.get("https://www.finanzen.ch/devisen/realtimekurs/eurokurs")
except selenium.common.exceptions.TimeoutException as e:
    print("timeout in beginning, should be ok")
except:
    print("UNKNOWN error when getting website.")
    print("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))

lastVal = 0.0
errorCount=0
while True:

    #a=[]
    try:
        valueElement=driver.find_element_by_css_selector(".price")
        timeElement=driver.find_element_by_css_selector("td.text-center:nth-child(1) > div:nth-child(2) > span:nth-child(1)")

        currentVal = float(valueElement.text)
        currentTime = str(timeElement.text)
        if(currentVal != lastVal):
            print(str(currentTime)+":\t"+ str(currentVal))
            lastVal = currentVal
        errorCount = 0
    except selenium.common.exceptions.NoSuchElementException:
        errorCount+=1
        if(errorCount>THRESH_ERROR_COUNT_MAX):
            break
        print("ERROR. No such element")
        print("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
    except:
        errorCount+=1
        if(errorCount>THRESH_ERROR_COUNT_MAX):
            break
        print("An UNKNOWN exception has occured in the main while loop.")
        print("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))





    # pushbulletHelloWorld.processbullet(a)

    # print(len(a))

    # for element in a:
       # print(element.text)

print("finished")
