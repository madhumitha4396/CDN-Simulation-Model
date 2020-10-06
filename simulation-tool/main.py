#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 22:57:24 2020

@authors: 
    
Goutam Krishna Reddy Sagam
Srikanth Ammineni
Madhumitha Sivasankaran
Shubhangi Mane

This is the python code for CDN simulation tool where one can model 
different cache configurations allowing us to test cache server behaviour as in the real world.
"""

'''
ENDPOINTS
tctc - tcp connection time cache
cct - cache check time
tcto  - tcp connection time origin
adtc - asset deliver time from cache
oct -  asset check time by origin
adto - asset deliver time from origin
end - if end is 1 then request is processed and asset is delivered 
'''

#Importing necessary libraries
import utility
import collections
from pprint import pprint
import sys
import os
import json
from utility import live_plotter

#Initializing dictionaries that stores request, simulation and throughput status
req_status = collections.defaultdict(dict)
sim_status = collections.defaultdict(dict)
throughput_status = collections.defaultdict(dict)

#stores time at which client or cache server is using throughput
throughput_status_time = collections.defaultdict(dict)

#stores cache server status
cacheServer_status = collections.defaultdict(dict)



def simulation(t,requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip):
    """
    This function handles the core of the simulation. 
    
    ---Parameters to be passed---
    t - time
    requests_ip - request objects
    simulation_ip - Simulation objects
    workload_ip - Workload objects
    cacheserver_ip - Cacheserver objects
    assets_ip - Asset objects
    clients_ip - Client objects
    origin_ip - Origin objects
    """
    
    #handle new requests
    if t in workload_ip.keys():
        new_req = workload_ip[t] 
        for req in new_req:

            global req_status
            #Create entry for each new request in req_status dict
            req_status = utility.build_request_status(req_status,req,t, requests_ip,assets_ip)
            req_status[req]['tctc'] = t + int(simulation_ip['simulation1']['tcp_connection_time'])

            global sorted_cacheserver_list,cacheServer_used
            #Create a sorted listed based on the proximity of the Cache servers to each client and choose the nearest one
            sorted_cacheserver_list=utility.assignCacheServer(clients_ip, requests_ip[req]['client'] )
            cacheServer_used = sorted_cacheserver_list[0][1]
    
            global cacheServer_status
            #Create entry for the Cache server in cacheServer_Status dict
            cacheServer_status = utility.build_cacheServer_status(cacheServer_status, cacheServer_used,cacheServer_ip)
            
    #handle started requests    
    if req_status:
        #process requests based on their finish time.
        sorted_keys = utility.sortKeys(req_status)
        for req in sorted_keys:   
            
            #Check if the request is completed
            if req_status[req]['completed'] == 0:       
                #Stage -0 - Initial stage. Establishing TCP connection between Client and Cacheserver 
                if req_status[req]['stage'] ==  0:
                    
                    #if current time less than the tcp connection time to cache Server
                    if t < req_status[req]['tctc']:
                        req_status[req][t] = 'Establishing TCP connection to cache server'
                        sorted_cacheserver_list=utility.assignCacheServer(clients_ip, requests_ip[req]['client']) 
                        req_status[req]['cacheServer']=sorted_cacheserver_list[0][1]
                        continue
                    #if current time qual to the tcp connection time to cache Server
                    elif t == req_status[req]['tctc']:
                        max_connections_client = clients_ip[requests_ip[req]['client']]['max_connections']
                        flag = False
                        sorted_cacheserver_list=utility.assignCacheServer(clients_ip, requests_ip[req]['client'])  

                        #To find the nearest Cache server that has available connections and throughput
                        for cs in range(0,len(sorted_cacheserver_list)):
                            max_connections_cache = cacheServer_ip[sorted_cacheserver_list[cs][1]]["max_connections"]                       
                            cacheServer_status = utility.build_cacheServer_status(cacheServer_status, sorted_cacheserver_list[cs][1],cacheServer_ip)
                            
                            #check throughput 
                            throughput_limit = cacheServer_ip[sorted_cacheserver_list[cs][1]]["throughput_limit"]
                            tcache = sorted_cacheserver_list[cs][1]
                            cache_throughput = int(cacheServer_ip[sorted_cacheserver_list[cs][1]]['max_output_throughput'])
                            if t in throughput_status_time[tcache]:
                                n = throughput_status_time[tcache].get(t) +1
                            else:
                                if 'old' in throughput_status_time[tcache]:
                                    n =throughput_status_time[tcache][throughput_status_time[tcache]['old']] +1
                                else:
                                    n = 1
                            throughput_avail  = cache_throughput/n
                            
                            #check connections
                            if (cacheServer_status[sorted_cacheserver_list[cs][1]]['active_inbound_connections'] + cacheServer_status[sorted_cacheserver_list[cs][1]]['active_outbound_connections'] < max_connections_cache) and (sim_status['connections_client'][requests_ip[req]['client']] < max_connections_client) and (throughput_avail > throughput_limit) :                                  
                                    cacheServer_used=sorted_cacheserver_list[cs][1]
                                    flag=True
                                    req_status[req]['cacheServer'] = cacheServer_used
                                    req_status[req]['cct'] = t + int(cacheServer_ip[req_status[req]['cacheServer']]["time_to_check_cache"])
                                    # start using throughput at
                                    new_t = t + int(cacheServer_ip[req_status[req]['cacheServer']]["time_to_check_cache"])
                                    #Check if asset present in Cache
                                    if requests_ip[req]['asset'] in cacheServer_ip[req_status[req]['cacheServer']]['cached_assets_id']:
                                        client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                        if len(throughput_status_time[client_id]) == 0:
                                            throughput_status_time[client_id][new_t] =throughput_status_time[client_id].get(new_t,0) +  1
                                            throughput_status_time[client_id]['old'] = new_t
                                        else:
                                            if throughput_status_time[client_id]['old'] > new_t:
                                                throughput_status_time[client_id]['old'] = new_t
                                            req_count = 1
                                            for key in throughput_status_time[client_id]:
                                                if key != 'old' and key != 'temp_adto' and key <= new_t:
                                                    req_count += throughput_status_time[client_id][key]
                                                if key != 'old' and key != 'temp_adto' and key > new_t:
                                                    throughput_status_time[client_id][key] +=1
                                            throughput_status_time[client_id][new_t] = req_count
                                            
                                        if len(throughput_status_time[cacheServer_used]) == 0:
                                            throughput_status_time[cacheServer_used][new_t] =throughput_status_time[cacheServer_used].get(new_t,0) +  1
                                            throughput_status_time[cacheServer_used]['old'] = new_t
                                           
                                        else:
                                            if throughput_status_time[cacheServer_used]['old'] > new_t:
                                                throughput_status_time[cacheServer_used]['old'] = new_t
                                            req_count = 1
                                            for key in throughput_status_time[cacheServer_used]:
                                                if key != 'old' and key != 'temp_adto' and key <= new_t:
                                                    req_count += throughput_status_time[cacheServer_used][key]
                                                if key != 'old' and key != 'temp_adto' and key > new_t:
                                                    throughput_status_time[cacheServer_used][key] +=1
                                            throughput_status_time[cacheServer_used][new_t] = req_count
                                        
                                    req_status[req]['stage'] = 1
                    
                                    cacheServer_status[req_status[req]['cacheServer']]['active_inbound_connections'] +=1
                                    sim_status['connections_client'][requests_ip[req]['client']] += 1
                                    break
                        
                        #When connections are not available, wait till timeout, abort if timeout is exceeded
                        if(flag==False):
                            req_status[req]['tctc'] += 1
                            req_status[req][t]="Max connections reached. Waiting until connections are available" 
                            req_status[req]['timeout_count'] +=1
                            if req_status[req]['timeout_count'] == simulation_ip['simulation1']['timeout']:
                                req_status[req]['completed'] = 1
                                req_status[req]['completed_at'] = t
                                req_status[req][t]= "Request time out"
                                
                            continue
                #Stage -1 - Checking the asset in Cache
                if req_status[req]['stage'] ==  1:
                    if t < req_status[req]['cct']:
                        req_status[req]['timeout_count'] = 0
                        if t not in req_status[req].keys():
                            req_status[req][t] = 'Checking for the requested asset in Cache'
                        else:
                            req_status[req][t] = 'TCP connection established between Client and Cacheserver. Checking for the requested asset in Cache'
                        continue
                    elif t == req_status[req]['cct']:
                        #check if cache present in cache server 
                        if requests_ip[req]['asset'] in cacheServer_ip[req_status[req]['cacheServer']]['cached_assets_id']:
                            req_status[req][t] = 'Requested asset present in cache'
                            #check throughput and calculate endpoint to transfer asset to client
                            req_asset_id = requests_ip[req]['asset']
                            asset_size = int(assets_ip[req_asset_id]['size'])
                            cache_throughput = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput'])
                            client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                            #check available throughput-- 
                            available_throughput = min(cache_throughput,client_throughput)
                            time_taken = utility.timeToTransfer(asset_size,available_throughput)
                            req_status[req]['adtc'] = t + time_taken
                            req_status[req]['size_transferred_to_client'] = {}
                            req_status[req]['size_transferred_to_client'][t] = 0
                            cacheServer_status[req_status[req]['cacheServer']]['cache_hit'] += 1 
                            req_status[req]['stage'] = 2
                                                       
                        else:
                            req_status[req][t] = 'Requested asset not present in cache'
                            #add tcp endpoint to origin
                            req_status[req]['tcto'] = t + int(simulation_ip['simulation1']['tcp_connection_time'])
                            cacheServer_status[req_status[req]['cacheServer']]['cache_miss'] += 1 
                            req_status[req]['stage'] = 3
                    
                #Stage-2 - Transferring Asset to client if asset found in Cache
                if req_status[req]['stage'] ==  2:
                    if t < req_status[req]['adtc']:
                                                                 
                        client_id = (clients_ip[requests_ip[req]['client']]['id'])
                        cacheServer_used = req_status[req]['cacheServer']
                        req_asset_id = requests_ip[req]['asset']
                        asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_transferred_to_client'].get(t,0)
                        cache_throughput = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput'])
                        client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                            #check available throughput-- 
                        available_throughput = min(cache_throughput,client_throughput)
                        te = throughput_status_time[client_id]['old']
                        if t in throughput_status_time[client_id]:
                            n1 = throughput_status_time[client_id].get(t)
                            throughput_status_time[client_id]['old'] = t
                        else:
                            n1 = throughput_status_time[client_id][te]
                            
                        te1 = throughput_status_time[cacheServer_used]['old']
                        if t in throughput_status_time[cacheServer_used]:
                            n2 = throughput_status_time[cacheServer_used].get(t)
                            throughput_status_time[cacheServer_used]['old'] = t
                        else:
                            n2 = throughput_status_time[cacheServer_used][te1]
                            
                            
                        n = max(n1,n2)
                        throughput_to_use = available_throughput/n
                        
                        #update throughput status for cacheserver and client
                        req_status[req]['input_throughput_being_used']['client'] = throughput_to_use
                        req_status[req]['output_throughput_being_used']['cacheServer'] = throughput_to_use
                        cacheServer_status[req_status[req]['cacheServer']]['output_throughput_used'] = throughput_to_use
                        cacheServer_status[req_status[req]['cacheServer']]['output_throughput_available'] = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput']) - throughput_to_use
                        time_taken = utility.timeToTransfer(asset_size,throughput_to_use)
                        transfer_pertick = asset_size / time_taken
                        req_status[req]['size_transferred_to_client'][t+1] = req_status[req]['size_transferred_to_client'][t]  + transfer_pertick
                        req_status[req]['adtc'] = t + time_taken 
                        if t not in req_status[req].keys():
                            req_status[req][t] = 'Transferring asset to client'
                        else:
                            req_status[req][t] = 'Asset found in cache. Transferring asset to client'
                        continue
                    elif t == req_status[req]['adtc']:
                        req_status[req][t] = 'Asset transferred to client'
                        #updating the inbound connections after the asset is transfered
                        cacheServer_status[req_status[req]['cacheServer']]['active_inbound_connections'] -= 1
                        sim_status['connections_client'][requests_ip[req]['client']] -= 1
                        client_id = (clients_ip[requests_ip[req]['client']]['id'])  
                        cacheServer_used = req_status[req]['cacheServer']
                        for key in throughput_status_time[client_id]:
                            if key != 'old' and key != 'temp_adto':
                                if throughput_status_time[client_id][key] > 1:
                                    throughput_status_time[client_id][key] -=1     
                                else:
                                    throughput_status_time[client_id][key] = 0
                                    
                        for key in throughput_status_time[cacheServer_used]:
                            if key != 'old' and key != 'temp_adto':
                                if throughput_status_time[cacheServer_used][key] > 1:
                                    throughput_status_time[cacheServer_used][key] -=1     
                                else:
                                    throughput_status_time[cacheServer_used][key] = 0
                        req_status[req]['completed'] = 1
                        req_status[req]['input_throughput_being_used']['client'] = 0
                        req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                        req_status[req]['output_throughput_being_used']['origin'] = 0
                        req_status[req]['output_throughput_being_used']['cacheServer'] = 0
                        req_status[req]['completed_at']=t
                #establishing connection to origin
                if req_status[req]['stage'] >=  3:
                    #Stage-3 - Establishing TCP connection between Client and Origin if asset not found in Cache
                    if req_status[req]['stage'] == 3:
                        if t < req_status[req]['tcto']:
                            req_status[req][t] = 'Establishing TCP connection to Origin'
                            continue
                        elif t == req_status[req]['tcto']:
                            max_connections_cache = cacheServer_ip[req_status[req]['cacheServer']]["max_connections"]
                            #checking for available connections for origin, and cacheserver
                            if (sim_status['connections_origin'][requests_ip[req]['origin']] < int(origin_ip[requests_ip[req]['origin']]["max_connections"]) and (cacheServer_status[req_status[req]['cacheServer']]['active_inbound_connections'] + cacheServer_status[req_status[req]['cacheServer']]['active_outbound_connections'] < max_connections_cache)):
                                sim_status['connections_origin'][requests_ip[req]['origin']] += 1
                                sim_status['outbound_connections_cacheServer'] +=1
                                cacheServer_status[req_status[req]['cacheServer']]['active_outbound_connections'] += 1
                                req_status[req][t] = 'tcp connection established to origin server'
                                req_status[req]['oct'] = t + int(origin_ip[requests_ip[req]['origin']]['asset_check_time'])
                                req_status[req]['stage'] = 4
                                new_t = t + int(origin_ip[requests_ip[req]['origin']]['asset_check_time'])
                                cacheServer_id = req_status[req]['cacheServer']
                                if len(throughput_status_time[cacheServer_id]) == 0:                                
                                    throughput_status_time[cacheServer_id][new_t] =throughput_status_time[cacheServer_id].get(new_t,0) +  1
                                    throughput_status_time[cacheServer_id]['old'] = new_t                                    
                                else:                                                              
                                    req_count = 1
                                    for key in throughput_status_time[cacheServer_id]:
                                        if key != 'old':
                                            req_count += throughput_status_time[cacheServer_id][key]
                                    throughput_status_time[cacheServer_id][new_t] = req_count  
                            else:
                                req_status[req]['tcto'] +=1
                                 #When connections are not available, wait till timeout, abort if timeout is exceeded
                                req_status[req][t]="Max connections reached. Waiting until connections are available"
                                req_status[req]['timeout_count'] +=1
                                if req_status[req]['timeout_count'] == simulation_ip['simulation1']['timeout']:
                                    req_status[req]['completed'] = 1
                                    req_status[req]['completed_at'] = t
                                    req_status[req][t]= "Request time out"
                                continue
                    #Stage-4 - Checking for the requested asset in Origin
                    elif req_status[req]['stage'] == 4 :     
                        if t < req_status[req]['oct']:
                            req_status[req][t] = 'Checking for the requested asset in Origin'
                            continue;
                        elif t == req_status[req]['oct']:
                            #checking for asset in origin
                            if requests_ip[req]['asset'] in origin_ip[requests_ip[req]['origin']]['assets']:
                                req_status[req][t] = 'Requested asset present in Origin server'
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])
                                cache_throughput1 = int(cacheServer_ip[req_status[req]['cacheServer']]['max_input_throughput'])
                                origin_throughput = int(origin_ip[requests_ip[req]['origin']]['max_output_throughput'])

                                available_throughput1 = min(cache_throughput1,origin_throughput)
                                time_taken1 = utility.timeToTransfer(asset_size,available_throughput1)
                                req_status[req]['adto'] = t + time_taken1

                                new_t = t + time_taken1
                                client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                if len(throughput_status_time[client_id]) == 0:
                                    throughput_status_time[client_id][new_t] =throughput_status_time[client_id].get(new_t,0) +  1
                                    throughput_status_time[client_id]['old'] = new_t
                                else:
                                    req_count1 = 1
                                    for key in throughput_status_time[client_id]:
                                        if key != 'old' and key != 'temp_adto':
                                            req_count1 += throughput_status_time[client_id][key]
                                    throughput_status_time[client_id][new_t] = req_count1
                                throughput_status_time[client_id]['temp_adto'] = new_t
                                throughput_status_time['temp_adto'][req] = new_t
                                req_status[req]['size_transferred_to_cache'] = {}
                                req_status[req]['size_transferred_to_cache'][t] = 0
                            else:
                                  #updating the outbound connections of the cacheserver and inbound of origin
                                req_status[req][t] = 'Requested asset not present in Origin server'
                                sim_status['connections_origin'][requests_ip[req]['origin']] -=1
                                sim_status['outbound_connections_cacheServer'] -=1
                                cacheServer_status[req_status[req]['cacheServer']]['active_outbound_connections'] -= 1
                                req_status[req]['completed'] = 1
                                req_status[req]['completed_at'] = t
                        if 'adto' in req_status[req]:
                            if t < req_status[req]['adto']:
                                cacheServer_id = req_status[req]['cacheServer']
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_transferred_to_cache'].get(t,0)
                                cache_throughput1 = int(cacheServer_ip[req_status[req]['cacheServer']]['max_input_throughput'])
                                origin_throughput = int(origin_ip[requests_ip[req]['origin']]['max_output_throughput'])
                                    #check available throughput-- 
                                available_throughput1 = min(cache_throughput1,origin_throughput)
                                te = throughput_status_time[cacheServer_id]['old']
                                if t in throughput_status_time[cacheServer_id]:
                                    n = throughput_status_time[cacheServer_id].get(t)
                                    throughput_status_time[cacheServer_id]['old'] = t
                                    
                                else:
                                    n = throughput_status_time[cacheServer_id][te]
                                throughput_to_use1 = available_throughput1/n
                                req_status[req]['input_throughput_being_used']['cacheServer'] = throughput_to_use1
                                req_status[req]['output_throughput_being_used']['origin'] = throughput_to_use1
                                total_cs_throughput_use=0
                                for i in req_status.keys():
                                    total_cs_throughput_use+=req_status[i]['input_throughput_being_used']['cacheServer']
                                cacheServer_status[req_status[req]['cacheServer']]['input_throughput_used'] = total_cs_throughput_use
                                cacheServer_status[req_status[req]['cacheServer']]['input_throughput_available'] = int(cacheServer_ip[req_status[req]['cacheServer']]['max_input_throughput']) - throughput_to_use1
                                time_taken1 = utility.timeToTransfer(asset_size,throughput_to_use1)
                                transfer_pertick1 = asset_size / time_taken1

                                req_status[req]['size_transferred_to_cache'][t+1] = req_status[req]['size_transferred_to_cache'][t]  + transfer_pertick1
                                req_status[req]['adto'] = t + time_taken1

                                client_id = (clients_ip[requests_ip[req]['client']]['id'])
                                req_count1 = 1                                
                                if t+time_taken1 != throughput_status_time['temp_adto'][req]:

                                    del throughput_status_time[client_id][throughput_status_time['temp_adto'][req]]

                                    if t+time_taken1 not  in throughput_status_time[client_id]:
                                        for key in throughput_status_time[client_id]:
                                            if key != 'old' and  key != 'temp_adto' :
                                                req_count1 += throughput_status_time[client_id][key]
                                        throughput_status_time[client_id][t + time_taken1] = req_count1
                                    else:
                                        throughput_status_time[client_id][t + time_taken1] += req_count1
                                    throughput_status_time['temp_adto'][req] = t+time_taken1
                                
                                req_status[req][t] = 'Storing asset in Cache'
                                continue
                            elif t == req_status[req]['adto']:
                                req_status[req][t] = 'Asset transferred to cache server'
                                sim_status['connections_origin'][requests_ip[req]['origin']] -=1
                                sim_status['outbound_connections_cacheServer'] -=1
                                cacheServer_status[req_status[req]['cacheServer']]['active_outbound_connections'] -= 1
                                #add asset to cache
                                cacheServer_ip[req_status[req]['cacheServer']]['cached_assets_id'].append(requests_ip[req]['asset'])
                                req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                                req_status[req]['output_throughput_being_used']['origin'] = 0
                                
                                cacheServer_id = req_status[req]['cacheServer']
                                for key in throughput_status_time[cacheServer_id]:
                                    if key != 'old':
                                        throughput_status_time[cacheServer_id][key] -=1
                                req_asset_id = requests_ip[req]['asset']
                                asset_size = int(assets_ip[req_asset_id]['size'])
                                cache_throughput = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput'])
                                client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                                #check available throughput-- 
                                available_throughput = min(cache_throughput,client_throughput)
                                time_taken = utility.timeToTransfer(asset_size,available_throughput)
                                req_status[req]['adtc1'] = t + time_taken
                                req_status[req]['stage'] = 5      
                                req_status[req]['size_transferred_to_client'] = {}
                                req_status[req]['size_transferred_to_client'][t] = 0
                        #handle adtc
                    #Stage-5 - Transferring the asset to Client
                    if req_status[req]['stage'] ==  5:
                        if t < req_status[req]['adtc1']:
                            client_id = (clients_ip[requests_ip[req]['client']]['id'])
                            req_asset_id = requests_ip[req]['asset']
                            asset_size = int(assets_ip[req_asset_id]['size'])  - req_status[req]['size_transferred_to_client'].get(t,0)
                            cache_throughput = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput'])
                            client_throughput = int(clients_ip[requests_ip[req]['client']]['max_input_throughput'])
                                #check available throughput-- 
                            available_throughput = min(cache_throughput,client_throughput)
                            te = throughput_status_time[client_id]['old']
                            if t in throughput_status_time[client_id]:
                                n = throughput_status_time[client_id].get(t)
                                throughput_status_time[client_id]['old'] = t
                            else:
                                n = throughput_status_time[client_id][te]
                            throughput_to_use = available_throughput/n
                            req_status[req]['input_throughput_being_used']['client'] = throughput_to_use
                            req_status[req]['output_throughput_being_used']['cacheServer'] = throughput_to_use
                            cacheServer_status[req_status[req]['cacheServer']]['output_throughput_available'] = int(cacheServer_ip[req_status[req]['cacheServer']]['max_output_throughput']) - throughput_to_use
                            time_taken = utility.timeToTransfer(asset_size,throughput_to_use)
                            transfer_pertick = asset_size / time_taken
                            req_status[req]['size_transferred_to_client'][t+1] = req_status[req]['size_transferred_to_client'][t]  + transfer_pertick
                            req_status[req]['adtc1'] = t + time_taken 
                            req_status[req][t] = 'Transferring asset to client'
                            continue
                        elif t == req_status[req]['adtc1']:
                            req_status[req][t] = 'Asset transferred to client'
            
                            #release connection
                            sim_status['inbound_connections_cacheServer'] -=1
                            cacheServer_status[req_status[req]['cacheServer']]['active_inbound_connections'] -= 1
                            sim_status['connections_client'][requests_ip[req]['client']] -= 1
                            client_id = (clients_ip[requests_ip[req]['client']]['id'])  
                            for key in throughput_status_time[client_id]:
                                if key != 'old' and key != 'temp_adto' :
                                    if throughput_status_time[client_id][key] > 1:
                                        throughput_status_time[client_id][key] -=1
                                    else:
                                        throughput_status_time[client_id][key] = 0  
                            req_status[req]['completed'] = 1
                            req_status[req]['input_throughput_being_used']['client'] = 0
                            req_status[req]['input_throughput_being_used']['cacheServer'] = 0
                            req_status[req]['output_throughput_being_used']['origin'] = 0
                            req_status[req]['output_throughput_being_used']['cacheServer'] = 0
                            req_status[req]['completed_at']=t
        #updating the throughput status         
        total_cs_throughput_use= collections.defaultdict(int)
        for i in req_status.keys():
             
            total_cs_throughput_use[req_status[i].get('cacheServer', '0')] +=int(req_status[i]['input_throughput_being_used']['cacheServer'])
        for i in cacheServer_status.keys():
            cacheServer_status[i]['input_throughput_used'] = total_cs_throughput_use[i]
            cacheServer_status[i]['input_throughput_available']=int(cacheServer_ip[i]["max_input_throughput"])-total_cs_throughput_use[i]
        total_cs_throughput_use= collections.defaultdict(int)
        for i in req_status.keys():
            total_cs_throughput_use[req_status[i].get('cacheServer','0')] +=int(req_status[i]['output_throughput_being_used']['cacheServer'])
        for i in cacheServer_status.keys():
            cacheServer_status[i]['output_throughput_used'] = total_cs_throughput_use[i]
            cacheServer_status[i]['output_throughput_available']=int(cacheServer_ip[i]["max_output_throughput"])-total_cs_throughput_use[i]
 
#create lists for plotting       
active_inbound=collections.defaultdict(list)
active_outbound=collections.defaultdict(list)
cacheserver_inputthroughput_list=collections.defaultdict(list)
cacheserver_outputthroughput_list=collections.defaultdict(list)
cacheserver_inputthroughputavailable_list=collections.defaultdict(list)
tick_intervals=[]
cache_hit=collections.defaultdict(list)
cache_miss = collections.defaultdict(list)
cacheserver_outputthroughputavailable_list = collections.defaultdict(list)
request_list = []
workload_id={}


#Function to loop through time
def timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workloads):

    workload = utility.makedirectory(simulation_ip,cacheServer_ip)
    
     
    line1 = []
    line2 = []
    line3 = [] 
    line4 = []
    line5 = []
    line6 = [] 
    line7 = []
    line8 = []
    line9 = []
    
    inb_index = out_index= outo_index = outt_index = outa_index = outb_index = outc_index = outm_index = 0
    
    for t in range(simulation_ip['simulation1']['simulation_duration']+1): 
        simulation(t,requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip)
        if t%int(simulation_ip['simulation1']['tick_duration'])==0: 
            #Capture system state at tick duration
            sim_stat=utility.CaptureSystemState(t,simulation_ip,workload_ip,req_status,cacheServer_status,workloads)
            
            #storing system state 
            with open(os.path.join('output', workload, 'system_state', '%s.json' %t), 'w') as outfile:                          
                json.dump(sim_stat, outfile, indent = 4)
        plot_for = simulation_ip['simulation1']['plot_for_cacheServer']
        
        #Updating lists for each t
        for i in cacheServer_status.keys():
            v = cacheServer_status[i].get('active_inbound_connections',0)
            if i not in active_inbound:
                active_inbound[i] = [0]*inb_index
                active_inbound[i].append(v)
            else:
                active_inbound[i].append(v)
                inb_index = len(active_inbound[i]) - 1
            if i not in active_outbound:
                active_outbound[i] = [0]*out_index
                active_outbound[i].append(cacheServer_status[i]['active_outbound_connections'])
            else:
                active_outbound[i].append(cacheServer_status[i]['active_outbound_connections'])
                out_index = len(active_outbound[i]) - 1
            if i not in cacheserver_inputthroughput_list:
                cacheserver_inputthroughput_list[i] = [0]*outt_index
                cacheserver_inputthroughput_list[i].append(cacheServer_status[i]['input_throughput_used'])
            else:
                cacheserver_inputthroughput_list[i].append(cacheServer_status[i]['input_throughput_used'])
                outt_index = len(cacheserver_inputthroughput_list[i]) - 1
            if i not in cacheserver_outputthroughput_list:
                cacheserver_outputthroughput_list[i] = [0]*outo_index
                cacheserver_outputthroughput_list[i].append(cacheServer_status[i]['output_throughput_used'])
            else:
                cacheserver_outputthroughput_list[i].append(cacheServer_status[i]['output_throughput_used'])
                outo_index = len(cacheserver_outputthroughput_list[i]) - 1
            if i not in cacheserver_inputthroughputavailable_list:
                cacheserver_inputthroughputavailable_list[i] = [0]*outa_index
                cacheserver_inputthroughputavailable_list[i].append(cacheServer_status[i]['input_throughput_available'])
            else:
                cacheserver_inputthroughputavailable_list[i].append(cacheServer_status[i]['input_throughput_available'])
                outa_index = len(cacheserver_inputthroughputavailable_list[i]) - 1
            if i not in cacheserver_outputthroughputavailable_list:
                cacheserver_outputthroughputavailable_list[i] = [0]*outb_index
                cacheserver_outputthroughputavailable_list[i].append(cacheServer_status[i]['output_throughput_available'])
            else:
                cacheserver_outputthroughputavailable_list[i].append(cacheServer_status[i]['output_throughput_available'])
                outb_index = len(cacheserver_outputthroughputavailable_list[i]) - 1   
            if i not in cache_hit:
                cache_hit[i]= [0]*outc_index
                cache_hit[i].append(cacheServer_status[i]['cache_hit'])
            else:
                cache_hit[i].append(cacheServer_status[i]['cache_hit'])

                outc_index = len(cache_hit[i]) - 1
            if i not in cache_miss:
                cache_miss[i]= [0]*outm_index
                cache_miss[i].append(cacheServer_status[i]['cache_miss'])
            else:
                cache_miss[i].append(cacheServer_status[i]['cache_miss'])
                outm_index = len(cache_miss[i]) - 1
        tick_intervals.append(t)
        count = 0
        for req in req_status.keys():
            if(req_status[req]['completed'] != 1):
                count=count+1
        request_list.append(count)
        
        l = []
        for i in workload_ip:
            l.append(len(workload_ip[i]))
        x = max(l)
  
        y = int(x/5)
        if y ==0:
            y = x+1
        
        request_count=0
        for i in workload_ip:
            request_count +=len(workload_ip[i])

        #dynamic plots
        line1=live_plotter(tick_intervals,active_inbound[plot_for],line1,'Time t','Active_inbound_connections','Time t vs Inbound Connections of Cache Server', simulation_ip['simulation1']['simulation_duration'],cacheServer_ip[plot_for]['max_connections']+1 )
        line2=live_plotter(tick_intervals,active_outbound[plot_for], line2,'Time t','Active_outbound_connections','Time t vs Outbound Connections of Cache Server',simulation_ip['simulation1']['simulation_duration'],cacheServer_ip[plot_for]['max_connections']+1)
        line3=live_plotter(tick_intervals,cacheserver_inputthroughput_list[plot_for], line3, 'Time t','Input_Throughput_used','Time t vs Input_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[plot_for]['max_input_throughput'])+100)
        line4=live_plotter(tick_intervals,cacheserver_outputthroughput_list[plot_for], line4,'Time t','Output_Throughput_used','Time t vs Output_Throughput_used (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[plot_for]['max_output_throughput'])+100)
        line5=live_plotter(tick_intervals, cacheserver_inputthroughputavailable_list[plot_for], line5,'Time t','Output_Throughput_used','Time t vs Input_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[plot_for]['max_input_throughput'])+100)
        line6=live_plotter(tick_intervals, cacheserver_outputthroughputavailable_list[plot_for], line6,'Time t','Output_Throughput_used','Time t vs Output_Throughput_Available (Cache_Server)',simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[plot_for]['max_output_throughput'])+100)
        line7=live_plotter(tick_intervals, cache_hit[plot_for], line7, 'Time t','Cache hit','Time t vs Cache hit',simulation_ip['simulation1']['simulation_duration'], y)
        line8=live_plotter(tick_intervals, cache_miss[plot_for], line8, 'Time t','Cache miss','Time t vs Cache miss',simulation_ip['simulation1']['simulation_duration'], y)
        line9=live_plotter(tick_intervals,request_list, line9, 'Time t','Active_requests','Time t vs Active_Requests',simulation_ip['simulation1']['simulation_duration'], x*5)
        t +=1

    #static plots
    for i in active_inbound:         
        utility.visualize(tick_intervals,active_inbound[i], [], 'Time t','Active_inbound_connections','Time t vs Inbound Connections', i ,simulation_ip['simulation1']['simulation_duration'],cacheServer_ip[i]['max_connections']+1, workload)
        utility.visualize(tick_intervals,active_outbound[i], [],'Time t','Active_outbound_connections','Time t vs Outbound Connections', i,simulation_ip['simulation1']['simulation_duration'],cacheServer_ip[i]['max_connections']+1, workload)
        utility.visualize(tick_intervals,cacheserver_inputthroughput_list[i], [], 'Time t','Input_Throughput_used','Time t vs Input_Throughput_used',i,simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[i]['max_input_throughput'])+100, workload)
        utility.visualize(tick_intervals,cacheserver_outputthroughput_list[i], [],'Time t','Output_Throughput_used','Time t vs Output_Throughput_used',i,simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[i]['max_output_throughput'])+100, workload)
        utility.visualize(tick_intervals, cacheserver_inputthroughputavailable_list[i], [],'Time t','Input_Throughput_Available','Time t vs Input_Throughput_Available',i,simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[i]['max_input_throughput'])+100, workload)
        utility.visualize(tick_intervals, cacheserver_outputthroughputavailable_list[i], [],'Time t','Output_Throughput_Available','Time t vs Output_Throughput_Available',i,simulation_ip['simulation1']['simulation_duration'],int(cacheServer_ip[i]['max_input_throughput'])+100, workload)
        utility.visualize(tick_intervals,cache_miss[i], cache_hit[i], 'Time t','Cache hit/miss','Time t vs Cache hit & miss',i,simulation_ip['simulation1']['simulation_duration'], y, workload, 'cache_miss','cache_hit')
    utility.visualize(tick_intervals,request_list, [], 'Time t','Active_requests','Time t vs Active_Requests','simulation',simulation_ip['simulation1']['simulation_duration'], x*5, workload)

def initializeSimStatus(requests_ip):
    global sim_status
    sim_status['inbound_connections_cacheServer'] = 0
    sim_status['outbound_connections_cacheServer'] = 0  
    sim_status['connections_client']={}
    sim_status['connections_origin']={}
    for req in requests_ip.keys():
        if req!="_id":
            client=requests_ip[req]['client']
            sim_status['connections_client'][client] = 0
            origin=requests_ip[req]['origin']
            sim_status['connections_origin'][origin] = 0

def main():
    f = open('input/'+sys.argv[1])
    contents = f.read()
    lines = contents.splitlines()
    #read data from json files
    simulation_ip = utility.read_json('input/'+lines[0])
    requests_ip = utility.read_json('input/'+lines[1])
    cacheServer_ip = utility.read_json('input/'+lines[2])
    assets_ip = utility.read_json('input/'+lines[3])
    clients_ip = utility.read_json('input/'+lines[4])
    origin_ip = utility.read_json('input/'+lines[5])
    workloads = utility.read_json('input/'+lines[6])
    workload_ip=utility.input_workload('input/'+lines[6])[simulation_ip["simulation1"]["workload"]]
    initializeSimStatus(requests_ip)
    timer(requests_ip,simulation_ip, workload_ip,cacheServer_ip,assets_ip,clients_ip,origin_ip,workloads)
   
    #pprint(req_status)
    
if __name__ == '__main__':
    main()
    



    
