# -*- coding: utf-8 -*-
"""
Created on Sat Jun  3 08:27:01 2023

@author: alma_
"""
import os
import sys
from lxml import etree
import pyodbc 


import paramiko
import pysftp

import shutil

'''
Servidor	IP	Nombre
SRI201243	192.168.253.113	BC Gateway Server BC, Administrator & BusinessWorks Server
SRI201244	192.168.253.114	BC Gateway Server BC & BusinessWorks Server
SRI201262	192.168.84.162	BC Interior Server & BusinessWorks Server
SRI201263	192.168.84.163	BC Interior Server & BusinessWorks Server
SRI201265	192.168.84.165	BusinessWorks Server
SRI201267	192.168.84.167	BusinessWorks Server
SRI201268	192.168.84.168	BusinessWorks Server
SRI201272	192.168.84.172	BusinessWorks Server
SRI201273	192.168.84.173	BusinessWorks Server
SRI201274	192.168.84.174	BusinessWorks Server
'''

Ftp_Server_host = 'SRI201265'
Ftp_username ='tibco'
Ftp_password = 'Int3gr@t10n5'
Ftp_source_files_path = '/opt/tibco/tra/domain/PEAIMEX03/datafiles/'
Ftp_local_path="C:\\alma\\HEB\\Metadata Process\\AllDataFiles\\"

server_list = ['SRI201262', 'SRI201263',\
               'SRI201265', 'SRI201267',\
               'SRI201268', 'SRI201272',\
               'SRI201273', 'SRI201274',\
               'SRI201243', 'SRI201244']

def grab_dir_r(sftp, dirR, dirL):
       
        if not sftp.isdir(dirR):
            #is a file and is a ProcessDefinition File
            if ".process" in dirR or ".substvar":
                #print('---',dirR)
                sftp.get(dirR, dirL)
        if sftp.isdir(dirR):
            mydirList = sftp.listdir(dirR)            
            for i in mydirList:
                if not os.path.exists(dirL):
                    os.makedirs(dirL)                
                grab_dir_r(sftp, dirR+'/' + i, dirL+'\\'+i) 
      
        
def read_server(server):
    try:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(Ftp_Server_host, username=Ftp_username, password=Ftp_password,cnopts=cnopts) as sftp:
            print ('---------------------------')
            print ('Inicializa ', Ftp_Server_host)
            
            
            # Obtain structure of the remote directory 
            mydirList = sftp.listdir(Ftp_source_files_path)
            sftp.listdir()
            
            for i in mydirList:
                dirLocalName = Ftp_local_path+server 
                if not os.path.exists(dirLocalName+"\\"+i):
                    print (i)
                    grab_dir_r(sftp, Ftp_source_files_path +  i, dirLocalName+"\\"+i)
        
        
        print ('Finalizo', Ftp_Server_host)
        print ('---------------------------')
    except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise
        
    
#read data file from  
read_server(Ftp_Server_host)



conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=LAPTOP-AJGCL8EE;'
                      'Database=DBTIB;'
                      'Trusted_Connection=yes;')

  
def saveMetadataProcess(TIBCO_ENGINE, PROJECT_NAME, PROCESS_NAME, ACTIVITY_NAME, ACTIVITY_TYPE, ACT_JDCSHARED, ACT_STATEMENT):
    cursor = conn.cursor()
    sql = "INSERT INTO process_metadata (TIBCO_ENGINE, PROJECT_NAME, PROCESS_NAME, ACTIVITY_NAME, ACTIVITY_TYPE, act_sharedRESOURCE, ACT_STATEMENT) VALUES (?,?,?,?,?,?,?)"
    
    cursor.execute(sql, (TIBCO_ENGINE, PROJECT_NAME, PROCESS_NAME, ACTIVITY_NAME, ACTIVITY_TYPE, ACT_JDCSHARED, ACT_STATEMENT) )
    conn.commit()


#Reading ProcessDefinition File
def readProcessFile(server_name, project_name, process_name, file_Path):    
    parser1 = etree.XMLParser(recover=True)
    tree = etree.parse(file_Path, parser1)
    
    root = tree.getroot()
    statement =''
    jdbcshared =''
    
    for child in root: 
        #print(child.tag, child.getchildren()[0])
        # Identify an JDBC Activity
        if  ("activity" in child.tag) and ("jdbc" in child.getchildren()[0].text):
            # print("found-->")
            # print("type: ", child.getchildren()[0].text)
            # print("activity: ", child.attrib['name']) 
            activity_name = child.attrib['name']
            activity_type = child.getchildren()[0].text
            for sChild in child.getchildren(): 
                if "config" in sChild.tag:
                    for tChild in sChild.getchildren():
                        if "statement" in tChild.tag or "ProcedureName" in tChild.tag:
                            # print("statement: ", tChild.text)
                            statement = tChild.text
                        if "jdbcSharedConfig" in tChild.tag:
                            jdbcshared= tChild.text
                            # print("jdbcSharedConfig: ", tChild.text)
                if ("JDBCGeneralActivity" in activity_type) and ("inputBindings" in sChild.tag):                    
                    statement = sChild.getchildren()[0].getchildren()[0].getchildren()[0].attrib['select']
                    print("-------------------->",statement)
                        
            #call function to insert data in DB
            saveMetadataProcess(server_name, project_name, process_name, activity_name, activity_type, jdbcshared, statement)
    
#function to get all process definition files
def getAllProcessFiles(walk_dir):      
    """
    

    Parameters
    ----------
    walk_dir : STRING, IS THE ABSOLUTE PATH OF DATA FILE REPOSITORIES
         

    Returns
    -------
    None.

    """
    
    print('walk_dir = ' + walk_dir)
    
    # If your current working directory may change during script execution, it's recommended to
    # immediately convert program arguments to an absolute path. Then the variable root below will
    # be an absolute path as well. Example:
    # walk_dir = os.path.abspath(walk_dir)
    print('walk_dir (absolute) = ' + os.path.abspath(walk_dir))
    
    server_name =''
    project_name=''
    wd_len = len(walk_dir)
    
    for root, subdirs, files in os.walk(walk_dir):
        root_len = len(root) 
        carpetas = root[wd_len+1:root_len].split("\\") 
        
        if len(carpetas[0]) >1 and len(carpetas)==1:
            #change of server
            server_name = carpetas[0]
            print('--\nserver = ' , server_name)
        if (len(carpetas)==2):
            #change of project
            project_name = carpetas[1]
            print('\nproject = ' , project_name)       
        
       
        # list_file_path = os.path.join(root, 'my-directory-list.txt')     
        # with open(list_file_path, 'wb') as list_file: 
            
        for filename in files: 
           
            file_path = os.path.join(root, filename)
             
            if(".process" in file_path):
                #call function readProcessFile
                process_name = os.path.basename(file_path)
                #print("file = ", file_path, " process_name: ", process_name)
                readProcessFile(server_name, project_name, process_name, file_path) 
            
#call getAllProcessFiles
#getAllProcessFiles("C:\\alma\\HEB\\Metadata Process\\AllDataFiles")
#getAllProcessFiles("C:\\alma\\HEB\\Repos2\\Repos4\\Prueba")
#getAllProcessFiles("C:\\alma\\HEB\\Repos2\\Repos4\\PROD\\OMSToPOSService_root")
