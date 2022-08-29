#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
New Bio-Man code

@author: menghanliu
"""

import BM_Toolbox as toolbox
import pandas as pd
import numpy as np
import random
import csv
import scipy.stats as stats



def Put_something_into_csv(something, fname):
    with open(fname, "a") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(something)

def Truncated_Norm_gen(lower, mu, sigma):
    upper = mu + (mu - lower)
    X = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
    res = X.rvs(1)[0]
    return res

class Environment():
    def __init__(self, Design, group_num):
        self.event_list = []
        self.clock = 0
        self.global_state = 'Initial'
        self.job_gen_count = 0
        self.group_num = group_num
        
        #params
        self.patient_max_num = 20 #4000#5 #10  #maximum number of patients who can come for therapy
        self.patient_arrival_distribution = 'Uniform'
        self.conversion_factor = 140000   #blood count multiplication factor
        self.BV_m_LB = 5                  # lower bound of blood vol in male
        self.BV_m_HB = 7.5                # higher bound of blood vol in male
        self.BV_f_LB = 3.5                # lower bound of blood vol in female
        self.BV_f_HB = 6.0                # higher bound of blood vol in female
        self.time_budget_for_Arrival =200  #total time for patient arrival in a year's time
        self.Simulation_time_budget = 3000     #total time for patient arrival in a year's time
        self.Female_ratio = 0.5
        self.max_rework_times = 3        #max times of rework, otherwise give up
        self.delta_t = 5     #5 days
        self.normal_dist_std = 0.7
        
        #params of design(old not using): [Manufacturing Time mix, Delta mix, Patient mix, QM Policy, Hrv Operator, Hrv Machines, Mfg Operators, Mfg Machines]
        #params of design: [Manufacturing Time mix, System mix, Patient mix, Hrv Operator, Hrv Machines, Mfg Operators, Mfg Machines]
        #Design to params
        #Manufacturing Time mix
        if Design[0] == 0:
            #stressed system
            self.mfg_dura_perc = [0.5, 0.25, 0.25]
            #self.mfg_dura = [7, 20, 35] is defined by t_low and t_up
        elif Design[0] == 1:
            #relaxed system
            self.mfg_dura_perc = [0.25, 0.5, 0.25]
            #self.mfg_dura = [20, 35, 60]
        #System mix
        if Design[1]==0:
            #stressed system
            self.low_slope = 100000 
            self.up_slope = 4000
        else:
            #relaxed system
            self.low_slope = 85000
            self.up_slope = 20000
        #Paitient mix
        if Design[2] == 0:
            self.bad_pat_rate = 8
            self.avg_pat_rate = 1
            self.good_pat_rate = 1
        elif Design[2] == 1:
            self.bad_pat_rate = 2
            self.avg_pat_rate = 5
            self.good_pat_rate = 3
        #Quality policy
        self.QM_Policy_MFG = 0 #Design[3]
        #Machine and operator
        if Design[3] == 0:
            self.hrv_machine_num = 4
        elif Design[3] == 1:
            self.hrv_machine_num = 8
        if Design[4] == 0:
            self.hrv_operator_num = 2
        elif Design[4] == 1:
            self.hrv_operator_num = 3
        if Design[5] == 0:
            self.mfg_machine_num = 8
        elif Design[5] == 1:
            self.mfg_machine_num = 12
        if Design[6] == 0:
            self.mfg_operator_num = 4
        elif Design[6] == 1:
            self.mfg_operator_num = 6

            
    def Machine_and_Operator_Setup(self):
        """
        Sets up the job list, mfg and hrv operators and machines  
        """
        self.job_list = []  #Job is defined by patient arrival function 
        self.queue_1 = toolbox.Queue('Queue_1', 'Machine_queue')
        self.queue_2 = toolbox.Queue('Queue_2', 'Machine_queue')
        self.queue_3 = toolbox.Queue('Queue_3', 'Machine_queue')
        self.queue_4 = toolbox.Queue('Queue_4', 'Operator_queue')
        self.queue_5 = toolbox.Queue('Queue_5', 'Operator_queue')
        self.hrv_operator_list = [toolbox.Operator('HO{}'.format(o+1), 'Harvesting') for o in range(0, int(self.hrv_machine_num))]
        self.hrv_machine_list = [toolbox.Machine('HM{}'.format(m+1), 'Harvesting') for m in range(0, int(self.hrv_operator_num))]
        self.mfg_operator_list = [toolbox.Operator('PO{}'.format(o+1), 'Processing') for o in range(0, int(self.mfg_machine_num))]
        self.mfg_machine_list = [toolbox.Machine('PM{}'.format(m+1), 'Processing') for m in range(0, int(self.mfg_operator_num))]
        #self.QC_operator_list = [toolbox.Operator('QO{}'.format(q+1), q+1, 'QC') for q in range(0, int(self.QC_Operators_Count))] 
        self.QC_machine = toolbox.Machine('QC', 'QC')
        self.Finish_stack = toolbox.Machine('Finish_stack', 'Finish_stack')
        self.finish_list = []
        
        
    def get_event(self):
        '''
        Gets the first event in the event list
        https://github.com/tkralphs/PyQueueSim/blob/master/QueueSim.py
        '''        
        #event = self.event_list.pop()
        #self.clock = event.e_happen_time
        
        temp = self.event_list[0]
        for item in self.event_list:
            if item.e_happen_time < temp.e_happen_time:
                temp = item
        event = temp
        
        if event.e_happen_time < self.clock:
            event.e_happen_time = self.clock
        
        self.event_list.remove(event)
        self.clock = event.e_happen_time
        
        return event


    def add_event(self, event):
        """
        Add event to event_list.
        """
        self.event_list.append(event)
        return
    
    
    def get_current_state(self):
        #get state info for the machine, operator,queue, job
        hrv_operator_state_list = [o.state for o in self.hrv_operator_list]
        mfg_operator_state_list = [o.state for o in self.mfg_operator_list]
        #QC_operator_state_list = ['Just QC machine'] 
        hrv_machine_state_list = [m.state for m in self.hrv_machine_list]
        mfg_machine_state_list = [m.state for m in self.mfg_machine_list]
        q1_state_list = [job.name for job in self.queue_1.job_list]
        q2_state_list = [job.name for job in self.queue_2.job_list]
        q3_state_list = [job.name for job in self.queue_3.job_list]
        q4_state_list = [job.name for job in self.queue_4.job_list] #hrv opr queue
        q5_state_list = [job.name for job in self.queue_5.job_list] #mfg opr queue   
        job_state_list = [j.state for j in self.job_list]
        event_list = [j.name for j in self.event_list]
        current_state_info = [hrv_operator_state_list, mfg_operator_state_list, hrv_machine_state_list, mfg_machine_state_list,
                              q1_state_list, q2_state_list, q3_state_list, q4_state_list, q5_state_list, job_state_list, event_list]
        return current_state_info
    
    def get_rework_state(self):
        rework_state_list=[]
        for job in self.job_list:
            if job.rework_count >0 and job.state != 'Finish':
                rework_state_list.append('In rework')
            else:
                rework_state_list.append('Not in rework')
        return rework_state_list
        
    def Simulate(self):
        """
        This is the simulation of the factory.
        """
        output_file = 'results/Event_information_group_{}.csv'.format(self.group_num)
        header = ['Clock', 'Event name', 'Event type', 'Event happen time', 'Event place', 'Event machine', 'Event operator', 'Event job', 
                  'Job yield','if_in_rework', 'hrv_operator_state_list', 'mfg_operator_state_list', 'hrv_machine_state_list', 'mfg_machine_state_list', 
                  'q1_state_list', 'q2_state_list', 'q3_state_list', 'q4_state_list', 'q5_state_list', 'job_state_list','event_list','total job count','rework_job_list']
        Put_something_into_csv(header, output_file)
        
        self.Machine_and_Operator_Setup()
        self.df_this_design = pd.DataFrame(columns=['Clock', 'Event name', 'Event type', 'Event happen time', 'Event place', 'Event machine', 'Event operator', 'Event job', 
                                                    'Job yield','if_in_rework', 'hrv_operator_state_list', 'mfg_operator_state_list', 
                                                    'hrv_machine_state_list', 'mfg_machine_state_list', 'q1_state_list', 'q2_state_list', 'q3_state_list', 
                                                    'q4_state_list', 'q5_state_list', 'job_state_list','event_list','total job count','rework_job_list'])
        new_job = self.Job_generator('J1', self.queue_1, 'In Queue_1')
        self.job_list.append(new_job)
        first_event = toolbox.Event('Patient {} arrival at {}'.format(new_job.name, self.queue_1.name), 'Arrival', self.clock, self.queue_1, None, None, new_job)
        self.job_gen_count += 1
        self.add_event(first_event)
        
        #Simulation
        while self.clock <= self.Simulation_time_budget:
            print('******************************************************')
            print('Now event_list:')
            print('---------------')
            if self.event_list == []:
                print('Simulation finished, there is no more event.')
                break
            else:
                this_event = self.get_event()
                print('*Clock {}:*'.format(self.clock))
                print('\n')
                print('*This event:*', this_event.get_event_info())
                self.Process_event(this_event)
                print('\n')
                #print('*Current state:*', self.get_current_state())
                to_append = [self.clock]+ this_event.get_event_info() + self.get_current_state() + [self.job_gen_count] + [self.get_rework_state()]
                Put_something_into_csv(to_append, output_file)
                
        time_in_system_list=[]
        for this_job in self.job_list:
            if this_job.state == 'Finish':
                time_in_system_list.append(this_job.leave_sys_time - this_job.enter_sys_time)
            else:
                time_in_system_list.append(self.clock - this_job.enter_sys_time)
        avg_time_in_sys = sum(time_in_system_list)/len(time_in_system_list)
        to_append =[avg_time_in_sys]+ [time_in_system_list]
        Put_something_into_csv(to_append, output_file)

        return self.df_this_design
    
    
    def Job_generator(self, name, place, state):
        job = toolbox.Job(name, place, state)
        #good bad or average patient
        job.pt_type = random.choices(['bad', 'average', 'good'], weights = [self.bad_pat_rate, self.avg_pat_rate, self.good_pat_rate])[0]
        #gender
        job.gender = random.choices(['female', 'male'], weights = [self.Female_ratio, 1-self.Female_ratio])[0]
        #blood volume
        if job.gender == 'male':
            job.BV = np.random.uniform(low = self.BV_m_LB, high = self.BV_m_HB) 
        else:
            job.BV = np.random.uniform(low = self.BV_f_LB, high = self.BV_f_HB)
        #tgt bc
        job.patients_target_bc = job.BV * self.conversion_factor #Y-bar?
        #time
        job.enter_sys_time = self.clock
        return job
    
    def Processing_yield_curve(self, dura, job):
        #This function calculates yield according time t(dura) and params
        target_bc = job.patients_target_bc
        t_low = target_bc/self.low_slope
        t_up = t_low + self.delta_t
        t_zero = t_up + target_bc/self.up_slope
        if dura <= t_low:
            p_yield = self.low_slope * dura
        elif dura > t_low and dura <= t_up:
            p_yield = target_bc
        elif dura > t_up and dura <= t_zero:
            p_yield = target_bc - self.up_slope*(dura-t_up)
        elif dura > t_zero:
            p_yield = 0
        #80% quantile
        if p_yield > 0:
            #mu = percentile value-z*std, and z=-0.84 for 20% according to table
            mu = p_yield + 0.84*self.normal_dist_std
            p_yield = Truncated_Norm_gen(p_yield, mu, self.normal_dist_std)
        # Dpeend on patients
        if job.pt_type == 'bad':
            p_yield_new = 0.5*p_yield
        elif job.pt_type == 'average':
            p_yield_new = 0.8*p_yield
        elif job.pt_type == 'good':
            p_yield_new = 1*p_yield
        print('p_yield_new:', p_yield_new)
        if p_yield_new <= target_bc:
            p_yield_new_new = p_yield_new/target_bc
        else:
            p_yield_new_new = 1
        return p_yield_new_new
    
    
    def Operator_look_for_next_job_in_opr_queue(self, operator):
        #Before fully released, look for job that needs operator
        #If a job also need machine but no machine available, just skip and look for next
        if operator.o_type == 'Harvesting':
            opr_queue = self.queue_4
        elif operator.o_type == 'Processing':
            opr_queue = self.queue_5
        non_booked_job_list = [job for job in opr_queue.job_list if job.state != 'Booked']
        if non_booked_job_list != []:
            next_job_temp = non_booked_job_list[0]
            this_job = next_job_temp
            if operator.o_type == 'Harvesting':
                if self.get_available_machine('Harvesting') != []:
                    chosen_machine = random.choice(self.get_available_machine('Harvesting'))
                    chosen_operator= operator
                    next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_1.name), 'Departure', self.clock, self.queue_1, chosen_machine, chosen_operator, this_job)
                    chosen_operator.Booked()
                    chosen_machine.Booked()
                    this_job.Booked()
                    self.add_event(next_event)
                else:
                    pass
            elif operator.o_type == 'Processing':
                for i in range(len(non_booked_job_list)):
                    this_job_temp = non_booked_job_list[i]
                    if this_job_temp.state == 'End Processing':
                        next_event = toolbox.Event('Collect Job {}'.format(this_job.name), 'Collect', self.clock, this_job_temp.place, this_job_temp.place, operator, this_job_temp)
                        self.add_event(next_event)
                        break
                    elif this_job_temp.state == 'In Queue_2':
                        if self.get_available_machine('Processing') != []:
                            chosen_machine = random.choice(self.get_available_machine('Processing'))
                            chosen_operator= operator
                            next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_2.name), 'Departure', self.clock, self.queue_2, chosen_machine, chosen_operator, this_job_temp)
                            chosen_operator.Booked()
                            chosen_machine.Booked()
                            this_job.Booked()
                            self.add_event(next_event)
                            break
                        else:
                            pass
        else:
            pass

    
    def Machine_look_for_next_job_in_queue(self, machine):
        #Everytime a machine is released, it look for job in its queue
        if machine.m_type == 'Harvesting':
            machine_queue = self.queue_1
        elif machine.m_type == 'Processing':
            machine_queue = self.queue_2
        non_booked_job_list = [job for job in machine_queue.job_list if job.state != 'Booked']
        if non_booked_job_list != []:
            next_job_temp = non_booked_job_list[0]
            this_job = next_job_temp
            if machine.m_type == 'Harvesting':
                if self.get_available_operator('Harvesting') != []:
                    chosen_machine = machine
                    chosen_operator= random.choice(self.get_available_operator('Harvesting'))
                    next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_1.name), 'Departure', self.clock, self.queue_1, chosen_machine, chosen_operator, this_job)
                    chosen_operator.Booked()
                    chosen_machine.Booked()
                    this_job.Booked()
                    self.add_event(next_event)
                else:
                    pass
            elif machine.m_type == 'Processing':
                if self.get_available_operator('Processing') != []:
                    chosen_machine = machine
                    chosen_operator= random.choice(self.get_available_operator('Processing'))
                    next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_2.name), 'Departure', self.clock, self.queue_2, chosen_machine, chosen_operator, this_job)
                    chosen_operator.Booked()
                    chosen_machine.Booked()
                    this_job.Booked()
                    self.add_event(next_event)
                else:
                    pass
        else:
            pass
    
    
    def get_available_operator(self, o_type):
        available_operator_set = []
        if o_type == 'Harvesting':
            for operator in self.hrv_operator_list:
                if operator.state == 'Idle':
                    available_operator_set.append(operator)
        elif o_type == 'Processing':
            for operator in self.mfg_operator_list:
                if operator.state == 'Idle':
                    available_operator_set.append(operator)
        return available_operator_set

        
    def get_available_machine(self, m_type):
        available_machine_set = []
        if m_type == 'Harvesting':
            for machine in self.hrv_machine_list:
                if machine.state == 'Idle':
                    available_machine_set.append(machine)
        elif m_type == 'Processing':
            for machine in self.mfg_machine_list:
                if machine.state == 'Idle':
                    available_machine_set.append(machine)
        return available_machine_set
    
    
    def Process_event(self, this_event):
        #Event processing
        if this_event.e_type == 'Arrival':
            if this_event.place == self.queue_1:
                this_job = this_event.job
                #process event
                self.queue_1.Add_Job(this_job)
                this_job.place = self.queue_1
                #schedule next arrival
                if self.clock <= self.time_budget_for_Arrival and self.job_gen_count <= self.patient_max_num :
                    new_name = 'J'+str(int(''.join(filter(str.isdigit, this_job.name)))+1)
                    new_job = self.Job_generator(new_name, self.queue_1, 'In Queue_1')
                    self.job_list.append(new_job)
                    interarrival_time= np.random.randint(2,5)
                    new_event = toolbox.Event('Patient {} arrival at {}'.format(new_job.name, self.queue_1.name), 'Arrival', self.clock+ interarrival_time, self.queue_1, None, None, new_job)
                    self.job_gen_count += 1
                    self.add_event(new_event)
                #if possible, depart tp harvesting machine
                if self.get_available_operator('Harvesting') != [] and self.get_available_machine('Harvesting') != []:
                    chosen_machine = random.choice(self.get_available_machine('Harvesting'))
                    chosen_operator= random.choice(self.get_available_operator('Harvesting'))
                    next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_1.name), 'Departure', self.clock, self.queue_1, chosen_machine, chosen_operator, this_job)
                    chosen_operator.Booked()
                    chosen_machine.Booked()
                    this_job.Booked()
                    self.add_event(next_event)
                elif self.get_available_operator('Harvesting') == []:
                    #put job into operator queue
                    self.queue_4.Add_Job(this_job) 
            elif this_event.place == self.queue_2:
                this_job = this_event.job
                #process event
                self.queue_2.Add_Job(this_job)
                this_job.place = self.queue_2
                #if possible, depart to processing machine
                if self.get_available_operator('Processing') != [] and self.get_available_machine('Processing') != []:
                    chosen_machine = random.choice(self.get_available_machine('Processing'))
                    chosen_operator= random.choice(self.get_available_operator('Processing'))
                    next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_2.name), 'Departure', self.clock, self.queue_2, chosen_machine, chosen_operator, this_job)
                    chosen_operator.Booked()
                    chosen_machine.Booked()
                    this_job.Booked()
                    self.add_event(next_event)
                elif self.get_available_operator('Processing') == []:
                    #put job into operator queue
                    self.queue_5.Add_Job(this_job) 
            elif this_event.place == self.queue_3:
                this_job = this_event.job
                #process event
                self.queue_3.Add_Job(this_job)
                this_job.place = self.queue_3
                #depart to QC
                next_event = toolbox.Event('Job {} departure from {}'.format(this_job.name, self.queue_3.name), 'Departure', self.clock, self.queue_3, self.QC_machine, None, this_job)
                this_job.Booked()
                self.add_event(next_event)
            
        elif this_event.e_type == 'Departure':
            this_job = this_event.job
            #process event
            if this_event.place == self.queue_1:
                self.queue_1.Remove_Job(this_job)
                #schedule next
                next_event = toolbox.Event('Job {} start setup at {}'.format(this_job.name, this_event.machine.name), 'Start_Setup', self.clock, this_event.machine, this_event.machine, this_event.operator, this_job)
                self.add_event(next_event)
            elif this_event.place == self.queue_2:
                self.queue_2.Remove_Job(this_job)
                #schedule next
                next_event = toolbox.Event('Job {} start setup at {}'.format(this_job.name, this_event.machine.name), 'Start_Setup', self.clock, this_event.machine, this_event.machine, this_event.operator, this_job)
                self.add_event(next_event)
            elif this_event.place == self.queue_3:
                self.queue_3.Remove_Job(this_job)
                #schedule next
                next_event = toolbox.Event('Job {} start QC'.format(this_job.name), 'Start_QC', self.clock, self.QC_machine, self.QC_machine, None, this_job)
                self.add_event(next_event)
        
        elif this_event.e_type == 'Start_Setup':
            this_job = this_event.job
            #process event
            this_job.place = this_event.machine
            this_event.machine.Start_Setup(this_job, this_event.operator)
            setup_duration = np.random.randint(1, 3)
            #schedule next
            next_event = toolbox.Event('Job {} end setup at {}'.format(this_job.name, this_event.machine.name), 'End_Setup', self.clock+setup_duration, this_event.machine, this_event.machine, None, this_job)
            self.add_event(next_event)
        
        elif this_event.e_type == 'End_Setup':
            this_job = this_event.job
            #process event
            this_event.machine.End_Setup()
            self.Operator_look_for_next_job_in_opr_queue(this_event.machine.operator)
            this_event.machine.operator = None
            #schedule next
            if this_event.machine.m_type == 'Harvesting':
                next_event = toolbox.Event('Job {} start harvesting at {}'.format(this_job.name, this_event.machine.name), 'Start_Harvesting', self.clock, this_event.place, this_event.machine, None, this_job)
            elif this_event.machine.m_type == 'Processing':
                next_event = toolbox.Event('Job {} start processing at {}'.format(this_job.name, this_event.machine.name), 'Start_Processing', self.clock, this_event.place, this_event.machine, None, this_job)
            self.add_event(next_event)
            
        elif this_event.e_type == 'Start_Harvesting':
            this_job = this_event.job
            #process event
            this_event.machine.Start_Work()
            harvest_duration = np.random.randint(6, 9)
            harvesting_yield = this_job.patients_target_bc * 0.8
            this_job.harvesting_yield= harvesting_yield
            #schedule next
            next_event = toolbox.Event('Job {} end harvesting at {}'.format(this_job.name, this_event.machine.name), 'End_Harvesting', self.clock+harvest_duration, this_event.place, this_event.machine, None, this_job)
            self.add_event(next_event)
            
        elif this_event.e_type == 'End_Harvesting':
            this_job = this_event.job
            #process event
            this_event.machine.End_Work()
            #schedule next
            next_event = toolbox.Event('Patient {} arrival at {}'.format(this_job.name, self.queue_2.name), 'Arrival', self.clock, self.queue_2, None, None, this_job)
            self.add_event(next_event)
            #look for next job in queue
            self.Machine_look_for_next_job_in_queue(this_event.machine)
            
            this_event.machine.job = None
        
        elif this_event.e_type == 'Start_Processing':
            this_job = this_event.job
            #process event
            this_event.machine.Start_Work()
            this_job.start_processing_time = self.clock
            target_bc = this_job.patients_target_bc
            t_low = target_bc/self.low_slope
            t_up = t_low + self.delta_t
            t_zero = t_up + target_bc/self.up_slope
            #processing_duration = random.choices(self.mfg_dura, weights = self.mfg_dura_perc)[0]
            processing_duration = random.choices([np.random.uniform(0,t_low), np.random.uniform(t_low,t_up), np.random.uniform(t_up,t_zero+4)], weights = self.mfg_dura_perc)[0]
            processing_duration_in_hours = processing_duration*24
            p_yield = self.Processing_yield_curve(processing_duration, this_job)
            this_job.processing_yield = p_yield
            #schedule next
            next_event = toolbox.Event('Job {} end processing at {}'.format(this_job.name, this_event.machine.name), 'End_Processing', self.clock+processing_duration_in_hours, this_event.place, this_event.machine, None, this_job)
            self.add_event(next_event)
            
            
        elif this_event.e_type == 'End_Processing':
            this_job = this_event.job
            #process event
            this_event.machine.End_Work()
            #schedule next
            if self.get_available_operator('Processing') != []:
                chosen_operator= random.choice(self.get_available_operator('Processing'))
                this_event.machine.operator = chosen_operator
                next_event = toolbox.Event('Collect Job {}'.format(this_job.name), 'Collect', self.clock, this_event.place, this_event.machine, chosen_operator, this_job)
                self.add_event(next_event)
            else:
                self.queue_5.Add_Job(this_job)
            
        elif this_event.e_type == 'Collect':
            this_job = this_event.job
            #process event
            if this_job.processing_yield <= 0:
                this_job.Start_rework(self.clock)
                #look for next job in queue
                self.Machine_look_for_next_job_in_queue(this_event.machine)
                self.Operator_look_for_next_job_in_opr_queue(this_event.operator)
                next_event = toolbox.Event('Patient {} arrival at {} (Rework)'.format(this_job.name, self.queue_1.name), 'Arrival', self.clock, self.queue_1, None, None, this_job)
            else:
                duration = self.clock - this_job.start_processing_time
                final_yield = self.Processing_yield_curve(duration/24, this_job)
                this_job.processing_yield = final_yield
                this_event.machine.state = 'Idle'
                this_event.machine.operator.state = 'Idle'
                #look for next job in queue
                self.Machine_look_for_next_job_in_queue(this_event.machine)
                self.Operator_look_for_next_job_in_opr_queue(this_event.operator)
                this_event.machine.job = None
                this_event.machine.operator = None
                next_event = toolbox.Event('Patient {} arrival at {}'.format(this_job.name, self.queue_3.name), 'Arrival', self.clock, self.queue_3, None, None, this_job)
            self.add_event(next_event)
            
        elif this_event.e_type == 'Start_QC':
            this_job = this_event.job
            #process event
            this_job.place = self.QC_machine
            res = self.quality_policy(self.QM_Policy_MFG, this_job)
            QC_dura = 0.5
            if res == "Sample Rejected":
                if this_job.rework_count <= self.max_rework_times:
                    this_job.Start_rework(self.clock)
                    next_event = toolbox.Event('Patient {} arrival at {} (Rework)'.format(this_job.name, self.queue_1.name), 'Arrival', self.clock+QC_dura, self.queue_1, None, None, this_job)
                else:
                    this_job.place = self.Finish_stack
                    self.finish_list.append(this_job)
                    this_job.state = 'Fail'
            else:
                next_event = toolbox.Event('Job {} end QC'.format(this_job.name), 'End_QC', self.clock+QC_dura, self.Finish_stack, self.Finish_stack, None, this_job)
            self.add_event(next_event)
            
        elif this_event.e_type == 'End_QC':
            this_job = this_event.job
            #process event
            this_job.place = self.Finish_stack
            this_job.Leave_sys(self.clock)
            self.finish_list.append(this_job)
            this_job.state = 'Finish'
            

#Testing policy
    def high_fidelity_test_case_A(self):
        P_1_HF = 0.99   #P(Ytilda >= Y* / Y' >= Y*) #P(viable/Test = Positive)
        P_2_HF = 0.10   #P(Ytilda >= Y* / Y' < Y*)  #P(viable/Test = Negative)
        P_3_HF = 0.65   #P(Y' >= Y*) #P(Measured Yield < Expected Yield)

        #calculating P(Y'>= Y* / Ytilda>= Y*) 
        #i.e. proability of measured yield being more than expected yield given calculated yield is more than expected
        #P(Y'>= Y* / Ytilda>= Y*)  = P(Ytilda >= Y* / Y' >= Y*) * P(Y' >= Y*) / [P(Ytilda >= Y* / Y' >= Y*) * P(Y' >= Y*) + P(Ytilda >= Y* / Y' < Y*) * P(Y' < Y*)]
        alpha_HF = 0.95#(P_1_HF * P_3_HF) / (P_1_HF * P_3_HF + P_2_HF * (1 - P_3_HF))  = 0.6785
        U1 = np.random.uniform(0, 1)
        if (U1 <= alpha_HF):
            Test_Result = 'Sample Passed'
        else:
            Test_Result = 'Sample Rejected'
        return Test_Result
        
    def high_fidelity_test_case_B(self):
        P_1_HF = 0.99   #P(Ytilda >= Y* / Y' >= Y*) #P(viable/Test = Positive)
        P_2_HF = 0.10   #P(Ytilda >= Y* / Y' < Y*)  #P(viable/Test = Negative)
        P_3_HF = 0.65   #P(Y' >= Y*) #P(Measured Yield < Expected Yield)
        Beta_HF = 0.9#((1-P_1_HF)* P_3_HF) / (((1-P_1_HF)* P_3_HF) + ((1-P_2_HF)*(1-P_3_HF))) =  0.02021772
        U2 = np.random.uniform(0, 1) 
        if (U2 <= Beta_HF):
            Test_Result = 'Sample Passed'    #It was fail, but Test confirms Pass
        else:
            Test_Result = 'Sample Rejected'  #It was fail, Test Confirms Fail
        return Test_Result

    def low_fidelity_test_case_A(self):
        P_1_LF = 0.85   #P(Ytilda >= Y* / Y' >= Y*) #P(viable/Test = Positive)
        P_2_LF = 0.45   #P(Ytilda >= Y* / Y' < Y*)  #P(viable/Test = Negative)
        P_3_LF = 0.40   #P(Y' >= Y*) #P(Measured Yield < Expected Yield)
        #calculating P(Y'>= Y* / Ytilda < Y*)
        alpha_LF = 0.9#(P_1_LF * P_3_LF) / (P_1_LF * P_3_LF + P_2_LF * (1 - P_3_LF)) = 0.55737704
        U3 = np.random.uniform(0, 1)
        if (U3 <= alpha_LF):
            Test_Result = 'Sample Passed'
        else:
            Test_Result = 'Sample Rejected'
        return Test_Result

    def low_fidelity_test_case_B(self):
        P_1_LF = 0.85   #P(Ytilda >= Y* / Y' >= Y*) #P(viable/Test = Positive)
        P_2_LF = 0.45   #P(Ytilda >= Y* / Y' < Y*)  #P(viable/Test = Negative)
        P_3_LF = 0.40   #P(Y' >= Y*) #P(Measured Yield < Expected Yield)
        Beta_LF = 0.95#((1-P_1_LF)* P_3_LF) / (((1-P_1_LF)* P_3_LF) + ((1-P_2_LF)*(1-P_3_LF))) = 0.15384615
        U4 = np.random.uniform(0, 1)
        if (U4 <= Beta_LF):
            Test_Result = 'Sample Passed'    #It was fail, but Test confirms Pass
        else:
            Test_Result = 'Sample Rejected'  #It was fail, Test Confirms Fail
        return Test_Result


    def quality_policy(self, QM_Policy_MFG, job):

        #defining level for each quality control policy
        #Test happens according to that level and the results are recorded
        Test_Result='Default result'
        process_yield = job.processing_yield
        patients_target_bc =job.patients_target_bc
        if QM_Policy_MFG == 0:
            #test everything in high fidelity
            #Case A
            if (process_yield >= patients_target_bc):
                Test_Result=self.high_fidelity_test_case_A()
            #Case B
            else:
                Test_Result=self.high_fidelity_test_case_B()
        elif QM_Policy_MFG == 1:
            #test everything in low fidelity and if test fails then check again in high fidelity
            #Case A
            if (process_yield >= patients_target_bc):
                Test_Result = self.low_fidelity_test_case_A() 
                if Test_Result == "Sample Rejected":
                    Test_Result = self.high_fidelity_test_case_A()
                    if Test_Result == "Sample Rejected":
                        Test_Result = "Rejected in LF and HF Both"
                    else:
                        Test_Result = "Rejected in LF but Passed in HF"
            #Case B
            else:
                Test_Result= self.low_fidelity_test_case_B()
                if Test_Result == "Sample Rejected":
                    Test_Result = self.high_fidelity_test_case_B()
                    if Test_Result == "Sample Rejected":
                        Test_Result = "Rejected in LF and HF Both"
                    else:
                        Test_Result = "Rejected in LF, Passed in HF"
        else:
            U5 = np.random.uniform(0, 1)
            if (U5 <= 0.70):
                if (process_yield >= patients_target_bc):
                    Test_Result=self.high_fidelity_test_case_A()
                else:
                    Test_Result=self.high_fidelity_test_case_B()
            else:
                Test_Result= "Proceeding Sample without contamination"
                
        return Test_Result



#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#[System mix, Patient mix, QM Policy, Hrv Operator, Hrv Machines, Mfg Operators, Mfg Machines]
def translate_into_design(item):
    res = int(''.join(filter(str.isdigit, item))) -1
    return res
    
design_file = 'Design_enumerate.csv'
df_design = pd.read_csv(design_file)
#for row in range(0,1):
for row in range(0,len(df_design)):
    Design = []
    for col in range(0,7):
        res = translate_into_design(df_design.iloc[row, col])
        Design.append(res)
    group_num = row
    Env = Environment(Design, group_num)
    df_this_design = Env.Simulate()
#df_this_design.to_csv('Events_info.csv')