#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 19:59:26 2020

@author: srikanth

This tool creates random inputs for simulation
"""


import json
import random
import sys
import os


input_file_path='input/'+sys.argv[1]

#Store input file into a variable
with open(input_file_path) as json_file:
    data = json.load(json_file)

order=["assets","origin","cacheservers","clients","requests","workloads","simulation"]    

for k in order:
    
    #Build asset objects
    if k=="assets":
        asset_count=data["asset"]["number_of_objects"]
        master_obj=[]
        for i in range(1,asset_count+1):
            asset_obj={}
            asset_obj["id"]="asset"+str(i)
            asset_obj["size"]=random.randint(int(data["asset"]["size"][0]/data["asset"]["size"][2]+1),int(data["asset"]["size"][1]/data["asset"]["size"][2]))*data["asset"]["size"][2]
            master_obj.append(asset_obj)
        with open(os.path.join('input', 'assets.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
    
    #Build origin objects
    if k=="origin":
        origin_count=data["origin"]["number_of_objects"]
        master_obj=[]
        for i in range(1,origin_count+1):
            origin_obj={}
            origin_obj["id"]="origin"+str(i)
            origin_obj["max_connections"]=random.randint(int(data["origin"]["max_connections"][0]/data["origin"]["max_connections"][2]+1),int(data["origin"]["max_connections"][1]/data["origin"]["max_connections"][2]))*data["origin"]["max_connections"][2]
            origin_obj["max_output_throughput"]=random.randint(int(data["origin"]["max_output_throughput"][0]/data["origin"]["max_output_throughput"][2]+1),int(data["origin"]["max_output_throughput"][1]/data["origin"]["max_output_throughput"][2]))*data["origin"]["max_output_throughput"][2]
            origin_obj["asset_check_time"]=random.randint(int(data["origin"]["asset_check_time"][0]/data["origin"]["asset_check_time"][2]+1),int(data["origin"]["asset_check_time"][1]/data["origin"]["asset_check_time"][2]))*data["origin"]["asset_check_time"][2]
            origin_obj["assets"]=[]
            rand_int=random.randint(1,10)
            for j in range(rand_int):
                origin_obj["assets"].append("asset"+str(random.randint(0,data["asset"]["number_of_objects"])))
            master_obj.append(origin_obj)
        with open(os.path.join('input', 'origins.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
    
    #Build Cacheserver objects
    if k=="cacheservers":
        cs_count=data["cacheserver"]["number_of_objects"]
        master_obj=[]
        for i in range(1,cs_count+1):
            cs_obj={}
            cs_obj["id"]="cacheserver"+str(i)
            cs_obj["max_connections"]=random.randint(int(data["cacheserver"]["max_connections"][0]/data["cacheserver"]["max_connections"][2]+1),int(data["cacheserver"]["max_connections"][1]/data["cacheserver"]["max_connections"][2]))*data["cacheserver"]["max_connections"][2]
            cs_obj["max_output_throughput"]=random.randint(int(data["cacheserver"]["max_output_throughput"][0]/data["cacheserver"]["max_output_throughput"][2]+1),int(data["cacheserver"]["max_output_throughput"][1]/data["cacheserver"]["max_output_throughput"][2]))*data["cacheserver"]["max_output_throughput"][2]
            cs_obj["max_input_throughput"]=random.randint(int(data["cacheserver"]["max_input_throughput"][0]/data["cacheserver"]["max_input_throughput"][2]+1),int(data["cacheserver"]["max_input_throughput"][1]/data["cacheserver"]["max_input_throughput"][2]))*data["cacheserver"]["max_input_throughput"][2]
            cs_obj["time_to_check_cache"]=random.randint(int(data["cacheserver"]["time_to_check_cache"][0]/data["cacheserver"]["time_to_check_cache"][2]+1),int(data["cacheserver"]["time_to_check_cache"][1]/data["cacheserver"]["time_to_check_cache"][2]))*data["cacheserver"]["time_to_check_cache"][2]
            cs_obj["throughput_limit"]=random.randint(int(data["cacheserver"]["throughput_limit"][0]/data["cacheserver"]["throughput_limit"][2]+1),int(data["cacheserver"]["throughput_limit"][1]/data["cacheserver"]["throughput_limit"][2]))*data["cacheserver"]["throughput_limit"][2]
            cs_obj["cached_assets_id"]=[]
            rand_int=random.randint(1,data["asset"]["number_of_objects"])
            for j in range(rand_int):
                cs_obj["cached_assets_id"].append("asset"+str(random.randint(1,data["asset"]["number_of_objects"])))
            master_obj.append(cs_obj)
        with open(os.path.join('input', 'cacheservers.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
    
    #Build client objects
    if k=="clients":
        client_count=data["client"]["number_of_objects"]
        master_obj=[]
        for i in range(1,client_count+1):
            client_obj={}
            client_obj["id"]="client"+str(i)
            #client_obj["max_connections"]=random.randint(int(data["client"]["max_connections"][0]/100+1),int(data["client"]["max_connections"][1]/100))*100
            client_obj["max_input_throughput"]=random.randint(int(data["client"]["max_input_throughput"][0]/data["client"]["max_input_throughput"][2]+1),int(data["client"]["max_input_throughput"][1]/data["client"]["max_input_throughput"][2]))*data["client"]["max_input_throughput"][2]
            client_obj["max_connections"]=random.randint(int(data["client"]["max_connections"][0]/data["client"]["max_connections"][2]+1),int(data["client"]["max_connections"][1]/data["client"]["max_connections"][2]))*data["client"]["max_connections"][2]
            temp={}
            for j in range(1,data["cacheserver"]["number_of_objects"]+1):
                temp["cacheserver"+str(j)]=random.randint(int(data["client"]["distance_from_cacheservers"][0]/data["client"]["distance_from_cacheservers"][2]+1),int(data["client"]["distance_from_cacheservers"][1]/data["client"]["distance_from_cacheservers"][2]))*data["client"]["distance_from_cacheservers"][2]
            client_obj["distance"]=temp
            master_obj.append(client_obj)
        with open(os.path.join('input', 'clients.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
            
    #Build request objects
    if k=="requests":
        req_count=data["request"]["number_of_objects"]
        master_obj=[]
        for i in range(1,req_count+1):
            req_obj={}
            req_obj["id"]="request"+str(i)
            req_obj["client"]="client"+str(random.randint(1,data["client"]["number_of_objects"]))
            req_obj["asset"]="asset"+str(random.randint(1,data["asset"]["number_of_objects"]))
            req_obj["origin"]="origin"+str(random.randint(1,data["origin"]["number_of_objects"]))
            req_obj["server"]="cacheserver"+str(random.randint(1,data["cacheserver"]["number_of_objects"]))
            master_obj.append(req_obj)
        with open(os.path.join('input', 'requests.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
            
    #Build workload objects
    if k=="workloads":
        wl_count=data["workload"]["number_of_objects"]
        master_obj=[]
        for i in range(1,wl_count+1):
            wl_obj={}
            wl_obj["id"]="workload"+str(i)
            wl_obj["requests"]=[]
            req_times=random.randint(1,data["simulation"]["simulation_duration"])
            incr=random.randint(1,10)
            for i in range(0,req_times,incr):
                temp_obj={}
                temp_obj["time"]=i
                temp_obj["request_id"]=[]
                nreqs=random.randint(10,100)
                for j in range(1,nreqs+1):
                    temp_obj["request_id"].append("request"+str(random.randint(1,data["request"]["number_of_objects"])))
                wl_obj["requests"].append(temp_obj)
            master_obj.append(wl_obj)
        with open(os.path.join('input', 'workloads.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)
    
    #Build simulation object
    if k=="simulation":
        master_obj=[]
        sim_obj={}
        sim_obj["id"]="simulation1"
        sim_obj["tick_duration"]=data["simulation"]["tick_duration"]
        sim_obj["simulation_duration"]=data["simulation"]["simulation_duration"]
        sim_obj["tcp_connection_time"]=data["simulation"]["tcp_connection_time"]
        sim_obj["workload"]="workload"+str(random.randint(1,data["workload"]["number_of_objects"]))
        sim_obj["plot_for_cacheServer"]=data["simulation"]["plot_for_cacheServer"]
        sim_obj["timeout"]=data["simulation"]["timeout"]
        master_obj.append(sim_obj)
        with open(os.path.join('input', 'simulation.json'), 'w') as outfile:
            json.dump(master_obj, outfile,indent=4)



