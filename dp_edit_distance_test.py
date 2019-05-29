import dp_edit_distance

def print_change_tupel(changes):
    print("Changes begin ---")
    for change_tupel in changes:
        for my_str in change_tupel:
            print(str(my_str), end=' ')
        print()
    print("--- End of changes. ---")


def test_case(text_old, text_new):
    changes = dp_edit_distance.get_edit_distance_changes(text_old= text_old, text_new = text_new)
    print_change_tupel(changes)

text_old = ['a','b','c']
text_new = ['a','b','c','d']

test_case(text_old = text_old, text_new=text_new)


text_old = ['a','b','c','d','e']
text_new = ['a','c','d','e']

test_case(text_old = text_old, text_new=text_new)


text_old = ['a','b']
text_new = ['a']

test_case(text_old = text_old, text_new=text_new)


text_old = ['a','b','c']
text_new = ['a','2','c']

test_case(text_old = text_old, text_new=text_new)





