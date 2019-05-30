from main_driver import preprocess_string

import telegramService

# test 1
my_str="Hellö. My naäe ist test.  Test4\n\ntest5. .fdfä.ä."
res = preprocess_string(my_str)

print("Result: "+str(res))

