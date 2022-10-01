#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
New Bio-Man code

@author: menghanliu
"""
import pandas as pd
import numpy as np
import random
    
#TODO: 23 docstring headers

class Event:
    """
    Event_type includes arrival, harvest, process, finish 
    Event is defined as a point on the timeline.
    """
    def __init__(self, name, e_type, e_happen_time, place, machine, operator, job):
        self.name = name
        self.e_type = e_type
        self.e_happen_time = e_happen_time
        self.place = place
        self.machine = machine
        self.operator = operator
        self.job = job
        #self.rework_times = rework_times
        
    def get_event_info(self):
        # get 'Event name', 'Event type', 'Event happen time', 'Event place', 'Event machine', 'Event operator', 'Event job', 'Job yield','If in rework'
        # if rework
        self.if_in_rework='Not in rework'
        if self.job.rework_count >0:
            if self.job.state=='Setup' or self.job.state=='Harvesting' or self.job.state=='Processing':
                self.if_in_rework='In rework'
        if self.machine != None and self.operator != None:
            event_info=[self.name, self.e_type, self.e_happen_time, self.place.name, self.machine.name, self.operator.name, self.job.name, self.job.processing_yield, self.if_in_rework]
        elif self.machine != None and self.operator == None:
            event_info=[self.name, self.e_type, self.e_happen_time, self.place.name, self.machine.name, self.operator, self.job.name, self.job.processing_yield, self.if_in_rework]
        elif self.machine == None and self.operator != None:
            event_info=[self.name, self.e_type, self.e_happen_time, self.place.name, self.machine, self.operator.name, self.job.name, self.job.processing_yield, self.if_in_rework]
        else:
            event_info=[self.name, self.e_type, self.e_happen_time, self.place.name, self.machine, self.operator, self.job.name, self.job.processing_yield, self.if_in_rework]
        #print('event_info:', event_info)
        return event_info
        
    
    
class Job:    
    #also called patient
    def __init__(self, name, place, state):
        self.name = name
        self.gender = 'Default'
        self.place = place
        self.state = state
        #params
        self.pt_type = 'Default'    #bad, avg or good, generated by percentage
        self.BV = 'Default'
        self.patients_target_bc = 'Default'
        #for rework
        self.rework_count = 0
        self.rework_time_points = []
        self.enter_sys_time = 'Default'
        self.leave_sys_time = 'Default'
        self.harvesting_yield = 'Default'
        self.processing_yield = 'Default'
        self.start_processing_time = 'Default'

    def Start_rework(self, this_clock):
        #Everytime a rework, no matter which -th, count it
        self.rework_count += 1
        self.rework_time_points.append(this_clock)
        
    def Enter_sys(self, this_clock):
        self.enter_sys_time = this_clock
        
    def Leave_sys(self, this_clock):
        self.leave_sys_time = this_clock
        
    def Booked(self):
        self.state = 'Booked' #it is in queue and it is booked



class Machine:
    def __init__(self, name, m_type):
        self.name = name
        self.m_type = m_type
        self.state = 'Idle'
        self.job = None
        self.operator = None 
        
    def Start_Setup(self, job, operator):
        self.state = 'Setup'
        self.job = job
        self.operator = operator
        self.job.state = 'Setup'
        self.operator.state = 'Busy'
        
    def End_Setup(self):
        self.state = 'End Setup'
        self.job.state = 'Setup'
        self.operator.state = 'Idle'

    def Start_Work(self):
        if self.m_type == 'Harvesting':
            self.state = 'Harvesting'
            self.job.state = 'Harvesting'
        elif self.m_type == 'Processing':
            self.state = 'Processing'
            self.job.state = 'Processing'
            
    def End_Work(self):
        if self.m_type == 'Harvesting':
            self.state = 'Idle'
            self.job.state = 'End Harvesting'
        elif self.m_type == 'Processing':
            self.state = 'End Processing'
            self.job.state = 'End Processing'
            
    def Booked(self):
        self.state = 'Booked' #it is in queue and it is booked
        
        
class Queue:    
    #also called patient
    def __init__(self, name, q_type):
        self.name = name
        self.q_type = q_type
        self.job_list = []
        
    def Add_Job(self, job):
        self.job_list.append(job)
        if self.q_type == 'Machine_queue':
            job.state = 'In {}'.format(self.name)
        else:
            pass
        
    def Remove_Job(self, job):
        self.job_list.remove(job)
        if self.q_type == 'Machine_queue':
            job.state = 'Out of {}'.format(self.name)
        else:
            pass
        
        
class Operator:    
    #also called patient
    def __init__(self, name, o_type):
        self.name = name
        self.o_type = o_type
        self.capacity = 'infinite'
        self.state = 'Idle'
        
    def Booked(self):
        self.state = 'Booked' #it is in queue and it is booked
        
    
