def quicksort(a: list):
    #对a的每一项检查是否是数字
    for i in a:
        if a is None or not isinstance(i, (int, float)):
            return False
        #递归调用
    if len(a) <= 1:
        return a
    else:
        pivot = a[0]
        left = []
        right = []
        for i in a[1:]:
            if i < pivot:
                left.append(i)
            else:
                right.append(i)
        return quicksort(left) + [pivot] + quicksort(right)
def sort(a: list):
    #对a的每一项检查是否是数字,并进行冒泡排序
    for i in a:
        if a is None or not isinstance(i, (int, float)):
            return False
    for i in range(len(a)):
        for j in range(len(a)-i-1):
            if a[j] > a[j+1]:
                a[j],a[j+1] = a[j+1],a[j]
    return a
