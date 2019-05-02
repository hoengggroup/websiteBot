

#a=['eins','zwei','drei','vier','fünf','sechs']
# b=['eins','zwei','drei','vier','sechs','sieben']
#b=['eins','drei','vier','fuenf','sechs','sieben']

a=['eins','zwei','drei']
b =['ein','zwei','drei','vier',]


def get_distance(a,b):
    tb = [[0 for i in range(len(a)+1)] for j in range(len(b)+1)]

    for i in range(1,len(b)+1):
        for j in range(1,len(a)+1):
            delta=0
            if(a[j-1] != b[i-1]):
                delta = 1
            tb[i][j] = min(tb[i-1][j],tb[i][j-1],tb[i-1][j-1])+delta
    
    for i in range(len(tb)):
        for j in range(len(tb[i])):
            print(tb[i][j],end='\t')    
        print()

    reverse_change_stack=[]
    
    

    # backtracking
    i = len(b)
    j = len(a)


    counter = 0
    while(counter< len(a)+1+len(b)+1):
        counter=counter+1
        
    

        min_before = min(tb[i-1][j],tb[i][j-1],tb[i-1][j-1])
        print("right now @ "+str(i)+" "+str(j)+" min bef:"+str(min_before)+" current:"+str(tb[i][j]))
        
        # first choice (pref:) diagonal up, i.e. swap
        if(tb[i-1][j-1] == min_before and i-1>=0 and j-1>=0):
            if(min_before < tb [i][j]):
                # swapped:
                print("swap")
                reverse_change_stack.extend([("swap",a[j-1],b[i-1])])
            
            i = i-1
            j = j-1
            continue
        
        # else on of them was deleted:
        elif(tb[i-1][j] == min_before and i-1 >=0): 
            if(min_before < tb[i][j]):
                print("add")
                reverse_change_stack.extend([("added",b[i-1])])
            i = i-1
            continue

        # else on of them was deleted:
        elif(tb[i][j-1] == min_before and j-1>=0):
            if(min_before < tb[i][j]):
                print("del")
                reverse_change_stack.extend([("deleted",a[j-1])])
            
            j = j-1
            continue
        else:
            pass

    return reverse_change_stack[::-1]
                

changes = []
changes = get_distance(a,b)
for a in changes:
        for my_str in a:
            print(str(my_str),end=' ')
        print()