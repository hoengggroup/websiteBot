from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import sys
from pathlib import Path
import difflib
import dp_edit_distance


parent_directory_binaries = str(Path(__file__).resolve().parents[0])

firefoxProfile = FirefoxProfile()
firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
## Disable CSS
firefoxProfile.set_preference('permissions.default.stylesheet', 2)
## Disable images
firefoxProfile.set_preference('permissions.default.image', 2)
## Disable JavaScript
firefoxProfile.set_preference('javascript.enabled', False)
## Disable Flash
firefoxProfile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so','false')

caps = DesiredCapabilities().FIREFOX
#caps["pageLoadStrategy"] = "normal"  #  complete
caps["pageLoadStrategy"] = "eager"  #  interactive

driver = webdriver.Firefox(desired_capabilities=caps,executable_path=parent_directory_binaries + '/drivers/geckodriver_mac', firefox_profile=firefoxProfile)
driver.set_page_load_timeout(10)


text_old=""
hash_old=""
while(True):
    try:
        driver.get("https://tassilo-schwarz.com/test-page/feef")
    except:
        pass # timeout, e.g.
    text_current = driver.find_element_by_tag_name("body").text
    hash_current = hash(text_current)
    print("Hash: "+str(hash_current))

    # if change:
    if(hash_current!=hash_old):
        print("Hash changed. Comparing text")
        a=[]
        b=[]
        for word in text_old.split():
            a.append(word)
        for word in text_current.split():
            b.append(word)
        changes = dp_edit_distance.get_edit_distance_changes(a,b)
        print("Changes begin ---")
        for change_tupel in changes:
                for my_str in change_tupel:
                    print(str(my_str),end=' ')
                print()
        print("-- changes end")
        print("Hash change was: "+str(hash_current)+" "+str(hash_old))

        hash_old = hash_current
        text_old = text_current
    