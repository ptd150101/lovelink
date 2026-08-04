from django.core import signing
EMAIL_SALT = "lovelink.email.verify"
PASSWORD_SALT = "lovelink.password.reset"

def email_token(user): return signing.dumps({"uid": str(user.pk), "email": user.email}, salt=EMAIL_SALT)
def password_token(user): return signing.dumps({"uid": str(user.pk), "pwd": user.password[-12:]}, salt=PASSWORD_SALT)
def load_email_token(token, max_age): return signing.loads(token, salt=EMAIL_SALT, max_age=max_age)
def load_password_token(token, max_age): return signing.loads(token, salt=PASSWORD_SALT, max_age=max_age)
