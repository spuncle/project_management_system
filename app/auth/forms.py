from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User, InvitationCode

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    invitation_code = StringField('邀请码', validators=[DataRequired()]) # <--- 新增字段
    submit = SubmitField('注册')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('该用户名已被使用。')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('该邮箱已被注册。')
            
    # --- 新增邀请码验证逻辑 ---
    def validate_invitation_code(self, invitation_code):
        code = InvitationCode.query.filter_by(code=invitation_code.data).first()
        if not code:
            raise ValidationError('邀请码无效。')
        if code.is_used:
            raise ValidationError('此邀请码已被使用。')
    # --------------------------

class LoginForm(FlaskForm):
    # ... 内容无变化 ...
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

# --- 邀请表单简化 ---
class InvitationForm(FlaskForm):
    submit = SubmitField('生成新邀请码')
# --------------------