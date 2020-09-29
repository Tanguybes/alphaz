from ..models.database.main_definitions import Notification, User

def add_notifications(api,db,element_type,element_action,id,users=None,all_users=True):
    if all_users:
        users           = db.select(User,distinct=User.id,columns=[User.id])

    notifications   = [Notification(user=x.id,user_from=api.user['id'],element_type=element_type,element_action=element_action,element_id=id) for x in users]
    db.add(notifications)