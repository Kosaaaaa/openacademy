# -*- coding: utf-8 -*-
"""Openacademy Database models"""
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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


class Session(models.Model):
    """Session Model"""
    _name = 'openacademy.session'
    _description = 'OpenAcademy Sessions'

    name = fields.Char(required=True)
    start_date = fields.Date()
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    end_date = fields.Date(compute="_compute_end_date", store=True)
    seats = fields.Integer(string="Number of seats")
    instructor_id = fields.Many2one('res.partner', string="Instructor")
    course_id = fields.Many2one('openacademy.course', ondelete='cascade',
                                string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    @api.depends('start_date', 'duration')
    def _compute_end_date(self):
        for line in self:
            if not (line.start_date and line.duration):
                line.end_date = line.start_date
                raise UserError(_('Duration or Start Date is not specified. You can fill it.'))

            duration = timedelta(days=line.duration, seconds=-1)
            line.end_date = line.start_date + duration
