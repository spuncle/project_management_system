from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from app.models import Personnel

class PersonnelForm(FlaskForm):
    name = StringField('负责人姓名', validators=[DataRequired()])
    submit = SubmitField('添加')

    def validate_name(self, name):
        person = Personnel.query.filter_by(name=name.data).first()
        if person:
            raise ValidationError('该负责人已存在，请勿重复添加。')