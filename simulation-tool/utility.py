#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:00:49 2020
@author:

Goutam Krishna Reddy Sagam
Srikanth Ammineni
Madhumitha Sivasankaran
Shubhangi Mane

"""
import json
import math
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import mplcursors
import os
import shutil
from matplotlib import style
from pprint import pprint


#Function to read json input files
def read_json(path):
    f = open(path)
    data = json.load(f) 
    temp = {}
    for i in range(len(data)):
        temp[data[i]['id']] = data[i]
    f.close()
    return temp
    
    

#Function to read workload input file
def input_workload(filepath):   
     workloads=read_json(filepath)
     dict={}
     for workload in workloads.keys():
         for i in workloads[workload]["requests"]:
             if workload not in dict:
                 dict[workload]={}
             if int(i["time"]) not in dict[workload]:
                dict[workload][int(i["time"])]=i["request_id"]
     return dict
 
    
#Function to calculate time to transfer asset based on throughput
def timeToTransfer(size, throughput):
    #return time in milli seconds
    time = (size/throughput)*1000
    return math.ceil(time)

plt.style.use('ggplot')


#function for dynamic plots
def live_plotter(x_vec,y1_data,line1,xlabel,ylabel,title,xlim,ylim,identifier='',pause_time=0.01):
    if line1==[]:
        plt.ion()
        fig = plt.figure(figsize=(5,4))
        ax = fig.add_subplot(111)
        ax.set_xlim(0, xlim+1)
        ax.set_ylim(0, ylim)

        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8,) 
    
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        mplcursors.cursor(hover=True)
    line1.set_data(x_vec, y1_data)
    plt.pause(pause_time) 
    return line1


#Function to choose cacheserver based on the distance matrix
def assignCacheServer(clients_ip, client):
    distances = clients_ip[client]['distance']
    
    distance_arr = [(distances[x],x) for x in distances]
    distance_arr.sort(key = lambda x: x[0])
    return distance_arr


#Function to build Cacheserver Status
def build_cacheServer_status(cacheServer_status, cacheServer,cacheServer_ip):
    if cacheServer in cacheServer_status:
        return cacheServer_status
    else:
        cacheServer_status[cacheServer]['cache_hit'] = 0
        cacheServer_status[cacheServer]['cache_miss'] = 0
        cacheServer_status[cacheServer]['active_inbound_connections'] = 0
        cacheServer_status[cacheServer]['active_outbound_connections'] = 0
        cacheServer_status[cacheServer]['input_throughput_used'] = 0
        cacheServer_status[cacheServer]['output_throughput_used'] = 0
        cacheServer_status[cacheServer]['input_throughput_available'] = int(cacheServer_ip[cacheServer]["max_input_throughput"])
        cacheServer_status[cacheServer]['output_throughput_available'] = int(cacheServer_ip[cacheServer]["max_output_throughput"])
        return cacheServer_status
 
    
#Function to build Request Status    
def build_request_status(req_status,req,t,requests_ip,assets_ip):   
        
    
        req_status[req] = {}
        req_status[req][t] = "started"
        req_status[req]['initiated_at'] = t        
        req_status[req]['stage'] = 0
        req_status[req]['completed'] = 0
        req_status[req]['client'] = requests_ip[req]['client']
        req_status[req]['origin'] = requests_ip[req]['origin']
        req_status[req]['asset'] = requests_ip[req]['asset']
        asset=requests_ip[req]['asset']
        req_status[req]['asset_size']= assets_ip[asset]['size']
        req_status[req]['input_throughput_being_used'] = {}
        req_status[req]['input_throughput_being_used']['client'] = 0
        req_status[req]['input_throughput_being_used']['cacheServer'] = 0
        req_status[req]['output_throughput_being_used'] = {}
        req_status[req]['output_throughput_being_used']['origin'] = 0
        req_status[req]['output_throughput_being_used']['cacheServer'] = 0
        req_status[req]['timeout_count'] = 0
        
        
        return req_status

def sortKeys(req_status):
    temp_key1 = []
    for r in req_status.keys():
        if req_status[r]['completed'] == 0:
            v1 = req_status[r].get('adtc1',0)
            v2 = req_status[r].get('adtc',0)
            if v1 != 0:
                temp_key1.append((v1,r))
            elif v2 !=0:
                temp_key1.append((v2,r))
            else:
                temp_key1.append((0,r))
                
    temp_key1.sort(key = lambda x : x[0])      
    fin_keys = [i[1] for i in temp_key1] 
    return fin_keys
        
#Function to capture System State
def CaptureSystemState(snapshot_time,simulation_ip,workload_ip,req_status,cacheServer_status,workloads):  
    simulation_output={}
    simulation_output['tick_duration']=int(simulation_ip['simulation1']['tick_duration'])
    simulation_output['snapshot_time']=snapshot_time
    simulation_output['workload']=simulation_ip['simulation1']['workload']
    simulation_output['number_of_requests_completed']=0
    simulation_output['total_data_transferred']=0
    for req in req_status.keys():
        if req_status[req]['completed']==1:
            simulation_output['number_of_requests_completed']+=1
            simulation_output['total_data_transferred']+=req_status[req]['asset_size']
        else:
            if "size_transferred_to_client" in req_status[req].keys() and snapshot_time in req_status[req]["size_transferred_to_client"].keys():
                simulation_output['total_data_transferred']+=req_status[req]["size_transferred_to_client"][snapshot_time]
    simulation_output['total_data_transferred']=simulation_output['total_data_transferred']
    
    simulation_output['requests_status']={}
    for req in req_status.keys():
        req_status_dict={}
        req_status_dict["initiated_at"]=req_status[req]['initiated_at']
        req_status_dict["client"]=req_status[req]["client"]
        req_status_dict["origin"]=req_status[req]["origin"]
        req_status_dict["asset"]=req_status[req]["asset"]
        req_status_dict["asset_size"]=req_status[req]['asset_size']
        #pprint(req_status)
        req_status_dict["cacheserver"]=req_status[req]['cacheServer']
        req_status_dict["status"]=req_status[req].get(snapshot_time,"Request already processed")
        req_status_dict["input_throughput_being_used"]=req_status[req]['input_throughput_being_used']
        req_status_dict["output_throughput_being_used"]=req_status[req]['output_throughput_being_used']
        #print(snapshot_time)
        #print(req_status[req])
        if "size_transferred_to_cache" in req_status[req].keys() and snapshot_time in req_status[req]["size_transferred_to_cache"].keys():
            req_status_dict["size_transferred_to_cache"]=req_status[req]["size_transferred_to_cache"][snapshot_time]
        if "size_transferred_to_client" in req_status[req].keys() and snapshot_time in req_status[req]["size_transferred_to_client"].keys():
            req_status_dict["size_transferred_to_client"]=req_status[req]["size_transferred_to_client"][snapshot_time]
        if req_status[req]['completed']==0: 
            req_status_dict["completed"]="No"
        else:
            req_status_dict["completed"]="Yes"
            req_status_dict["completed_at"]=req_status[req]['completed_at']
        simulation_output['requests_status'][req]=req_status_dict
        
    simulation_output['cacheserver_status']={}
    for cacheserver in cacheServer_status.keys():
        cs_status_dict={}
        cs_status_dict["cache_hit"]=cacheServer_status[cacheserver]["cache_hit"]
        cs_status_dict["cache_miss"]=cacheServer_status[cacheserver]["cache_miss"]
        cs_status_dict["input_throughput_being_used"]=cacheServer_status[cacheserver]["input_throughput_used"]
        cs_status_dict["output_throughput_being_used"]=cacheServer_status[cacheserver]["output_throughput_used"]
        cs_status_dict["input_throughput_available"]=cacheServer_status[cacheserver]["input_throughput_available"]
        cs_status_dict["output_throughput_available"]=cacheServer_status[cacheserver]["output_throughput_available"]
        cs_status_dict["number_of_active_inbound_connections"]=cacheServer_status[cacheserver]["active_inbound_connections"]
        cs_status_dict["number_of_active_outbound_connections"]=cacheServer_status[cacheserver]["active_outbound_connections"]
        cs_status_dict['total_data_transferred']=0
        for req in req_status.keys():
            if req_status[req]["cacheServer"]==cacheserver:
                if req_status[req]['completed']==1:
                    cs_status_dict['total_data_transferred']+=req_status[req]['asset_size']
                else:
                    if "size_transferred_to_client" in req_status[req].keys() and snapshot_time in req_status[req]["size_transferred_to_client"].keys():
                        cs_status_dict['total_data_transferred']+=req_status[req]["size_transferred_to_client"][snapshot_time]
        simulation_output['cacheserver_status'][cacheserver]=cs_status_dict
        
    return simulation_output

#function to create 'output' folder
def makedirectory(simulation_ip,cacheServer_ip):
    dir = 'output'
    if not os.path.exists(dir):
        os.makedirs(dir)
    workload=simulation_ip["simulation1"]["workload"]
    dir='output/'+workload
    if os.path.exists(dir): 
        shutil.rmtree('output/'+workload)
    os.makedirs('output/'+workload)
    dir1='output/'+workload+'/visualization' 
    if not os.path.exists(dir1):
        os.makedirs('output/'+workload+'/visualization')
    if not os.path.exists('output/'+workload+'/visualization'+'/simulation'):
        os.makedirs('output/'+workload+'/visualization'+'/simulation')
    for cs in cacheServer_ip.keys():
        dir='output/'+workload+'/visualization'+'/'+cs
        if not os.path.exists(dir):
            os.makedirs(dir)
    dir2='output/'+workload+'/system_state'
    if not os.path.exists(dir2):
        os.makedirs('output/'+workload+'/system_state')                
    return workload

#function for capturing and storing static plots
def visualize(x,y,z,xlabel,ylabel,title,cs,xlim,ylim,workload,label1=None,label2=None):
    style.use('ggplot')
    ax = plt.figure().gca()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, ylim)         
    if z:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True)) 
        ax.plot(x,y,alpha=0.8,label=label1)
        ax.plot(x,z,alpha=0.8,label=label2)
        plt.legend()
        plt.savefig('output/'+workload+'/visualization/'+cs+'/%s.png' %title)
        plt.close()
       
    else:            
        ax.yaxis.set_major_locator(MaxNLocator(integer=True)) 
        ax.plot(x,y,alpha=0.8)
        plt.savefig('output/'+workload+'/visualization/'+cs+'/%s.png' %title)
        plt.close()

        
    matplotlib.use('Agg')