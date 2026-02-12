from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # นับจำนวนแจ้งเตือนที่ยังไม่ได้อ่าน (is_read=False)
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_notification_count': unread_count}
    return {}