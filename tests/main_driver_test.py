from main_driver import preprocess_string

# test 1
my_str="Hellö. My naäe ist test.  Test4\n\ntest5. .fdfä.ä."
res = preprocess_string(my_str)

print("Result: "+str(res))
assert(str(res) == "['Hello', 'My naae ist test', ' Test4', 'test5', '.fdfa.a.']")
print("assert ok.\n\n")

