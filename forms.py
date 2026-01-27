from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class KnowledgeEntryForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    topic = SelectField('Тема', choices=[])
    content = TextAreaField('Содержание', validators=[DataRequired()], render_kw={"rows": 15})