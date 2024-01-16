from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, SelectMultipleField, BooleanField
from wtforms.fields import TimeField
from wtforms.validators import DataRequired

from wtforms import SelectMultipleField, widgets

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class DealSubmissionForm(FlaskForm):
    establishment_name = StringField('Establishment Name', validators=[DataRequired()])
    establishment_type = SelectField('Establishment Type', choices=[('bar', 'Bar'), ('restaurant', 'Restaurant'), ('other', 'Other')], validators=[DataRequired()])
    deal_name = StringField('Deal Name', validators=[DataRequired()])
    deal_description = TextAreaField('Deal Description', validators=[DataRequired()])
    all_day = BooleanField('All Day')
    start_time = TimeField('Start Time', validators=[DataRequired()], render_kw={'disabled': ''})  # Initially disabled
    end_time = TimeField('End Time', validators=[DataRequired()], render_kw={'disabled': ''})  # Initially disabled
    days_active = MultiCheckboxField('Days Active:\n', choices=[('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday')], validators=[])
    repeat = BooleanField('Recurring Deal?')
    submit = SubmitField('Submit')