# coding:utf-8
from django.core.paginator import Paginator, EmptyPage, InvalidPage

def page_list_return(total, current=1):
    min_page = current - 2 if current - 4 > 0 else 1
    max_page = min_page + 4 if min_page + 4 < total else total

    return range(min_page, max_page+1)
    #获得总页数，和当前页数，计算出最小页数并返回一个页数列表

def pages(posts, r):
    """分页公用函数"""
    contact_list = posts
    p = paginator = Paginator(contact_list, 5)
    ## 设置在每页显示的数量，这里为50,得到一个对象
    try:
        current_page = int(r.GET.get('page', '1'))
    except ValueError:
        current_page = 1

    page_range = page_list_return(len(p.page_range), current_page)
    #获取到页的范围，和当前页，并把它传给page_list_return，计算出最大页和最小页


    try:
        contacts = paginator.page(current_page)
        #跳转到当前页，如果发生错误，或者页数不存在调到总页数
    except (EmptyPage, InvalidPage):
        contacts = paginator.page(paginator.num_pages)
        #paginator.num_pages  总页数
    if current_page >= 5:
        show_first = 1
    else:
        show_first = 0
    if current_page <= (len(p.page_range) - 3):
        show_end = 1
    else:
        show_end = 0

    return contact_list, p, contacts, page_range, current_page, show_first, show_end