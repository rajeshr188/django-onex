from django.shortcuts import render

# Create your views here.
def  noticegroup_list(request):
    ng = NoticeGroup.objects.all()
    return render(request,'girvi/noticegroup_list.html',context={'objects':ng})

def noticegroup_create(request):
    form = NoticeGroupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            object = form.save()
            return render(request,'girvi/noticegroup_detail.html',context={'object':object})
    return render(request,'girvi/noticegroup_form.html',context={'form':form})

def noticegroup_detail(request,pk):
    ng = get_object_or_404(NoticeGroup,pk = pk)
    loans = Loan.objects.unreleased().filter(created__gt = ng.date_range.lower,created__lt = ng.date_range.upper)

    return render(request,'girvi/noticegroup_detail.html',context={'object':ng,'loans':loans})