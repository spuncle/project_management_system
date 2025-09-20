from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import User, InvitationCode

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password', message='两次输入的密码不一致。')])
    invitation_code = StringField('邀请码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('该用户名已被使用。')
            
    def validate_invitation_code(self, invitation_code):
        code = InvitationCode.query.filter_by(code=invitation_code.data).first()
        if not code:
            raise ValidationError('邀请码无效。')
        if code.is_used:
            raise ValidationError('此邀请码已被使用。')

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

class InvitationForm(FlaskForm):
    submit = SubmitField('生成新邀请码')

# --- 【新增】修改密码表单 ---
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password', message='两次输入的新密码不一致。')])
    submit = SubmitField('修改密码')
# --------------------------