# -*- coding: utf-8 -*-
"""Openacademy Database models"""
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Course(models.Model):
    """Course Model"""
    _name = 'openacademy.course'
    _description = 'OpenAcademy Course'

    name = fields.Char(
        string="Title",
        required=True,
        help="Name of the Course")
    description = fields.Text()
    responsible_id = fields.Many2one('res.users', ondelete='set null',
                                     string="Responsible", index=True)
    session_ids = fields.One2many(
        'openacademy.session',
        'course_id',
        string="Sessions")

    def copy(self, default=None):
        default = dict(default or {})

        copy_count = self.search_count(
            [('name', '=like', "Copy of {}".format(self.name))]
        )

        if not copy_count:
            new_name = "Copy of {}".format(self.name)
        else:
            new_name = "Copy of {} ({})".format(self.name, copy_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         _("The title of the course should not be the description.")
         ),

        (
            'name_unique',
            'UNIQUE(name)',
            _("The course title must be unique.")
        ),
    ]


class Session(models.Model):
    """Session Model"""
    _name = 'openacademy.session'
    _description = 'OpenAcademy Sessions'

    name = fields.Char(required=True)
    start_date = fields.Date(default=lambda self: fields.Date.today())
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    end_date = fields.Date(compute="_compute_end_date", store=True)
    seats = fields.Integer(string="Number of seats")
    instructor_id = fields.Many2one('res.partner', string="Instructor")
    course_id = fields.Many2one('openacademy.course', ondelete='cascade',
                                string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(compute='_compute_taken_seats')
    active = fields.Boolean(default=True)

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for line in self:
            if not (line.start_date and line.duration):
                line.end_date = line.start_date

            duration = timedelta(days=line.duration, seconds=-1)
            line.end_date = line.start_date + duration

    @api.depends('seats', 'attendee_ids')
    def _compute_taken_seats(self):
        for line in self:
            if not line.seats:
                line.taken_seats = 0.0
            else:
                line.taken_seats = 100.0 * len(line.attendee_ids) / line.seats

    @api.onchange('seats', 'attendee_ids')
    def _onchange_verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect \"seats\" value"),
                    'message': _("The number of available seats may not be negative."),
                }}
        elif self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase number of seats({}) or remove excess attendees({})").format(
                        self.seats,
                        len(self.attendee_ids)),
                }}

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for line in self:
            if line.instructor_id and (
                    line.instructor_id in line.attendee_ids):
                raise ValidationError(
                    _("A session's intructor can't be an attendee."))
