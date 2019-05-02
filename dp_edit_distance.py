# -*- coding: utf-8 -*-

# a=['eins','zwei','drei','vier','fünf','sechs']
# b=['eins','zwei','drei','vier','sechs','sieben']
# b=['eins','drei','vier','fuenf','sechs','sieben']


def get_edit_distance_changes(text_old, text_new):
    tb = [[0 for i in range(len(text_old)+1)] for j in range(len(text_new)+1)]

    for i in range(1, len(text_new)+1):
        for j in range(1, len(text_old)+1):
            delta = 0
            if(text_old[j-1] != text_new[i-1]):
                delta = 1
            tb[i][j] = min(tb[i-1][j], tb[i][j-1], tb[i-1][j-1]) + delta

    # for i in range(len(tb)):
        # for j in range(len(tb[i])):
            # print(tb[i][j], end='\t')
        # print()

    reverse_change_stack = []

    # backtracking
    i = len(text_new)
    j = len(text_old)

    counter = 0
    while(counter < len(text_old)+1+len(text_new)+1):
        counter = counter+1

        min_before = min(tb[i-1][j], tb[i][j-1], tb[i-1][j-1])
        # print("right now @ " + str(i) + " "+str(j) + " min bef:" + str(min_before) + " current:" + str(tb[i][j]))

        # first choice (pref:) diagonal up, i.e. swap
        if(tb[i-1][j-1] == min_before and i-1 >= 0 and j-1 >= 0):
            if(min_before < tb[i][j]):
                # swapped:
                # print("swap")
                reverse_change_stack.extend([("swap", text_old[j-1], text_new[i-1])])

            i = i-1
            j = j-1
            continue

        # else on of them was deleted:
        elif(tb[i-1][j] == min_before and i-1 >= 0):
            if(min_before < tb[i][j]):
                # print("add")
                reverse_change_stack.extend([("added", text_new[i-1])])
            i = i-1
            continue

        # else on of them was deleted:
        elif(tb[i][j-1] == min_before and j-1 >= 0):
            if(min_before < tb[i][j]):
                # print("del")
                reverse_change_stack.extend([("deleted", text_old[j-1])])

            j = j-1
            continue
        else:
            pass

    return reverse_change_stack[::-1]

'''
a = []
b = []
text_old = "eins zwei drei"
text_new = "ein zwei drei vier"
for word in text_old.split():
    a.append(word)
for word in text_new.split():
    b.append(word)


changes = get_edit_distance_changes(a, b)
for a in changes:
    for my_str in a:
        print(str(my_str), end=' ')
    print()'''
